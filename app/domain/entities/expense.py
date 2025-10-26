from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from pydantic.types import UUID


class ExpenseCategory(str, Enum):
    """Enumeration of possible expense categories."""

    LEBENSMITTEL = "Lebensmittel"
    LIEFERSERVICE = "Lieferservice"
    DROGERIEARTIKEL = "Drogerieartikel"
    URLAUB = "Urlaubsreisen"
    KLEIDUNG = "Kleidung"
    OTHER = "Sonstiges"


class ExpenseEntity(BaseModel):
    id: Optional[UUID] = None

    fk_user_id: UUID

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

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @staticmethod
    def create_expense_from_request(
        fk_user_id: UUID,
        title: str,
        amount: float,
        currency: str,
        description: Optional[str],
        category: ExpenseCategory,
        expensedate: datetime,
        vendor: Optional[str],
    ) -> "ExpenseEntity":
        expense_id: UUID = uuid4()
        return ExpenseEntity(
            id=expense_id,
            fk_user_id=fk_user_id,
            title=title,
            amount=amount,
            currency=currency,
            description=description,
            category=category,
            expensedate=expensedate,
            vendor=vendor,
        )


class ExpenseRepository(ABC):
    """Abstract base class for expense
    reports.
    """

    @abstractmethod
    def save(self, expense: ExpenseEntity) -> ExpenseEntity:
        """Persist an expense entity.

        Args:
            expense: Expense domain entity to persist.

        Returns:
            The persisted Expense entity with updated fields (e.g., ID).
        """

    @abstractmethod
    def get_by_id(self, expense_id: UUID) -> Optional[ExpenseEntity]:
        """Find expense by ID.

        Args:
            expense_id: Expense UUID to search for.

        Returns:
            Expense domain entity if found, None otherwise.
        """
