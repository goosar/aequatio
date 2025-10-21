"""Tests for authentication endpoints."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.domain.entities.user import User
from app.persistence.models.user import User as UserModel
from main import app


def override_get_db(test_db: Session):
    """Create a database dependency override for testing."""

    def _get_test_db():
        try:
            yield test_db
        finally:
            pass

    return _get_test_db


@pytest.fixture
def client(db: Session):
    """Create a test client with database dependency override."""
    app.dependency_overrides[get_db] = override_get_db(db)
    yield TestClient(app)
    app.dependency_overrides.clear()


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


class TestLoginEndpoint:
    """Test the POST /auth/login endpoint."""

    def test_login_with_valid_credentials(self, client: TestClient, registered_user: User):
        """Should return JWT token for valid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_with_invalid_email(self, client: TestClient):
        """Should return 401 for non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    def test_login_with_invalid_password(self, client: TestClient, registered_user: User):
        """Should return 401 for incorrect password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    def test_login_with_inactive_user(self, client: TestClient, db: Session, registered_user: User):
        """Should return 401 for inactive user."""
        # Deactivate user
        user_model = db.query(UserModel).filter(UserModel.id == registered_user.id).first()
        if user_model:
            user_model.is_active = False  # type: ignore[assignment]
            db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    def test_login_with_missing_email(self, client: TestClient):
        """Should return 422 for missing email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422

    def test_login_with_missing_password(self, client: TestClient):
        """Should return 422 for missing password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
            },
        )

        assert response.status_code == 422

    def test_login_with_invalid_email_format(self, client: TestClient):
        """Should return 422 for invalid email format."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422

    def test_login_with_empty_credentials(self, client: TestClient):
        """Should return 422 for empty credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "",
                "password": "",
            },
        )

        assert response.status_code == 422

    def test_login_response_contains_www_authenticate_header(self, client: TestClient):
        """Should include WWW-Authenticate header in 401 response."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )

        assert response.status_code == 401
        assert "www-authenticate" in response.headers
        assert response.headers["www-authenticate"] == "Bearer"


class TestTokenValidation:
    """Test JWT token validation."""

    def test_token_can_be_decoded(self, client: TestClient, registered_user: User):
        """Should be able to decode the returned token."""
        # Login to get token
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Decode token using security module
        from app.core.security import verify_token

        payload = verify_token(token)
        assert payload is not None
        assert "sub" in payload
        assert payload["sub"] == str(registered_user.id)

    def test_token_has_expiration(self, client: TestClient, registered_user: User):
        """Should include expiration time in token."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        from app.core.security import verify_token

        payload = verify_token(token)
        assert payload is not None
        assert "exp" in payload

    def test_expired_token_is_rejected(self):
        """Should reject expired tokens."""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": "test-user-id"},
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        from app.core.security import verify_token

        payload = verify_token(expired_token)
        assert payload is None


class TestAuthenticationIntegration:
    """Test complete authentication flow."""

    def test_register_and_login_flow(self, client: TestClient):
        """Should be able to register and immediately login."""
        # Register a new user
        register_response = client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewUserPass123!",
            },
        )

        assert register_response.status_code == 201

        # Login with the new user
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "NewUserPass123!",
            },
        )

        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

    def test_multiple_logins_generate_different_tokens(
        self, client: TestClient, registered_user: User
    ):
        """Should generate tokens for multiple login attempts."""
        import time

        # First login
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        # Wait a moment to ensure different timestamp
        time.sleep(1.1)

        # Second login
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]

        # Both tokens should be valid but different (due to different timestamps)
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2


class TestSecurityBehavior:
    """Test security-related behavior."""

    def test_password_not_leaked_in_error_response(self, client: TestClient):
        """Should not leak password in error responses."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SomePassword123!",
            },
        )

        response_text = response.text.lower()
        assert "somepassword" not in response_text
        assert "password123" not in response_text

    def test_timing_attack_mitigation(self, client: TestClient, registered_user: User):
        """Should take similar time for valid/invalid credentials.

        Note: This is a basic check. Real timing attack testing requires
        statistical analysis over many iterations.
        """
        import time

        # Time with invalid email
        start1 = time.time()
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )
        time1 = time.time() - start1

        # Time with invalid password
        start2 = time.time()
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!",
            },
        )
        time2 = time.time() - start2

        # Both should take roughly similar time
        # (This is a simplified check - real timing tests need more iterations)
        assert abs(time1 - time2) < 0.5  # Within 500ms
