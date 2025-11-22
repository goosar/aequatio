from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain.entities.expense import ExpenseCategory


class ExpenseCreateCommand(BaseModel):
    """Request schema for creating a new expense.

    Attributes:
        title: Title of the expense (1-100 characters).
        amount: Amount of the expense (positive float).
        currency: Currency code (3 uppercase letters, e.g., USD, EUR).
        description: Optional description of the expense (max 500 characters).
        category: Category of the expense.
        expensedate: Date and time when the expense was made.
        vendor: Optional vendor of the expense.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Title of the expense",
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Amount of the expense (must be positive)",
    )
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="Currency code (3 uppercase letters)",
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="Optional description of the expense",
    )
    category: ExpenseCategory = Field(
        ...,
        description="Category of the expense",
    )
    expensedate: datetime = Field(
        ...,
        description="Date and time when the expense was made",
    )
    vendor: str | None = Field(
        None,
        max_length=100,
        description="Optional vendor of the expense",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate that the currency code is a valid ISO 4217 code."""
        valid_currencies = {"USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY"}
        if v not in valid_currencies:
            raise ValueError(f"Currency '{v}' is not a valid ISO 4217 code")
        return v

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models
        json_schema_extra = {
            "example": {
                "title": "Office Supplies",
                "amount": 150.75,
                "currency": "USD",
                "description": "Purchase of office supplies for Q1",
                "category": "Sonstiges",
                "expensedate": "2024-06-15T14:30:00Z",
                "vendor": "Office Depot",
            }
        }


class ExpenseResponse(BaseModel):
    """Response schema for an expense.

    Attributes:
        id: Unique identifier of the expense.
        title: Title of the expense.
        amount: Amount of the expense.
        currency: Currency code.
        description: Optional description of the expense.
        category: Category of the expense.
        expensedate: Date and time when the expense was made.
        vendor: Optional vendor of the expense.
        created_at: Timestamp when the expense was created.
        updated_at: Timestamp when the expense was last updated.
    """

    id: UUID
    title: str
    amount: float
    currency: str
    description: str | None
    category: ExpenseCategory
    expensedate: datetime
    vendor: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models
