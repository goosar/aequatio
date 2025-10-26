"""Expense persistence Model"""

from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExpenseCategory(str, Enum):
    """Enumeration of possible expense categories."""

    LEBENSMITTEL = "Lebensmittel"
    LIEFERSERVICE = "Lieferservice"
    DROGERIEARTIKEL = "Drogerieartikel"
    URLAUB = "Urlaubsreisen"
    KLEIDUNG = "Kleidung"
    OTHER = "Sonstiges"


class SQLAlchemyExpense(Base):
    """Expense database model.

    Represents an expense entity in the database with relevant attributes.

    Attributes:
        id: Unique identifier for the expense (primary key).
        title: Title of the expense.
        amount: Amount of the expense.
        currency: Currency code of the expense.
        description: Optional description of the expense.
        category: Category of the expense.
        expensedate: Date and time when the expense was made.
        vendor: Optional vendor of the expense.
        created_at: Timestamp of expense creation (auto-generated).
        updated_at: Timestamp of last update (auto-updated on modification).
    """

    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    fk_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    description = Column(String, nullable=True)
    category = Column(SQLEnum(ExpenseCategory), nullable=False)
    expensedate = Column(DateTime(timezone=True), nullable=False)
    vendor = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"))

    user = relationship("User", back_populates="expenses")

    def __repr__(self) -> str:
        """Return string representation of the Expense instance.

        Returns:
            String representation showing title and amount.
        """
        return (
            f"<Expense(id={self.id}, title='{self.title}', amount={self.amount} {self.currency})>"
        )
