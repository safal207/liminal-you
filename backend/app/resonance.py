from __future__ import annotations

import asyncio
from typing import Any, Dict, Set

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState


class ResonanceHub:
    """Central hub orchestrating resonance WebSocket sessions."""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self._broadcast_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new websocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
            self._ensure_broadcast_loop()

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a websocket connection from the hub."""
        async with self._lock:
            self._connections.discard(websocket)

    async def publish(self, message: Dict[str, Any]) -> None:
        """Schedule a message to broadcast to all active connections."""
        await self._queue.put(message)

    async def heartbeat(self, websocket: WebSocket, interval: float = 20.0) -> None:
        """Continuously send heartbeat messages to keep the channel alive."""
        try:
            while True:
                await asyncio.sleep(interval)
                if websocket.client_state != WebSocketState.CONNECTED:
                    break
                try:
                    await websocket.send_json({"event": "heartbeat"})
                except WebSocketDisconnect:
                    break
                except RuntimeError:
                    # Starlette raises RuntimeError when trying to send on a closed socket.
                    break
        except asyncio.CancelledError:
            pass

    def _ensure_broadcast_loop(self) -> None:
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())

    async def _broadcast_loop(self) -> None:
        while True:
            message = await self._queue.get()
            stale: Set[WebSocket] = set()
            for connection in list(self._connections):
                try:
                    await connection.send_json(message)
                except (WebSocketDisconnect, RuntimeError):
                    stale.add(connection)
            if stale:
                async with self._lock:
                    for conn in stale:
                        self._connections.discard(conn)


resonance_hub = ResonanceHub()
