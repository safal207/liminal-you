from __future__ import annotations

from contextlib import suppress

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from ..feedback import feedback_hub

router = APIRouter()


@router.websocket("/ws/feedback")
async def feedback_socket(websocket: WebSocket) -> None:
    profile_id = websocket.query_params.get("profile_id")
    await feedback_hub.connect(websocket, profile_id=profile_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        with suppress(Exception):
            await feedback_hub.disconnect(websocket)
