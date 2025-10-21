"""Authentication schemas for login and token responses."""

from pydantic import BaseModel, EmailStr


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

    Example:
        >>> response = TokenResponse(
        ...     access_token="eyJ...",
        ...     token_type="bearer"
        ... )
    """

    access_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    }
