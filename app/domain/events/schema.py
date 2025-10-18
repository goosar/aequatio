from uuid import UUID, uuid4
import datetime
from typing import Optional, Dict, Any, Generic, TypeVar, Literal

# pydantic may not have stubs available in the environment; tell mypy to ignore import errors
from pydantic import BaseModel, Field, EmailStr, AwareDatetime, ConfigDict  # type: ignore[import]


T = TypeVar("T")


def now_utc() -> datetime.datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.datetime.now(datetime.timezone.utc)


class EventMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    event_type: str  # e.g. "expense.created"
    version: int = 1  # event schema version
    source: str = "aequatio"
    created_at: AwareDatetime = Field(default_factory=now_utc)
    correlation_id: Optional[UUID] = None
    trace_id: Optional[str] = None
    schema_id: Optional[str] = None
    extras: Optional[Dict[str, Any]] = None


class Event(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    metadata: EventMetadata
    payload: T

    def to_json(self, **kwargs) -> str:
        return self.model_dump_json(by_alias=True, exclude_none=True, **kwargs)

    @classmethod
    def from_json(cls, raw: str) -> "Event[Any]":
        return cls.model_validate_json(raw)


class ExpanseEvent(BaseModel):
    expense_id: UUID
    paid_by_user_id: UUID
    timestamp: AwareDatetime = Field(default_factory=now_utc)


class ExpenseCreatedEvent(ExpanseEvent):
    amount_cents: int
    currency: str = "EUR"
    category: str
    description: Optional[str] = None
    group_id: UUID


class ExpenseUpdatedEvent(ExpanseEvent):
    amount_cents: int
    currency: str = "EUR"
    category: str
    description: Optional[str] = None


class ExpenseDeletedEvent(ExpanseEvent):
    pass


class UserCreatedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    user_id: UUID
    user_email: EmailStr
    user_name: str
    timestamp: AwareDatetime = Field(default_factory=now_utc)


EventType = Literal[
    "expense.created", "expense.updated", "expense.deleted", "user.created"
]


def make_event(
    payload: T,
    event_type: EventType,
    *,
    version: int = 1,
    source: str = "aequatio",
    correlation_id: UUID | None = None,
    trace_id: str | None = None,
    schema_id: str | None = None,
    extras: Dict[str, Any] | None = None,
) -> Event[T]:
    meta = EventMetadata(
        event_type=event_type,
        version=version,
        source=source,
        correlation_id=correlation_id,
        trace_id=trace_id,
        schema_id=schema_id,
        extras=extras or {},
    )
    return Event[T](metadata=meta, payload=payload)
