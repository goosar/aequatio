"""Outbox repository for transactional event publishing.

This module provides functions to add domain events to the outbox table
within the same database transaction as aggregate changes, ensuring
exactly-once delivery guarantees.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.persistence.models.outbox import OutboxEvent


def add_outbox_event(
    db: Session,
    event_type: str,
    payload: Dict[str, Any],
    aggregate_type: str = "DomainEvent",
    aggregate_id: str = "0",
    event_version: int = 1,
    occurred_at: Optional[datetime.datetime] = None,
) -> OutboxEvent:
    """Persist an outbox event within the current transaction.

    This function adds a domain event to the outbox table without committing.
    The caller is responsible for committing the transaction to ensure
    atomicity between aggregate changes and event publishing.

    Args:
        db: SQLAlchemy session (must be same transaction as aggregate).
        event_type: Event type identifier (e.g., "user.registered").
        payload: Event payload as dictionary.
        aggregate_type: Aggregate type (e.g., "User", default "DomainEvent").
        aggregate_id: Aggregate identifier (default "0" for general events).
        event_version: Event schema version (default 1).
        occurred_at: Event occurrence timestamp (default UTC now).

    Returns:
        Created OutboxEvent instance.

    Example:
        >>> event_data = {"user_id": 123, "username": "john"}
        >>> outbox_event = add_outbox_event(
        ...     db=db,
        ...     event_type="user.registered",
        ...     payload=event_data,
        ...     aggregate_type="User",
        ...     aggregate_id="123"
        ... )
        >>> db.commit()  # Commit transaction atomically
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
    db.add(evt)
    # Do not commit here; caller commits to ensure atomicity
    return evt
