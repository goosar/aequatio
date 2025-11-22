"""Tests for Expense application service.

This module tests the ExpenseApplicationService for expense creation business logic.
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.api.v1.schemas.expense import ExpenseCreateCommand
from app.application.services.expense_service import ExpenseApplicationService
from app.domain.entities.expense import ExpenseCategory, ExpenseEntity
from app.persistence.models.expense import SQLAlchemyExpense
from app.persistence.models.user import User as UserModel


class TestExpenseApplicationServiceCreate:
    """Test cases for creating expenses via the application service."""

    def test_create_expense_successfully(self, db):
        """Test creating an expense through the application service."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Create request data
        request_data = ExpenseCreateCommand(
            title="Office Supplies",
            amount=150.75,
            currency="USD",
            description="Purchase of office supplies for Q1",
            category=ExpenseCategory.OTHER,
            expensedate=datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc),
            vendor="Office Depot",
        )

        # Create expense via service
        service = ExpenseApplicationService(db)
        created_expense = service.create_expense(request_data, user.id)

        # Verify returned expense
        assert created_expense is not None
        assert isinstance(created_expense, ExpenseEntity)
        assert created_expense.id is not None
        assert created_expense.fk_user_id == user.id
        assert created_expense.title == "Office Supplies"
        assert created_expense.amount == 150.75
        assert created_expense.currency == "USD"
        assert created_expense.description == "Purchase of office supplies for Q1"
        assert created_expense.category == ExpenseCategory.OTHER
        assert created_expense.vendor == "Office Depot"

        # Verify expense is persisted in database
        db_expense = db.query(SQLAlchemyExpense).filter_by(fk_user_id=user.id).first()
        assert db_expense is not None
        assert db_expense.title == "Office Supplies"
        assert db_expense.amount == 150.75

    def test_create_expense_without_optional_fields(self, db):
        """Test creating an expense without optional fields."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Create request without optional fields
        request_data = ExpenseCreateCommand(
            title="Groceries",
            amount=50.0,
            currency="EUR",
            description=None,
            category=ExpenseCategory.LEBENSMITTEL,
            expensedate=datetime.now(timezone.utc),
            vendor=None,
        )

        # Create expense via service
        service = ExpenseApplicationService(db)
        created_expense = service.create_expense(request_data, user.id)

        # Verify
        assert created_expense.description is None
        assert created_expense.vendor is None

        # Verify in database
        db_expense = db.query(SQLAlchemyExpense).filter_by(id=created_expense.id).first()
        assert db_expense is not None
        assert db_expense.description is None
        assert db_expense.vendor is None

    def test_create_multiple_expenses_for_user(self, db):
        """Test creating multiple expenses for the same user."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        service = ExpenseApplicationService(db)

        # Create multiple expenses
        expenses = []
        for i in range(3):
            request_data = ExpenseCreateCommand(
                title=f"Expense {i + 1}",
                amount=100.0 * (i + 1),
                currency="USD",
                description=f"Description {i + 1}",
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
                vendor=None,
            )
            expense = service.create_expense(request_data, user.id)
            expenses.append(expense)

        # Verify all expenses are created
        assert len(expenses) == 3
        db_expenses = db.query(SQLAlchemyExpense).filter_by(fk_user_id=user.id).all()
        assert len(db_expenses) == 3

    def test_create_expense_all_categories(self, db):
        """Test creating expenses with all available categories."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        service = ExpenseApplicationService(db)
        categories = [
            ExpenseCategory.LEBENSMITTEL,
            ExpenseCategory.LIEFERSERVICE,
            ExpenseCategory.DROGERIEARTIKEL,
            ExpenseCategory.URLAUB,
            ExpenseCategory.KLEIDUNG,
            ExpenseCategory.OTHER,
        ]

        for category in categories:
            request_data = ExpenseCreateCommand(
                title=f"Test {category.value}",
                amount=100.0,
                currency="EUR",
                description=None,
                category=category,
                expensedate=datetime.now(timezone.utc),
                vendor=None,
            )
            created_expense = service.create_expense(request_data, user.id)
            assert created_expense.category == category

            # Verify in database
            db_expense = db.query(SQLAlchemyExpense).filter_by(id=created_expense.id).first()
            assert db_expense.category == category

    def test_create_expense_with_different_currencies(self, db):
        """Test creating expenses with different currency codes."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        service = ExpenseApplicationService(db)
        currencies = ["USD", "EUR", "GBP", "JPY"]

        for currency in currencies:
            request_data = ExpenseCreateCommand(
                title=f"Expense in {currency}",
                amount=100.0,
                currency=currency,
                description=None,
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
                vendor=None,
            )
            created_expense = service.create_expense(request_data, user.id)
            assert created_expense.currency == currency

    def test_create_expense_with_long_values(self, db):
        """Test creating expense with maximum allowed field lengths."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Create request with long values
        long_title = "A" * 100  # Maximum length
        long_description = "B" * 500  # Maximum length
        long_vendor = "C" * 100  # Maximum length

        request_data = ExpenseCreateCommand(
            fk_user_id=user.id,
            title=long_title,
            amount=999.99,
            currency="USD",
            description=long_description,
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
            vendor=long_vendor,
        )

        service = ExpenseApplicationService(db)
        created_expense = service.create_expense(request_data, user.id)

        # Verify
        assert created_expense.title == long_title
        assert len(created_expense.title) == 100
        assert created_expense.description == long_description
        assert len(created_expense.description) == 500
        assert created_expense.vendor == long_vendor
        assert len(created_expense.vendor) == 100

    def test_create_expense_with_special_characters(self, db):
        """Test creating expense with special characters in text fields."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        request_data = ExpenseCreateCommand(
            fk_user_id=user.id,
            title="Café & Restaurant: €50",
            amount=50.0,
            currency="EUR",
            description="Lunch @ Café d'Or - 50% discount!",
            category=ExpenseCategory.LIEFERSERVICE,
            expensedate=datetime.now(timezone.utc),
            vendor="Café & Co.",
        )

        service = ExpenseApplicationService(db)
        created_expense = service.create_expense(request_data, user.id)

        # Verify special characters are preserved
        assert "Café" in created_expense.title
        assert "€" in created_expense.title
        assert "@" in created_expense.description
        assert "50%" in created_expense.description
        assert "&" in created_expense.vendor

    def test_create_expense_with_very_small_amount(self, db):
        """Test creating expense with minimum positive amount."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        request_data = ExpenseCreateCommand(
            fk_user_id=user.id,
            title="Minimal Expense",
            amount=0.01,  # Smallest positive amount
            currency="USD",
            description=None,
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
            vendor=None,
        )

        service = ExpenseApplicationService(db)
        created_expense = service.create_expense(request_data, user.id)

        assert created_expense.amount == 0.01

    def test_create_expense_with_large_amount(self, db):
        """Test creating expense with large amount."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        request_data = ExpenseCreateCommand(
            fk_user_id=user.id,
            title="Large Purchase",
            amount=999999.99,
            currency="USD",
            description=None,
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
            vendor=None,
        )

        service = ExpenseApplicationService(db)
        created_expense = service.create_expense(request_data, user.id)

        assert created_expense.amount == 999999.99

    def test_create_expense_with_past_date(self, db):
        """Test creating expense with date in the past."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        past_date = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        request_data = ExpenseCreateCommand(
            fk_user_id=user.id,
            title="Past Expense",
            amount=100.0,
            currency="USD",
            description=None,
            category=ExpenseCategory.OTHER,
            expensedate=past_date,
            vendor=None,
        )

        service = ExpenseApplicationService(db)
        created_expense = service.create_expense(request_data, user.id)

        assert created_expense.expensedate == past_date

    def test_create_expense_generates_unique_ids(self, db):
        """Test that each expense gets a unique ID."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        service = ExpenseApplicationService(db)
        expense_ids = set()

        # Create multiple expenses
        for i in range(5):
            request_data = ExpenseCreateCommand(
                fk_user_id=user.id,
                title=f"Expense {i}",
                amount=100.0,
                currency="USD",
                description=None,
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
                vendor=None,
            )
            created_expense = service.create_expense(request_data, user.id)
            expense_ids.add(created_expense.id)

        # All IDs should be unique
        assert len(expense_ids) == 5

    def test_create_expense_preserves_timestamp(self, db):
        """Test that expense creation preserves the created_at timestamp."""
        # Create a test user
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        request_data = ExpenseCreateCommand(
            fk_user_id=user.id,
            title="Timestamped Expense",
            amount=100.0,
            currency="USD",
            description=None,
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
            vendor=None,
        )

        service = ExpenseApplicationService(db)
        created_expense = service.create_expense(request_data, user.id)

        # Verify created_at is set
        assert created_expense.created_at is not None
        assert isinstance(created_expense.created_at, datetime)

        # Verify it's recent (within last minute)
        time_diff = datetime.utcnow() - created_expense.created_at
        assert time_diff.total_seconds() < 60
