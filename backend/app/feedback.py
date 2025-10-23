from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from .astro import AstroField
from .services.preferences import get_feedback_enabled

logger = logging.getLogger(__name__)

_FEEDBACK_MESSAGES = {
    "warm": "Поле дрожит — пригласи дыхание.",
    "cool": "Поле гармонично, можно делиться.",
    "neutral": "Слушаем поле.",
}


def _is_feature_globally_enabled() -> bool:
    raw = os.getenv("FEEDBACK_ENABLED", "true").lower()
    return raw not in {"0", "false", "off"}


@dataclass
class _ConnectionInfo:
    profile_id: Optional[str]


class NeuroFeedbackHub:
    """Coordinates the unified neuro-feedback broadcast loop."""

    def __init__(self, *, interval: float = 3.0, change_threshold: float = 0.1) -> None:
        self._connections: Dict[WebSocket, _ConnectionInfo] = {}
        self._astro_field = AstroField()
        self._lock = asyncio.Lock()
        self._last_payload: Dict[str, Any] | None = None
        self._last_sent_ts = 0.0
        self._interval = interval
        self._change_threshold = change_threshold
        self._broadcast_task: asyncio.Task[None] | None = None
        self._queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()

    async def connect(self, websocket: WebSocket, profile_id: str | None = None) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[websocket] = _ConnectionInfo(profile_id=profile_id)
            self._ensure_broadcast_loop()
        if self._last_payload and self._should_send_feedback(websocket):
            try:
                await websocket.send_json(self._last_payload)
            except WebSocketDisconnect:
                await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.pop(websocket, None)

    async def publish(self, message: Dict[str, Any]) -> None:
        """Send a raw message to all connected clients."""
        self._ensure_broadcast_loop()
        await self._queue.put({"payload": message, "feedback_only": False})

    async def integrate_field(self, pad_vec: Any) -> Dict[str, Any]:
        """Integrate a PAD vector into the astro field and broadcast feedback."""
        state = self._astro_field.integrate(pad_vec)
        self._ensure_broadcast_loop()
        await self._queue.put({"state": state})
        return state

    async def snapshot(self) -> Dict[str, Any]:
        return self._astro_field.snapshot()

    def analyze_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        entropy = float(state.get("entropy", 0.0))
        coherence = float(state.get("coherence", 0.0))
        pad = state.get("pad_avg", [0.0, 0.0, 0.0])

        if entropy > 0.7:
            tone = "warm"
        elif coherence > 0.8:
            tone = "cool"
        else:
            tone = "neutral"

        message = _FEEDBACK_MESSAGES[tone]
        intensity = max(0.0, min(1.0, (coherence + (1.0 - entropy)) / 2))

        return {
            "tone": tone,
            "message": message,
            "intensity": round(intensity, 3),
            "pad": [float(value) for value in pad[:3]],
            "entropy": round(entropy, 3),
            "coherence": round(coherence, 3),
            "ts": int(state.get("ts", time.time())),
            "samples": int(state.get("samples", 0)),
        }

    def _ensure_broadcast_loop(self) -> None:
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())

    async def _broadcast_loop(self) -> None:
        while True:
            item = await self._queue.get()
            if "state" in item:
                state = item["state"]
                await self._handle_state(state)
            else:
                payload = item["payload"]
                await self._broadcast(payload, feedback_only=item.get("feedback_only", False))

    async def _handle_state(self, state: Dict[str, Any]) -> None:
        analysis = self.analyze_state(state)
        payload = {"event": "neuro_feedback", "data": analysis}

        now = time.monotonic()
        should_send = False

        if not self._last_payload:
            should_send = True
        else:
            last_data = self._last_payload.get("data", {})
            tone_changed = analysis.get("tone") != last_data.get("tone")
            intensity_changed = abs(analysis.get("intensity", 0.0) - last_data.get("intensity", 0.0))
            should_send = tone_changed or intensity_changed > self._change_threshold
            if not should_send and now - self._last_sent_ts >= self._interval:
                should_send = True

        if not should_send:
            return

        await self._broadcast(payload, feedback_only=True)
        self._last_payload = payload
        self._last_sent_ts = now

    async def _broadcast(self, payload: Dict[str, Any], *, feedback_only: bool) -> None:
        if feedback_only and not _is_feature_globally_enabled():
            logger.debug("feedback loop disabled globally; skipping broadcast")
            return

        stale: list[WebSocket] = []
        async with self._lock:
            items = list(self._connections.items())
        for websocket, info in items:
            if feedback_only and not self._should_send_feedback(websocket):
                profile_id = info.profile_id or "anonymous"
                logger.debug("Skipping feedback broadcast for profile %s (opted out)", profile_id)
                continue
            try:
                await websocket.send_json(payload)
            except (WebSocketDisconnect, RuntimeError):
                stale.append(websocket)
        if stale:
            async with self._lock:
                for websocket in stale:
                    self._connections.pop(websocket, None)

        if feedback_only:
            tone = payload.get("data", {}).get("tone")
            logger.info("Feedback tone shifted to %s", tone)

    def _should_send_feedback(self, websocket: WebSocket) -> bool:
        info = self._connections.get(websocket)
        if not info:
            return False
        if info.profile_id:
            return get_feedback_enabled(info.profile_id)
        return True


feedback_hub = NeuroFeedbackHub()
