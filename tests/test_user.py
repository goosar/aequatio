"""Tests for User domain entity (Aggregate Root).

This module tests the User entity's business logic, invariants,
and domain event emission following DDD principles.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from app.domain.entities.user import User
from app.domain.events.schema import UserRegisteredPayload


class TestUserRegistration:
    """Test cases for User.register() factory method."""

    def test_register_creates_user_with_valid_data(self):
        """Test successful user registration with valid data."""
        username = "john_doe"
        email = "john@example.com"
        password = "SecurePass123!"

        user = User.register(username, email, password)

        assert user.username == username
        assert user.email == email
        assert user.is_active is True
        assert user.hashed_password != password  # Password should be hashed
        assert user.hashed_password.startswith("$2b$")  # Bcrypt hash
        assert isinstance(user.created_at, datetime)
        assert user.updated_at is None

    def test_register_with_metadata(self):
        """Test registration with metadata for event."""
        metadata = {"ip": "192.168.1.1", "user_agent": "Mozilla/5.0"}

        user = User.register("john_doe", "john@example.com", "SecurePass123!", metadata)

        assert user.has_events()
        events = user.get_events()
        assert len(events) == 1
        event = events[0]
        assert event.metadata.event_type == "user.registered"
        assert isinstance(event.payload, UserRegisteredPayload)
        assert event.payload.username == "john_doe"
        assert event.payload.email == "john@example.com"
        assert event.payload.metadata == metadata

    def test_register_emits_domain_event(self):
        """Test that registration emits UserRegistered domain event."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")

        assert user.has_events() is True
        events = user.get_events()
        assert len(events) == 1

        event = events[0]
        assert event.metadata.event_type == "user.registered"
        assert event.payload.username == "john_doe"
        assert event.payload.email == "john@example.com"

    def test_register_rejects_weak_password(self):
        """Test that weak passwords are rejected."""
        with pytest.raises(ValueError, match="Password validation failed"):
            User.register("john_doe", "john@example.com", "weak")

    def test_register_rejects_password_no_uppercase(self):
        """Test rejection of password without uppercase letter."""
        with pytest.raises(ValueError, match="uppercase"):
            User.register("john_doe", "john@example.com", "password123!")

    def test_register_rejects_password_no_lowercase(self):
        """Test rejection of password without lowercase letter."""
        with pytest.raises(ValueError, match="lowercase"):
            User.register("john_doe", "john@example.com", "PASSWORD123!")

    def test_register_rejects_password_no_digit(self):
        """Test rejection of password without digit."""
        with pytest.raises(ValueError, match="digit"):
            User.register("john_doe", "john@example.com", "SecurePass!")

    def test_register_rejects_password_no_special_char(self):
        """Test rejection of password without special character."""
        with pytest.raises(ValueError, match="special character"):
            User.register("john_doe", "john@example.com", "SecurePass123")

    def test_register_rejects_password_too_short(self):
        """Test rejection of password shorter than 8 characters."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            User.register("john_doe", "john@example.com", "Pass1!")

    def test_register_rejects_reserved_usernames(self):
        """Test that reserved usernames are rejected."""
        reserved_usernames = ["admin", "root", "system", "api", "administrator", "mod", "moderator"]

        for username in reserved_usernames:
            with pytest.raises(ValueError, match=f"Username '{username}' is reserved"):
                User.register(username, "user@example.com", "SecurePass123!")

    def test_register_rejects_reserved_usernames_case_insensitive(self):
        """Test that reserved usernames are rejected regardless of case."""
        with pytest.raises(ValueError, match="Username 'ADMIN' is reserved"):
            User.register("ADMIN", "user@example.com", "SecurePass123!")

        with pytest.raises(ValueError, match="Username 'Admin' is reserved"):
            User.register("Admin", "user@example.com", "SecurePass123!")

    def test_register_with_minimum_valid_username(self):
        """Test registration with minimum valid username length."""
        user = User.register("abc", "user@example.com", "SecurePass123!")
        assert user.username == "abc"

    def test_register_with_maximum_valid_username(self):
        """Test registration with maximum valid username length."""
        username = "a" * 50  # Maximum length
        user = User.register(username, "user@example.com", "SecurePass123!")
        assert user.username == username

    def test_register_with_underscores_in_username(self):
        """Test registration with underscores in username."""
        user = User.register("john_doe_123", "user@example.com", "SecurePass123!")
        assert user.username == "john_doe_123"


class TestUserDeactivation:
    """Test cases for User.deactivate() command."""

    def test_deactivate_active_user(self):
        """Test deactivating an active user."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        assert user.is_active is True

        user.deactivate("Policy violation")

        assert user.is_active is False
        assert user.updated_at is not None
        assert isinstance(user.updated_at, datetime)

    def test_deactivate_with_reason(self):
        """Test deactivation with a reason."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")

        # Reason is accepted but not stored (could be added to event in future)
        user.deactivate(reason="Account suspension")
        assert user.is_active is False

    def test_deactivate_without_reason(self):
        """Test deactivation without a reason."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")

        user.deactivate()
        assert user.is_active is False

    def test_deactivate_already_inactive_user_raises_error(self):
        """Test that deactivating an already inactive user raises an error."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user.deactivate()

        with pytest.raises(ValueError, match="already inactive"):
            user.deactivate()

    def test_deactivate_updates_timestamp(self):
        """Test that deactivation updates the updated_at timestamp."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        original_created_at = user.created_at

        user.deactivate()

        assert user.updated_at is not None
        assert user.updated_at >= original_created_at  # >= to handle fast execution


class TestUserActivation:
    """Test cases for User.activate() command."""

    def test_activate_inactive_user(self):
        """Test activating an inactive user."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user.deactivate()
        assert user.is_active is False

        user.activate()

        assert user.is_active is True
        assert user.updated_at is not None

    def test_activate_already_active_user_raises_error(self):
        """Test that activating an already active user raises an error."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")

        with pytest.raises(ValueError, match="already active"):
            user.activate()

    def test_activate_updates_timestamp(self):
        """Test that activation updates the updated_at timestamp."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user.deactivate()

        user.activate()

        assert user.updated_at is not None
        assert isinstance(user.updated_at, datetime)


class TestUserEmailChange:
    """Test cases for User.change_email() command."""

    def test_change_email_to_new_address(self):
        """Test changing email to a new address."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        new_email = "newemail@example.com"

        user.change_email(new_email)

        assert user.email == new_email
        assert user.updated_at is not None

    def test_change_email_rejects_same_email(self):
        """Test that changing to the same email raises an error."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")

        with pytest.raises(ValueError, match="same as current email"):
            user.change_email("john@example.com")

    def test_change_email_updates_timestamp(self):
        """Test that email change updates the updated_at timestamp."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")

        user.change_email("newemail@example.com")

        assert user.updated_at is not None
        assert isinstance(user.updated_at, datetime)


class TestUserEventManagement:
    """Test cases for domain event management."""

    def test_has_events_returns_true_when_events_exist(self):
        """Test that has_events returns True when events exist."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        assert user.has_events() is True

    def test_has_events_returns_false_when_no_events(self):
        """Test that has_events returns False when no events."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user.clear_events()
        assert user.has_events() is False

    def test_get_events_returns_copy_of_events(self):
        """Test that get_events returns a copy of events."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        events1 = user.get_events()
        events2 = user.get_events()

        assert events1 == events2
        assert events1 is not events2  # Different list instances

    def test_clear_events_removes_all_events(self):
        """Test that clear_events removes all events."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        assert user.has_events() is True

        user.clear_events()

        assert user.has_events() is False
        assert len(user.get_events()) == 0

    def test_update_event_user_id_updates_user_and_events(self):
        """Test that update_event_user_id updates user ID and event payloads."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        new_user_id = uuid4()

        user.update_event_user_id(new_user_id)

        assert user.id == new_user_id
        events = user.get_events()
        for event in events:
            if hasattr(event.payload, "user_id"):
                assert event.payload.user_id == new_user_id

    def test_update_event_user_id_with_uuid(self):
        """Test updating event user ID with a UUID."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user_id = uuid4()

        user.update_event_user_id(user_id)

        assert user.id == user_id
        events = user.get_events()
        assert events[0].payload.user_id == user_id


class TestUserQueries:
    """Test cases for query methods (no state mutation)."""

    def test_can_login_returns_true_for_active_user(self):
        """Test that active users can log in."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        assert user.can_login() is True

    def test_can_login_returns_false_for_inactive_user(self):
        """Test that inactive users cannot log in."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user.deactivate()
        assert user.can_login() is False

    def test_can_login_after_reactivation(self):
        """Test that users can log in after reactivation."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user.deactivate()
        user.activate()
        assert user.can_login() is True


class TestUserRepresentation:
    """Test cases for string representation."""

    def test_repr_without_id(self):
        """Test string representation without ID."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        repr_str = repr(user)
        assert "john_doe" in repr_str
        assert "User" in repr_str
        assert "active=True" in repr_str

    def test_repr_with_id(self):
        """Test string representation with ID."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user_id = uuid4()
        user.update_event_user_id(user_id)

        repr_str = repr(user)
        assert "john_doe" in repr_str
        assert str(user_id) in repr_str
        assert "active=True" in repr_str

    def test_repr_inactive_user(self):
        """Test string representation of inactive user."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        user.deactivate()

        repr_str = repr(user)
        assert "active=False" in repr_str


class TestUserValidation:
    """Test cases for Pydantic validation."""

    def test_username_too_short_raises_error(self):
        """Test that username shorter than 3 characters raises validation error."""
        with pytest.raises(ValueError):
            User(
                username="ab",  # Too short
                email="user@example.com",
                hashed_password="$2b$12$hash",
            )

    def test_username_too_long_raises_error(self):
        """Test that username longer than 50 characters raises validation error."""
        with pytest.raises(ValueError):
            User(
                username="a" * 51,  # Too long
                email="user@example.com",
                hashed_password="$2b$12$hash",
            )

    def test_username_invalid_characters_raises_error(self):
        """Test that username with invalid characters raises validation error."""
        invalid_usernames = [
            "john-doe",  # Hyphen not allowed
            "john.doe",  # Dot not allowed
            "john@doe",  # @ not allowed
            "john doe",  # Space not allowed
        ]

        for username in invalid_usernames:
            with pytest.raises(ValueError):
                User(
                    username=username,
                    email="user@example.com",
                    hashed_password="$2b$12$hash",
                )

    def test_invalid_email_raises_error(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(ValueError):
            User(
                username="john_doe",
                email="invalid-email",  # Invalid email
                hashed_password="$2b$12$hash",
            )


class TestUserWorkflows:
    """Integration tests for complete user workflows."""

    def test_complete_registration_workflow(self):
        """Test complete registration workflow with event handling."""
        # Register user
        user = User.register(
            "john_doe", "john@example.com", "SecurePass123!", metadata={"ip": "192.168.1.1"}
        )

        # Verify user state
        assert user.username == "john_doe"
        assert user.is_active is True

        # Verify event was emitted
        assert user.has_events() is True
        events = user.get_events()
        assert len(events) == 1
        assert events[0].metadata.event_type == "user.registered"

        # Simulate repository persisting and getting ID
        user_id = uuid4()
        user.update_event_user_id(user_id)
        assert user.id == user_id

        # Clear events after committing to outbox
        user.clear_events()
        assert user.has_events() is False

    def test_deactivation_and_reactivation_workflow(self):
        """Test user deactivation and reactivation workflow."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")

        # Initially active
        assert user.can_login() is True

        # Deactivate
        user.deactivate("Policy violation")
        assert user.can_login() is False
        assert user.is_active is False

        # Reactivate
        user.activate()
        assert user.can_login() is True
        assert user.is_active is True

    def test_email_change_workflow(self):
        """Test email change workflow."""
        user = User.register("john_doe", "john@example.com", "SecurePass123!")
        original_email = user.email

        # Change email
        new_email = "newemail@example.com"
        user.change_email(new_email)

        assert user.email == new_email
        assert user.email != original_email
        assert user.updated_at is not None

    @pytest.mark.parametrize(
        "username,email,password,should_succeed",
        [
            ("valid_user", "valid@example.com", "ValidPass123!", True),
            ("abc", "short@example.com", "ShortPass1!", True),
            ("a" * 50, "long@example.com", "LongUserPass1!", True),
            ("admin", "admin@example.com", "AdminPass123!", False),  # Reserved
            ("valid_user", "valid@example.com", "weak", False),  # Weak password
        ],
    )
    def test_registration_validation_matrix(
        self, username: str, email: str, password: str, should_succeed: bool
    ):
        """Test registration with various combinations of valid/invalid data."""
        if should_succeed:
            user = User.register(username, email, password)
            assert user.username == username
            assert user.email == email
        else:
            with pytest.raises(ValueError):
                User.register(username, email, password)
