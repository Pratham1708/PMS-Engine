"""
pipeline_ws.py — WebSocket Router & Replay Events API for Quantitative Research Laboratory.
"""

import asyncio
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.services.pipeline_event_bus import get_event_bus
from app.services.pipeline_monitor import get_monitor
from app.services import db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["pipeline_ws"])


@router.websocket("/api/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    """
    WebSocket endpoint streaming live quantitative research pipeline events.
    """
    await websocket.accept()
    bus = get_event_bus()

    # Capture event loop for thread-safe broadcast dispatch
    try:
        loop = asyncio.get_running_loop()
        bus.register_loop(loop)
    except Exception:
        pass

    bus.add_subscriber(websocket)

    # Immediately transmit current monitor state on connection
    monitor = get_monitor()
    initial_state = {
        "event_type": "initial_state",
        "monitor": monitor.to_dict(),
    }
    try:
        await websocket.send_json(initial_state)
    except Exception as e:
        logger.error(f"[WebSocket] Failed sending initial state: {e}")

    try:
        while True:
            # Keep connection open & handle incoming client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info("[WebSocket] Client disconnected cleanly.")
    except Exception as e:
        logger.warning(f"[WebSocket] Disconnected with error: {e}")
    finally:
        bus.remove_subscriber(websocket)


@router.get("/api/snapshot/pipeline/{snapshot_id}/events")
async def get_pipeline_replay_events(snapshot_id: str):
    """
    Fetch all versioned execution events for a past snapshot run to power Replay Mode.
    """
    events = db.get_pipeline_events(snapshot_id)
    if not events:
        # Check if snapshot metadata exists
        snap = db.get_snapshot_by_id(snapshot_id) if hasattr(db, "get_snapshot_by_id") else None
        return {
            "snapshot_id": snapshot_id,
            "total_events": 0,
            "events": [],
            "message": f"No replay events logged for snapshot '{snapshot_id}'.",
        }

    return {
        "snapshot_id": snapshot_id,
        "total_events": len(events),
        "events": events,
    }
