"""Tests for authentication service methods."""

import pytest
from sqlalchemy.orm import Session

from app.application.services.user_service import UserApplicationService
from app.domain.entities.user import User
from app.persistence.models.user import User as UserModel


@pytest.fixture
def user_service(db: Session) -> UserApplicationService:
    """Create a user application service for testing."""
    return UserApplicationService(db)


@pytest.fixture
def registered_user(db: Session) -> User:
    """Create a registered user in the database."""
    user = User.register(
        username="testuser",
        email="test@example.com",
        plain_password="SecurePass123!",
        metadata={},
    )

    # Persist to database
    user_model = UserModel(
        id=user.id,
        username=user.username,
        email=user.email,
        hashed_password=user.hashed_password,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    return user


class TestAuthenticateUser:
    """Test the authenticate_user method."""

    def test_authenticate_with_valid_credentials(
        self, user_service: UserApplicationService, registered_user: User
    ):
        """Should authenticate user with correct email and password."""
        authenticated_user = user_service.authenticate_user(
            email="test@example.com",
            password="SecurePass123!",
        )

        assert authenticated_user is not None
        assert authenticated_user.id == registered_user.id
        assert authenticated_user.email == registered_user.email
        assert authenticated_user.username == registered_user.username

    def test_authenticate_with_invalid_email(self, user_service: UserApplicationService):
        """Should return None for non-existent email."""
        authenticated_user = user_service.authenticate_user(
            email="nonexistent@example.com",
            password="AnyPassword123!",
        )

        assert authenticated_user is None

    def test_authenticate_with_invalid_password(
        self, user_service: UserApplicationService, registered_user: User
    ):
        """Should return None for incorrect password."""
        authenticated_user = user_service.authenticate_user(
            email="test@example.com",
            password="WrongPassword123!",
        )

        assert authenticated_user is None

    def test_authenticate_with_empty_password(
        self, user_service: UserApplicationService, registered_user: User
    ):
        """Should return None for empty password."""
        authenticated_user = user_service.authenticate_user(
            email="test@example.com",
            password="",
        )

        assert authenticated_user is None

    def test_authenticate_inactive_user(
        self, db: Session, user_service: UserApplicationService, registered_user: User
    ):
        """Should return None for inactive user."""
        # Deactivate the user
        assert registered_user.id is not None
        user_service.deactivate_user(registered_user.id)

        # Try to authenticate
        authenticated_user = user_service.authenticate_user(
            email="test@example.com",
            password="SecurePass123!",
        )

        assert authenticated_user is None

    def test_authenticate_case_sensitive_email(
        self, user_service: UserApplicationService, registered_user: User
    ):
        """Should be case-sensitive for email (or handle normalization)."""
        # Note: Depending on your email validation, this might need adjustment
        authenticated_user = user_service.authenticate_user(
            email="TEST@EXAMPLE.COM",
            password="SecurePass123!",
        )

        # If your system normalizes emails, this should work
        # If not, adjust the test accordingly
        # For now, assume case-sensitive
        assert authenticated_user is None


class TestAuthenticateUserEdgeCases:
    """Test edge cases for authentication."""

    def test_authenticate_with_sql_injection_attempt(self, user_service: UserApplicationService):
        """Should safely handle SQL injection attempts."""
        # Try SQL injection in email field
        authenticated_user = user_service.authenticate_user(
            email="admin' OR '1'='1",
            password="anything",
        )

        assert authenticated_user is None

    def test_authenticate_with_special_characters_in_password(
        self, db: Session, user_service: UserApplicationService
    ):
        """Should handle special characters in password correctly."""
        # Create user with special characters in password
        user = User.register(
            username="specialuser",
            email="special@example.com",
            plain_password="P@$$w0rd!#%&*()[]{}",
            metadata={},
        )

        user_model = UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        db.add(user_model)
        db.commit()

        # Should authenticate with exact password
        authenticated_user = user_service.authenticate_user(
            email="special@example.com",
            password="P@$$w0rd!#%&*()[]{}",
        )

        assert authenticated_user is not None
        assert authenticated_user.email == "special@example.com"

    def test_authenticate_with_unicode_password(
        self, db: Session, user_service: UserApplicationService
    ):
        """Should handle Unicode characters in password."""
        # Create user with Unicode password
        user = User.register(
            username="unicodeuser",
            email="unicode@example.com",
            plain_password="Pāsswörd123!",
            metadata={},
        )

        user_model = UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        db.add(user_model)
        db.commit()

        # Should authenticate with exact password
        authenticated_user = user_service.authenticate_user(
            email="unicode@example.com",
            password="Pāsswörd123!",
        )

        assert authenticated_user is not None
        assert authenticated_user.email == "unicode@example.com"
