from __future__ import annotations

from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..astro import AstroField

router = APIRouter()
field = AstroField()
clients: Set[WebSocket] = set()


@router.websocket("/ws/astro")
async def ws_astro(ws: WebSocket) -> None:
    await ws.accept()
    clients.add(ws)
    await ws.send_json({"event": "astro_field", "data": field.snapshot()})
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.discard(ws)


async def push_field(state: Dict[str, Any]) -> None:
    stale: Set[WebSocket] = set()
    for client in clients:
        try:
            await client.send_json({"event": "astro_field", "data": state})
        except Exception:  # pragma: no cover - network failure cleanup
            stale.add(client)
    for client in stale:
        clients.discard(client)
