"""
WebSocket module — Fix #9: Terminal events check using WSEventType.
"""
import asyncio
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
import backend.config as config
from backend.core.events import TERMINAL_EVENTS, WSEventType

logger = logging.getLogger(__name__)

def get_channel_key(task_id: str) -> str:
    return f"dia:analysis:progress:{task_id}"

async def publish_progress(task_id: str, event: dict):
    r = aioredis.from_url(config.REDIS_URL, decode_responses=True)
    try:
        await r.publish(get_channel_key(task_id), json.dumps(event))
    finally:
        await r.aclose()

async def stream_analysis_progress(websocket: WebSocket, task_id: str):
    await websocket.accept()
    r = aioredis.from_url(config.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    channel = get_channel_key(task_id)

    try:
        await pubsub.subscribe(channel)
        logger.info(f"WebSocket subscribed to channel: {channel}")

        async for raw_message in pubsub.listen():
            if raw_message["type"] != "message":
                continue

            try:
                event = json.loads(raw_message["data"])
            except json.JSONDecodeError:
                continue

            try:
                # F-6: Heartbeat handling (don't forward to frontend but keep connection alive)
                if event.get("type") == WSEventType.HEARTBEAT:
                    continue
                await websocket.send_json(event)
            except WebSocketDisconnect:
                logger.info(f"Client disconnected from {channel}")
                break

            # Fix #9: Use central TERMINAL_EVENTS set
            if event.get("type") in TERMINAL_EVENTS:
                logger.info(f"Received terminal event on {channel}, closing WebSocket")
                await websocket.close(code=1000)
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnect caught for {channel}")
    except Exception as e:
        logger.error(f"WebSocket error on {channel}: {e}")
        try:
            await websocket.send_json({"type": WSEventType.ERROR, "message": str(e)})
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await r.aclose()
        logger.info(f"WebSocket cleanup complete for {channel}")
