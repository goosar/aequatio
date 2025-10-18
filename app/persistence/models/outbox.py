from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database import Base  # Import from unified location


class OutboxEvent(Base):
    __tablename__ = "events_outbox"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String(length=100), nullable=False)
    aggregate_id = Column(String(length=100), nullable=False, index=True)
    event_type = Column(String(length=200), nullable=False)
    event_version = Column(Integer, nullable=False, default=1)
    payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=False), nullable=False, default=datetime.datetime.utcnow)
    created_at = Column(DateTime(timezone=False), nullable=False, default=datetime.datetime.utcnow)
    published_at = Column(DateTime(timezone=False), nullable=True, index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)

    __table_args__ = (Index("ix_events_outbox_unpublished", "published_at"),)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "payload": self.payload,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published_at": (self.published_at.isoformat() if self.published_at else None),
            "attempt_count": self.attempt_count,
            "last_error": self.last_error,
        }
