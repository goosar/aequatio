"""Tests for outbox repository functions.

This module tests the transactional outbox pattern implementation,
ensuring domain events are persisted correctly within database transactions.
"""

import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.outbox.repository import add_outbox_event
from app.persistence.models.outbox import OutboxEvent


class TestAddOutboxEvent:
    """Test suite for add_outbox_event function."""

    def test_add_outbox_event_with_all_parameters(self):
        """Test adding outbox event with all parameters specified."""
        # Arrange
        db = Mock(spec=Session)
        occurred_at = datetime.datetime(2025, 10, 20, 12, 0, 0)
        payload = {"user_id": "123", "username": "john_doe"}

        # Act
        result = add_outbox_event(
            db=db,
            event_type="user.registered",
            payload=payload,
            aggregate_type="User",
            aggregate_id="123",
            event_version=2,
            occurred_at=occurred_at,
        )

        # Assert
        assert isinstance(result, OutboxEvent)
        assert result.event_type == "user.registered"
        assert result.payload == payload
        assert result.aggregate_type == "User"
        assert result.aggregate_id == "123"
        assert result.event_version == 2
        assert result.occurred_at == occurred_at
        db.add.assert_called_once_with(result)

    def test_add_outbox_event_with_minimal_parameters(self):
        """Test adding outbox event with minimal required parameters."""
        # Arrange
        db = Mock(spec=Session)
        payload = {"message": "test"}

        # Act
        result = add_outbox_event(
            db=db,
            event_type="test.event",
            payload=payload,
        )

        # Assert
        assert result.event_type == "test.event"
        assert result.payload == payload
        assert result.aggregate_type == "DomainEvent"  # Default
        assert result.aggregate_id == "0"  # Default
        assert result.event_version == 1  # Default
        assert isinstance(result.occurred_at, datetime.datetime)
        db.add.assert_called_once()

    def test_add_outbox_event_generates_timestamp_when_not_provided(self):
        """Test that occurred_at is auto-generated when not provided."""
        # Arrange
        db = Mock(spec=Session)
        before = datetime.datetime.utcnow()

        # Act
        result = add_outbox_event(
            db=db,
            event_type="test.event",
            payload={"data": "test"},
        )

        # Assert
        after = datetime.datetime.utcnow()
        assert before <= result.occurred_at <= after

    def test_add_outbox_event_does_not_commit(self):
        """Test that add_outbox_event does not commit the transaction."""
        # Arrange
        db = Mock(spec=Session)

        # Act
        add_outbox_event(
            db=db,
            event_type="test.event",
            payload={"data": "test"},
        )

        # Assert
        db.add.assert_called_once()
        db.commit.assert_not_called()  # Should not commit

    def test_add_outbox_event_with_complex_payload(self):
        """Test adding event with complex nested payload."""
        # Arrange
        db = Mock(spec=Session)
        payload = {
            "user_id": "123",
            "username": "john_doe",
            "metadata": {
                "ip": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "tags": ["new", "verified"],
            },
            "timestamp": "2025-10-20T12:00:00Z",
        }

        # Act
        result = add_outbox_event(
            db=db,
            event_type="user.registered",
            payload=payload,
            aggregate_type="User",
            aggregate_id="123",
        )

        # Assert
        assert result.payload == payload
        assert result.payload["metadata"]["tags"] == ["new", "verified"]

    def test_add_outbox_event_with_empty_payload(self):
        """Test adding event with empty payload."""
        # Arrange
        db = Mock(spec=Session)

        # Act
        result = add_outbox_event(
            db=db,
            event_type="system.ping",
            payload={},
        )

        # Assert
        assert result.payload == {}

    def test_add_outbox_event_preserves_aggregate_type(self):
        """Test that aggregate type is preserved correctly."""
        # Arrange
        db = Mock(spec=Session)
        test_cases = [
            ("User", "123"),
            ("Order", "order-456"),
            ("Payment", "pay-789"),
            ("CustomAggregate", "custom-001"),
        ]

        for aggregate_type, aggregate_id in test_cases:
            # Act
            result = add_outbox_event(
                db=db,
                event_type="test.event",
                payload={"test": "data"},
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
            )

            # Assert
            assert result.aggregate_type == aggregate_type
            assert result.aggregate_id == aggregate_id

    def test_add_outbox_event_with_different_event_versions(self):
        """Test adding events with different schema versions."""
        # Arrange
        db = Mock(spec=Session)

        for version in [1, 2, 5, 10]:
            # Act
            result = add_outbox_event(
                db=db,
                event_type="test.event",
                payload={"version": version},
                event_version=version,
            )

            # Assert
            assert result.event_version == version

    def test_add_outbox_event_with_special_characters_in_event_type(self):
        """Test event types with special characters."""
        # Arrange
        db = Mock(spec=Session)
        event_types = [
            "user.registered",
            "order.created.v2",
            "payment_processed",
            "email-sent",
            "notification:push",
        ]

        for event_type in event_types:
            # Act
            result = add_outbox_event(
                db=db,
                event_type=event_type,
                payload={"type": event_type},
            )

            # Assert
            assert result.event_type == event_type

    def test_add_outbox_event_adds_to_session(self):
        """Test that event is added to the database session."""
        # Arrange
        db = Mock(spec=Session)
        payload = {"test": "data"}

        # Act
        result = add_outbox_event(
            db=db,
            event_type="test.event",
            payload=payload,
        )

        # Assert
        db.add.assert_called_once()
        added_event = db.add.call_args[0][0]
        assert added_event is result
        assert isinstance(added_event, OutboxEvent)


class TestOutboxEventIntegration:
    """Integration tests for outbox event creation."""

    def test_multiple_events_can_be_added_in_same_transaction(self):
        """Test adding multiple events within same transaction."""
        # Arrange
        db = Mock(spec=Session)
        events_data = [
            ("user.registered", {"user_id": "1"}),
            ("user.email_verified", {"user_id": "1"}),
            ("user.profile_updated", {"user_id": "1"}),
        ]

        # Act
        results = []
        for event_type, payload in events_data:
            result = add_outbox_event(db=db, event_type=event_type, payload=payload)
            results.append(result)

        # Assert
        assert len(results) == 3
        assert db.add.call_count == 3
        db.commit.assert_not_called()  # Caller commits

    def test_outbox_event_can_be_rolled_back(self):
        """Test that outbox events can be rolled back if needed."""
        # Arrange
        db = Mock(spec=Session)

        # Act
        result = add_outbox_event(
            db=db,
            event_type="test.event",
            payload={"data": "test"},
        )
        db.rollback()

        # Assert
        db.add.assert_called_once_with(result)
        db.rollback.assert_called_once()


class TestOutboxEventEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.parametrize(
        "aggregate_id",
        [
            "0",
            "123",
            "user-abc-123",
            "550e8400-e29b-41d4-a716-446655440000",  # UUID
            "very-long-id-" + "x" * 80,
        ],
    )
    def test_add_outbox_event_with_various_aggregate_ids(self, aggregate_id):
        """Test various aggregate ID formats."""
        # Arrange
        db = Mock(spec=Session)

        # Act
        result = add_outbox_event(
            db=db,
            event_type="test.event",
            payload={"id": aggregate_id},
            aggregate_id=aggregate_id,
        )

        # Assert
        assert result.aggregate_id == aggregate_id

    def test_add_outbox_event_with_null_values_in_payload(self):
        """Test payload with None/null values."""
        # Arrange
        db = Mock(spec=Session)
        payload = {
            "user_id": "123",
            "optional_field": None,
            "metadata": {"key": None, "value": "test"},
        }

        # Act
        result = add_outbox_event(
            db=db,
            event_type="test.event",
            payload=payload,
        )

        # Assert
        assert result.payload["optional_field"] is None
        assert result.payload["metadata"]["key"] is None

    def test_add_outbox_event_with_very_long_event_type(self):
        """Test event type at maximum length."""
        # Arrange
        db = Mock(spec=Session)
        long_event_type = "domain.subdomain.entity.action." + "x" * 150

        # Act
        result = add_outbox_event(
            db=db,
            event_type=long_event_type,
            payload={"test": "data"},
        )

        # Assert
        assert result.event_type == long_event_type

    def test_add_outbox_event_preserves_timestamp_precision(self):
        """Test that microsecond precision is preserved in timestamps."""
        # Arrange
        db = Mock(spec=Session)
        occurred_at = datetime.datetime(2025, 10, 20, 12, 30, 45, 123456)

        # Act
        result = add_outbox_event(
            db=db,
            event_type="test.event",
            payload={"time": "test"},
            occurred_at=occurred_at,
        )

        # Assert
        assert result.occurred_at == occurred_at
        assert result.occurred_at.microsecond == 123456
