from __future__ import annotations

import asyncio
from contextlib import suppress

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from ..resonance import resonance_hub

router = APIRouter()


@router.websocket("/ws/resonance")
async def resonance_socket(websocket: WebSocket) -> None:
    await resonance_hub.connect(websocket)
    heartbeat_task = asyncio.create_task(resonance_hub.heartbeat(websocket))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        with suppress(asyncio.CancelledError):
            await heartbeat_task
        await resonance_hub.disconnect(websocket)
