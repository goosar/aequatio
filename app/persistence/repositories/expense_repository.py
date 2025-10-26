from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.expense import ExpenseCategory, ExpenseEntity, ExpenseRepository
from app.persistence.models.expense import SQLAlchemyExpense


class SQLAlchemyExpenseRepository(ExpenseRepository):
    """
    Repository implementation for managing Expense entities using SQLAlchemy ORM.
    This class provides concrete implementation of the ExpenseRepository interface,
    handling the persistence and retrieval of expense records in a database using
    SQLAlchemy sessions.
    Attributes:
        db (Session): SQLAlchemy database session for executing queries.
    Methods:
        save(expense: Expense) -> Expense:
            Persists an expense entity to the database.
        get_by_id(expense_id: UUID) -> Optional[Expense]:
            Retrieves an expense entity by its unique identifier.
        _to_orm(expense: Expense) -> SQLAlchemyExpense:
            Converts a domain Expense model to SQLAlchemy ORM model.
        _from_orm(orm_expense: SQLAlchemyExpense) -> Expense:
            Converts a SQLAlchemy ORM model to domain Expense model.
    """

    def __init__(self, db: Session):
        self.db = db

    def save(self, expense: ExpenseEntity) -> ExpenseEntity:
        orm_expense: SQLAlchemyExpense = self._to_orm(expense)
        self.db.add(orm_expense)
        self.db.flush()  # Ensure ID is generated
        return expense

    def _to_orm(self, expense: ExpenseEntity) -> SQLAlchemyExpense:
        return SQLAlchemyExpense(
            id=expense.id,
            fk_user_id=expense.fk_user_id,
            title=expense.title,
            amount=expense.amount,
            currency=expense.currency,
            description=expense.description,
            category=expense.category.value,
            expensedate=expense.expensedate,
            vendor=expense.vendor,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )

    def _from_orm(self, orm_expense: SQLAlchemyExpense) -> ExpenseEntity:
        return ExpenseEntity(
            id=orm_expense.id,
            fk_user_id=orm_expense.fk_user_id,
            title=orm_expense.title,
            amount=orm_expense.amount,
            currency=orm_expense.currency,
            description=orm_expense.description,
            category=ExpenseCategory(orm_expense.category),
            expensedate=orm_expense.expensedate,
            vendor=orm_expense.vendor,
            created_at=orm_expense.created_at,
            updated_at=orm_expense.updated_at,
        )

    def get_by_id(self, expense_id: UUID) -> Optional[ExpenseEntity]:
        orm_expense = (
            self.db.query(SQLAlchemyExpense).filter(SQLAlchemyExpense.id == expense_id).first()
        )

        return self._from_orm(orm_expense) if orm_expense else None
