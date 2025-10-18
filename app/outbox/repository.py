from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from persistence.models.Outbox import OutboxEvent
from sqlalchemy.orm import Session


def add_outbox_event(
    session: Session,
    aggregate_type: str,
    aggregate_id: str,
    event_type: str,
    event_version: int,
    payload: Dict[str, Any],
    occurred_at: Optional[datetime.datetime] = None,
) -> OutboxEvent:
    """
    Persist an OutboxEvent using the provided SQLAlchemy session.
    Use this inside the same transaction that updates aggregates.
    """
    if occurred_at is None:
        occurred_at = datetime.datetime.utcnow()

    evt = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        event_version=event_version,
        payload=payload,
        occurred_at=occurred_at,
    )
    session.add(evt)
    # do not commit here; caller should commit the transaction so outbox write is atomic with aggregate changes
    return evt
