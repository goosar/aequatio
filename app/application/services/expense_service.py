from uuid import UUID

from sqlalchemy.orm import Session

from app.api.v1.schemas.expense import ExpenseCreateRequest
from app.domain.entities.expense import ExpenseEntity
from app.persistence.repositories.expense_repository import SQLAlchemyExpenseRepository


class ExpenseApplicationService:
    """
    Service class for managing expenses.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.expense_repo = SQLAlchemyExpenseRepository(db)

    def create_expense(self, expense_data: ExpenseCreateRequest, user_id: UUID) -> ExpenseEntity:
        """
        Create a new expense for the authenticated user.

        Args:
            expense_data: The expense creation request data.
            user_id: The ID of the authenticated user (from JWT token).

        Returns:
            The created expense entity.
        """
        expense: ExpenseEntity = ExpenseEntity.create_expense_from_request(
            fk_user_id=user_id,
            title=expense_data.title,
            amount=expense_data.amount,
            currency=expense_data.currency,
            description=expense_data.description,
            category=expense_data.category,
            expensedate=expense_data.expensedate,
            vendor=expense_data.vendor,
        )

        saved_expense = self.expense_repo.save(expense)
        return saved_expense
