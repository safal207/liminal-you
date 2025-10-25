"""LiminalDB Python client using WebSocket and CBOR protocol."""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import cbor2
import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


@dataclass
class Impulse:
    """Impulse structure for LiminalDB."""

    kind: str  # "Query" | "Write" | "Affect"
    pattern: str
    strength: float  # 0.0..1.0
    ttl_ms: int = 5000
    tags: List[str] | None = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "kind": self.kind,
            "pattern": self.pattern,
            "strength": self.strength,
            "ttl_ms": self.ttl_ms,
        }
        if self.tags:
            data["tags"] = self.tags
        return data


@dataclass
class ResonantModel:
    """ResonantModel structure for LiminalDB."""

    id: str
    edges: List[Dict[str, Any]] | None = None
    persistence: str = "memory"  # "memory" | "snapshot" | "archive"
    latent_traits: Dict[str, float] | None = None
    tags: List[str] | None = None

    def to_dict(self) -> Dict[str, Any]:
        data = {"id": self.id, "persistence": self.persistence}
        if self.edges:
            data["edges"] = self.edges
        if self.latent_traits:
            data["traits"] = self.latent_traits
        if self.tags:
            data["tags"] = self.tags
        return data


class LiminalDBClient:
    """Async WebSocket client for LiminalDB."""

    def __init__(self, url: str = "ws://localhost:8001"):
        self.url = url
        self._ws: WebSocketClientProtocol | None = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._event_handlers: Dict[str, List[callable]] = {}

    async def connect(self) -> None:
        """Connect to LiminalDB WebSocket server."""
        if self._connected:
            return

        try:
            self._ws = await websockets.connect(self.url)
            self._connected = True
            logger.info("Connected to LiminalDB at %s", self.url)

            # Start event listener
            asyncio.create_task(self._listen_events())
        except Exception as e:
            logger.error("Failed to connect to LiminalDB: %s", e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from LiminalDB."""
        if self._ws:
            await self._ws.close()
            self._connected = False
            logger.info("Disconnected from LiminalDB")

    async def _listen_events(self) -> None:
        """Listen for events from LiminalDB."""
        if not self._ws:
            return

        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    # CBOR format
                    event = cbor2.loads(message)
                else:
                    # JSON format
                    event = json.loads(message)

                await self._handle_event(event)
        except websockets.exceptions.ConnectionClosed:
            logger.info("LiminalDB connection closed")
            self._connected = False
        except Exception as e:
            logger.error("Error in event listener: %s", e)

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle incoming event from LiminalDB."""
        event_type = event.get("ev")
        if not event_type:
            return

        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error("Error in event handler for %s: %s", event_type, e)

    def on_event(self, event_type: str, handler: callable) -> None:
        """Register event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def send_impulse(self, impulse: Impulse) -> Dict[str, Any]:
        """Send impulse to LiminalDB."""
        if not self._connected or not self._ws:
            raise RuntimeError("Not connected to LiminalDB")

        async with self._lock:
            # Send as CBOR
            message = cbor2.dumps(impulse.to_dict())
            await self._ws.send(message)

            # Wait for response (for now, we'll just return success)
            # In production, implement proper request/response correlation
            return {"status": "ok"}

    async def query(self, pattern: str, strength: float = 0.7, tags: List[str] | None = None) -> Dict[str, Any]:
        """Send Query impulse."""
        impulse = Impulse(
            kind="Query",
            pattern=pattern,
            strength=strength,
            tags=tags,
        )
        return await self.send_impulse(impulse)

    async def write(self, pattern: str, strength: float = 0.8, tags: List[str] | None = None) -> Dict[str, Any]:
        """Send Write impulse."""
        impulse = Impulse(
            kind="Write",
            pattern=pattern,
            strength=strength,
            tags=tags,
        )
        return await self.send_impulse(impulse)

    async def affect(self, pattern: str, strength: float = 0.6, tags: List[str] | None = None) -> Dict[str, Any]:
        """Send Affect impulse."""
        impulse = Impulse(
            kind="Affect",
            pattern=pattern,
            strength=strength,
            tags=tags,
        )
        return await self.send_impulse(impulse)

    async def awaken_get(self, model_id: str) -> Dict[str, Any]:
        """Get ResonantModel state."""
        if not self._connected or not self._ws:
            raise RuntimeError("Not connected to LiminalDB")

        async with self._lock:
            command = {"cmd": "awaken.get", "args": {"id": model_id}}
            message = cbor2.dumps(command)
            await self._ws.send(message)

            # Wait for response
            response = await self._ws.recv()
            if isinstance(response, bytes):
                return cbor2.loads(response)
            return json.loads(response)

    async def awaken_set(self, model: ResonantModel) -> Dict[str, Any]:
        """Set ResonantModel configuration."""
        if not self._connected or not self._ws:
            raise RuntimeError("Not connected to LiminalDB")

        async with self._lock:
            command = {"cmd": "awaken.set", "args": model.to_dict()}
            message = cbor2.dumps(command)
            await self._ws.send(message)

            # Wait for response
            response = await self._ws.recv()
            if isinstance(response, bytes):
                return cbor2.loads(response)
            return json.loads(response)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current cluster metrics."""
        if not self._connected or not self._ws:
            raise RuntimeError("Not connected to LiminalDB")

        async with self._lock:
            command = {"cmd": "metrics"}
            message = cbor2.dumps(command)
            await self._ws.send(message)

            # Wait for response
            response = await self._ws.recv()
            if isinstance(response, bytes):
                return cbor2.loads(response)
            return json.loads(response)


# Global client instance
_client: LiminalDBClient | None = None


def get_liminaldb_client() -> LiminalDBClient:
    """Get global LiminalDB client instance."""
    global _client
    if _client is None:
        _client = LiminalDBClient()
    return _client
