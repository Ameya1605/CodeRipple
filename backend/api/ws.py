from fastapi import APIRouter, WebSocket
from backend.websocket import stream_analysis_progress
from backend.auth.dependencies import get_ws_user

router = APIRouter()

@router.websocket("/ws/analyze/{task_id}")
async def analysis_progress_ws(websocket: WebSocket, task_id: str):
    user = await get_ws_user(websocket)
    if user is None:
        return
    await stream_analysis_progress(websocket, task_id)
