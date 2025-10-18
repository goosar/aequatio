"""Domain event schemas.

This module defines all domain events that represent business-significant
occurrences in the system. Events follow a consistent structure with metadata
and strongly-typed payloads.

Architecture:
- EventMetadata: Common envelope for all events (ID, type, tracing, timestamps)
- Event[T]: Generic wrapper combining metadata + typed payload
- Payload classes: Specific event data (ExpenseCreated, UserRegistered, etc.)
- Factory functions: Convenience constructors for creating events

All events are immutable (frozen) to ensure event sourcing integrity.
"""

import datetime
from typing import Any, Dict, Generic, Literal, Optional, TypeVar
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field

# Type variable for generic event payloads
T = TypeVar("T")


# ============================================================================
# UTILITIES
# ============================================================================


def now_utc() -> datetime.datetime:
    """Return timezone-aware UTC datetime.

    Returns:
        Current UTC datetime with timezone information.

    Example:
        >>> dt = now_utc()
        >>> dt.tzinfo is not None
        True
    """
    return datetime.datetime.now(datetime.timezone.utc)


# ============================================================================
# EVENT ENVELOPE
# ============================================================================


class EventMetadata(BaseModel):
    """Metadata envelope for all domain events.

    Provides common fields for event identification, versioning, tracing,
    and correlation across distributed systems.

    Attributes:
        id: Unique event identifier (auto-generated UUID).
        event_type: Event type identifier (e.g., "expense.created").
        version: Schema version for event evolution (default 1).
        source: Service/system that emitted the event.
        created_at: Timestamp when event was created (UTC).
        correlation_id: Links related events in a workflow.
        trace_id: Distributed tracing identifier.
        schema_id: Reference to event schema registry.
        extras: Additional metadata key-value pairs.

    Example:
        >>> metadata = EventMetadata(event_type="user.registered")
        >>> metadata.version
        1
        >>> metadata.source
        'aequatio'
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: str = Field(..., description="Event type (e.g., 'expense.created')")
    version: int = Field(default=1, description="Event schema version")
    source: str = Field(default="aequatio", description="Event source system")
    created_at: AwareDatetime = Field(
        default_factory=now_utc, description="Event creation timestamp (UTC)"
    )
    correlation_id: Optional[UUID] = Field(
        default=None, description="Links related events in a workflow"
    )
    trace_id: Optional[str] = Field(default=None, description="Distributed tracing identifier")
    schema_id: Optional[str] = Field(default=None, description="Schema registry reference")
    extras: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class Event(BaseModel, Generic[T]):
    """Generic event wrapper combining metadata and typed payload.

    All domain events follow this structure: metadata envelope + specific payload.
    The payload type is parameterized for type safety.

    Attributes:
        metadata: Event metadata (ID, type, timestamps, tracing).
        payload: Strongly-typed event payload data.

    Example:
        >>> from uuid import uuid4
        >>> expense_data = ExpenseCreatedPayload(
        ...     expense_id=uuid4(),
        ...     paid_by_user_id=uuid4(),
        ...     amount_cents=1000,
        ...     category="Food",
        ...     group_id=uuid4()
        ... )
        >>> event = make_event(expense_data, "expense.created")
        >>> event.metadata.event_type
        'expense.created'
    """

    model_config = ConfigDict(extra="forbid")

    metadata: EventMetadata = Field(..., description="Event metadata envelope")
    payload: T = Field(..., description="Event-specific payload data")

    def to_json(self, **kwargs: Any) -> str:
        """Serialize event to JSON string.

        Args:
            **kwargs: Additional arguments passed to model_dump_json.

        Returns:
            JSON string representation of the event.

        Example:
            >>> json_str = event.to_json()
            >>> "expense.created" in json_str
            True
        """
        return self.model_dump_json(by_alias=True, exclude_none=True, **kwargs)

    @classmethod
    def from_json(cls, raw: str) -> "Event[Any]":
        """Deserialize event from JSON string.

        Args:
            raw: JSON string to deserialize.

        Returns:
            Event instance with metadata and payload.

        Example:
            >>> json_str = '{"metadata": {...}, "payload": {...}}'
            >>> event = Event.from_json(json_str)
        """
        return cls.model_validate_json(raw)


# ============================================================================
# EXPENSE EVENT PAYLOADS
# ============================================================================


class ExpenseBasePayload(BaseModel):
    """Base payload for all expense-related events.

    Contains common fields shared across expense lifecycle events
    (created, updated, deleted).

    Attributes:
        expense_id: Unique identifier for the expense.
        paid_by_user_id: User who paid for the expense.
        timestamp: When the event occurred (UTC).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    expense_id: UUID = Field(..., description="Unique expense identifier")
    paid_by_user_id: UUID = Field(..., description="User who paid")
    timestamp: AwareDatetime = Field(default_factory=now_utc, description="Event timestamp (UTC)")


class ExpenseCreatedPayload(ExpenseBasePayload):
    """Payload for expense creation events.

    Emitted when a new expense is created in a group.

    Attributes:
        expense_id: Unique identifier for the expense.
        paid_by_user_id: User who paid for the expense.
        timestamp: When the expense was created.
        amount_cents: Amount in cents (avoids floating point issues).
        currency: ISO 4217 currency code (default EUR).
        category: Expense category (e.g., "Food", "Transport").
        description: Optional expense description.
        group_id: Group this expense belongs to.

    Example:
        >>> payload = ExpenseCreatedPayload(
        ...     expense_id=uuid4(),
        ...     paid_by_user_id=uuid4(),
        ...     amount_cents=1250,
        ...     currency="EUR",
        ...     category="Food",
        ...     description="Team lunch",
        ...     group_id=uuid4()
        ... )
    """

    amount_cents: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    group_id: UUID = Field(..., description="Group identifier")


class ExpenseUpdatedPayload(ExpenseBasePayload):
    """Payload for expense update events.

    Emitted when an existing expense is modified.

    Attributes:
        expense_id: Unique identifier for the expense.
        paid_by_user_id: User who paid for the expense.
        timestamp: When the expense was updated.
        amount_cents: Updated amount in cents.
        currency: ISO 4217 currency code (default EUR).
        category: Updated expense category.
        description: Updated expense description.

    Example:
        >>> payload = ExpenseUpdatedPayload(
        ...     expense_id=uuid4(),
        ...     paid_by_user_id=uuid4(),
        ...     amount_cents=1500,
        ...     currency="EUR",
        ...     category="Food",
        ...     description="Updated team lunch cost"
        ... )
    """

    amount_cents: int = Field(..., gt=0, description="Updated amount in cents")
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)


class ExpenseDeletedPayload(ExpenseBasePayload):
    """Payload for expense deletion events.

    Emitted when an expense is deleted/removed from a group.

    Attributes:
        expense_id: Unique identifier for the deleted expense.
        paid_by_user_id: User who originally paid.
        timestamp: When the expense was deleted.

    Example:
        >>> payload = ExpenseDeletedPayload(
        ...     expense_id=uuid4(),
        ...     paid_by_user_id=uuid4()
        ... )

    Note:
        This payload only inherits base fields; no additional data needed.
    """


# ============================================================================
# USER EVENT PAYLOADS
# ============================================================================


class UserRegisteredPayload(BaseModel):
    """Payload for user registration events.

    Emitted when a new user successfully registers in the system.
    This event can trigger welcome emails, analytics, onboarding workflows, etc.

    Attributes:
        user_id: Unique identifier for the newly registered user.
        username: Username chosen by the user.
        email: Email address provided during registration.
        timestamp: When the user registered (UTC).
        metadata: Additional context (IP address, user agent, etc.).

    Example:
        >>> payload = UserRegisteredPayload(
        ...     user_id=123,
        ...     username="john_doe",
        ...     email="john@example.com",
        ...     metadata={"ip_address": "192.168.1.1"}
        ... )
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra={
            "example": {
                "user_id": 123,
                "username": "john_doe",
                "email": "john@example.com",
                "timestamp": "2025-10-18T10:30:00Z",
                "metadata": {"ip_address": "192.168.1.1"},
            }
        },
    )

    user_id: UUID = Field(..., description="Unique user identifier (UUID)")
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., description="User's email address")
    timestamp: AwareDatetime = Field(
        default_factory=now_utc, description="Registration timestamp (UTC)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context (IP, user agent, etc.)"
    )


# ============================================================================
# EVENT TYPE DEFINITIONS
# ============================================================================

EventType = Literal["expense.created", "expense.updated", "expense.deleted", "user.registered"]
"""Supported event types in the system.

Use this literal type for type-safe event type strings.
"""


# ============================================================================
# EVENT FACTORY FUNCTIONS
# ============================================================================


def make_event(
    payload: T,
    event_type: EventType,
    *,
    version: int = 1,
    source: str = "aequatio",
    correlation_id: Optional[UUID] = None,
    trace_id: Optional[str] = None,
    schema_id: Optional[str] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Event[T]:
    """Create an event with metadata envelope and typed payload.

    Convenience factory for constructing properly-structured events
    with consistent metadata.

    Args:
        payload: Event-specific data (ExpenseCreatedPayload, etc.).
        event_type: Type identifier (must match EventType literal).
        version: Event schema version (default 1).
        source: Source system identifier (default "aequatio").
        correlation_id: Links related events in a workflow.
        trace_id: Distributed tracing identifier.
        schema_id: Reference to event schema registry.
        extras: Additional metadata key-value pairs.

    Returns:
        Event[T] with metadata and payload.

    Example:
        >>> expense_data = ExpenseCreatedPayload(
        ...     expense_id=uuid4(),
        ...     paid_by_user_id=uuid4(),
        ...     amount_cents=1000,
        ...     category="Food",
        ...     group_id=uuid4()
        ... )
        >>> event = make_event(
        ...     expense_data,
        ...     "expense.created",
        ...     correlation_id=uuid4(),
        ...     trace_id="abc-123"
        ... )
        >>> event.metadata.event_type
        'expense.created'
    """
    metadata = EventMetadata(
        event_type=event_type,
        version=version,
        source=source,
        correlation_id=correlation_id,
        trace_id=trace_id,
        schema_id=schema_id,
        extras=extras,
    )
    return Event[T](metadata=metadata, payload=payload)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Utilities
    "now_utc",
    # Event envelope
    "EventMetadata",
    "Event",
    "EventType",
    # Expense payloads
    "ExpenseBasePayload",
    "ExpenseCreatedPayload",
    "ExpenseUpdatedPayload",
    "ExpenseDeletedPayload",
    # User payloads
    "UserRegisteredPayload",
    # Factory
    "make_event",
]
