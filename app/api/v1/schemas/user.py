"""User API schemas for request and response validation.

This module defines Pydantic models for user-related API operations,
ensuring type safety and validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Request schema for user registration.

    Attributes:
        username: Unique username (3-50 characters, alphanumeric + underscore).
        email: Valid email address.
        password: Password meeting security requirements.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Alphanumeric username with underscores",
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Secure password (min 8 chars)"
    )

    @field_validator("username")
    @classmethod
    def username_no_reserved(cls, v: str) -> str:
        """Prevent registration of reserved usernames."""
        reserved = {"admin", "root", "system", "api", "administrator"}
        if v.lower() in reserved:
            raise ValueError(f"Username '{v}' is reserved")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123!",
            }
        }


class UserResponse(BaseModel):
    """Response schema for user data (excludes sensitive fields).

    Attributes:
        id: Unique user identifier (UUID).
        username: User's username.
        email: User's email address.
        is_active: Whether the account is active.
        created_at: Account creation timestamp.
    """

    id: UUID
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "john_doe",
                "email": "john@example.com",
                "is_active": True,
                "created_at": "2025-10-18T10:30:00Z",
            }
        }
