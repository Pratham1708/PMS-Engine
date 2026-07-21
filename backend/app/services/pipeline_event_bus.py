"""
pipeline_event_bus.py — Real-time event broker for PMS Engine Quantitative Research Laboratory.

Features:
- Thread-safe singleton for emitting sequence-numbered pipeline events.
- Persists all events to DB via db.save_pipeline_event for historical Replay Mode.
- Broadcasts versioned JSON events to connected WebSockets.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Any, Dict, Optional, Set
from fastapi import WebSocket

from app.services import db

logger = logging.getLogger(__name__)


class PipelineEventBus:
    """Thread-safe event bus for real-time WebSocket streaming & Replay persistence."""

    _instance: Optional["PipelineEventBus"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._state_lock = threading.Lock()
        self._subscribers: Set[WebSocket] = set()
        self._active_snapshot_id: Optional[str] = None
        self._sequence_counter: int = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @classmethod
    def get_instance(cls) -> "PipelineEventBus":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Register current asyncio event loop for thread-safe cross-thread dispatch."""
        self._loop = loop

    def reset_sequence(self, snapshot_id: str) -> None:
        """Reset sequence counter for a new snapshot run."""
        with self._state_lock:
            self._active_snapshot_id = snapshot_id
            self._sequence_counter = 0
            logger.info(f"[EventBus] Sequence reset for snapshot {snapshot_id}")

    def add_subscriber(self, ws: WebSocket) -> None:
        """Add a WebSocket subscriber."""
        with self._state_lock:
            self._subscribers.add(ws)
            logger.info(f"[EventBus] Client connected. Active subscribers: {len(self._subscribers)}")

    def remove_subscriber(self, ws: WebSocket) -> None:
        """Remove a WebSocket subscriber."""
        with self._state_lock:
            self._subscribers.discard(ws)
            logger.info(f"[EventBus] Client disconnected. Active subscribers: {len(self._subscribers)}")

    def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        snapshot_id: Optional[str] = None,
        stage_name: Optional[str] = None,
        stock_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish a versioned pipeline execution event.

        Assigns monotonically increasing event_sequence, saves to DB for Replay Mode,
        and broadcasts to connected WebSockets.
        """
        with self._state_lock:
            self._sequence_counter += 1
            seq_id = self._sequence_counter
            sid = snapshot_id or self._active_snapshot_id or "snap_live"

        import pytz
        from datetime import datetime
        now_str = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()

        # Enforce envelope metadata
        envelope = {
            "pipeline_id": f"pipe_{sid}",
            "snapshot_id": sid,
            "engine_version": "1.0.0",
            "event_sequence": seq_id,
            "event_type": event_type,
            "stage_name": stage_name,
            "stock_symbol": stock_symbol,
            "timestamp": now_str,
            "payload": payload,
        }

        # Save to DB for Replay Mode
        try:
            db.save_pipeline_event(
                snapshot_id=sid,
                sequence_id=seq_id,
                event_type=event_type,
                stage_name=stage_name,
                stock_symbol=stock_symbol,
                payload_dict=envelope,
            )
        except Exception as e:
            logger.error(f"[EventBus] Failed to persist event seq {seq_id}: {e}")

        # Broadcast to WebSockets
        self.broadcast(envelope)
        return envelope

    def broadcast(self, message_dict: Dict[str, Any]) -> None:
        """Broadcast message to all active WebSocket clients."""
        with self._state_lock:
            clients = list(self._subscribers)

        if not clients:
            return

        msg_text = json.dumps(message_dict, default=str)

        async def _send_all():
            for ws in clients:
                try:
                    await ws.send_text(msg_text)
                except Exception:
                    with self._state_lock:
                        self._subscribers.discard(ws)

        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(_send_all(), self._loop)
        else:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(_send_all(), loop)
            except Exception:
                pass


def get_event_bus() -> PipelineEventBus:
    """Module accessor for global PipelineEventBus singleton."""
    return PipelineEventBus.get_instance()
