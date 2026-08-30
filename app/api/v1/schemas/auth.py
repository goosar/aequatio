"""Authentication schemas for login and token responses."""

from pydantic import BaseModel, EmailStr

from app.api.v1.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Request schema for user login.

    Attributes:
        email: User's email address.
        password: User's plaintext password.

    Example:
        >>> login = LoginRequest(
        ...     email="user@example.com",
        ...     password="SecurePass123!"
        ... )
    """

    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }
    }


class TokenResponse(BaseModel):
    """Response schema for successful login.

    Attributes:
        access_token: JWT access token for API authentication.
        token_type: Type of token (always "bearer").
        user: Authenticated user's public profile.

    Example:
        >>> response = TokenResponse(
        ...     access_token="eyJ...",
        ...     token_type="bearer",
        ...     user=UserResponse(
        ...         id="550e8400-e29b-41d4-a716-446655440000",
        ...         username="john_doe",
        ...         email="john@example.com",
        ...         is_active=True,
        ...         created_at="2025-10-18T10:30:00Z",
        ...     ),
        ... )
    """

    access_token: str
    token_type: str = "bearer"
    user: UserResponse

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "john_doe",
                    "email": "john@example.com",
                    "is_active": True,
                    "created_at": "2025-10-18T10:30:00Z",
                },
            }
        }
    }
