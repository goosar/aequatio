"""Tests for Expense repository.

This module tests the SQLAlchemyExpenseRepository for persistence operations.
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.domain.entities.expense import ExpenseCategory, ExpenseEntity
from app.persistence.models.expense import SQLAlchemyExpense
from app.persistence.models.user import User as UserModel
from app.persistence.repositories.expense_repository import SQLAlchemyExpenseRepository


class TestExpenseRepositorySave:
    """Test cases for saving expenses."""

    def test_save_expense_successfully(self, db):
        """Test saving a new expense to the database."""
        # Create a test user first (required for foreign key)
        user = UserModel(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Create expense entity
        expense = ExpenseEntity.create_expense_from_request(
            fk_user_id=user.id,
            title="Test Expense",
            amount=100.50,
            currency="USD",
            description="Test description",
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
            vendor="Test Vendor",
        )

        # Save expense
        repo = SQLAlchemyExpenseRepository(db)
        saved_expense = repo.save(expense)

        # Verify returned expense
        assert saved_expense.id == expense.id
        assert saved_expense.fk_user_id == user.id
        assert saved_expense.title == "Test Expense"
        assert saved_expense.amount == 100.50
        assert saved_expense.currency == "USD"

        # Verify expense is in database
        db_expense = db.query(SQLAlchemyExpense).filter_by(id=expense.id).first()
        assert db_expense is not None
        assert db_expense.title == "Test Expense"
        assert db_expense.amount == 100.50

    def test_save_expense_without_optional_fields(self, db):
        """Test saving an expense without optional fields."""
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

        # Create expense without optional fields
        expense = ExpenseEntity.create_expense_from_request(
            fk_user_id=user.id,
            title="Minimal Expense",
            amount=50.0,
            currency="EUR",
            description=None,
            category=ExpenseCategory.LEBENSMITTEL,
            expensedate=datetime.now(timezone.utc),
            vendor=None,
        )

        # Save expense
        repo = SQLAlchemyExpenseRepository(db)
        saved_expense = repo.save(expense)

        # Verify
        assert saved_expense.description is None
        assert saved_expense.vendor is None

        # Verify in database
        db_expense = db.query(SQLAlchemyExpense).filter_by(id=expense.id).first()
        assert db_expense is not None
        assert db_expense.description is None
        assert db_expense.vendor is None

    def test_save_multiple_expenses(self, db):
        """Test saving multiple expenses for the same user."""
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

        repo = SQLAlchemyExpenseRepository(db)

        # Create and save multiple expenses
        expenses = []
        for i in range(3):
            expense = ExpenseEntity.create_expense_from_request(
                fk_user_id=user.id,
                title=f"Expense {i + 1}",
                amount=100.0 * (i + 1),
                currency="USD",
                description=None,
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
                vendor=None,
            )
            saved_expense = repo.save(expense)
            expenses.append(saved_expense)

        # Verify all expenses are saved
        assert len(expenses) == 3
        db_expenses = db.query(SQLAlchemyExpense).filter_by(fk_user_id=user.id).all()
        assert len(db_expenses) == 3

    def test_save_expense_all_categories(self, db):
        """Test saving expenses with all available categories."""
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

        repo = SQLAlchemyExpenseRepository(db)
        categories = [
            ExpenseCategory.LEBENSMITTEL,
            ExpenseCategory.LIEFERSERVICE,
            ExpenseCategory.DROGERIEARTIKEL,
            ExpenseCategory.URLAUB,
            ExpenseCategory.KLEIDUNG,
            ExpenseCategory.OTHER,
        ]

        for category in categories:
            expense = ExpenseEntity.create_expense_from_request(
                fk_user_id=user.id,
                title=f"Test {category.value}",
                amount=100.0,
                currency="EUR",
                description=None,
                category=category,
                expensedate=datetime.now(timezone.utc),
                vendor=None,
            )
            saved_expense = repo.save(expense)
            assert saved_expense.category == category

            # Verify in database
            db_expense = db.query(SQLAlchemyExpense).filter_by(id=expense.id).first()
            assert db_expense.category == category


class TestExpenseRepositoryGetById:
    """Test cases for retrieving expenses by ID."""

    def test_get_by_id_existing_expense(self, db):
        """Test retrieving an existing expense by ID."""
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

        # Create and save expense
        expense = ExpenseEntity.create_expense_from_request(
            fk_user_id=user.id,
            title="Test Expense",
            amount=100.0,
            currency="USD",
            description="Test description",
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
            vendor="Test Vendor",
        )

        repo = SQLAlchemyExpenseRepository(db)
        saved_expense = repo.save(expense)

        # Retrieve expense
        retrieved_expense = repo.get_by_id(saved_expense.id)

        # Verify
        assert retrieved_expense is not None
        assert retrieved_expense.id == saved_expense.id
        assert retrieved_expense.title == "Test Expense"
        assert retrieved_expense.amount == 100.0
        assert retrieved_expense.currency == "USD"
        assert retrieved_expense.description == "Test description"
        assert retrieved_expense.vendor == "Test Vendor"
        assert retrieved_expense.category == ExpenseCategory.OTHER

    def test_get_by_id_nonexistent_expense(self, db):
        """Test retrieving a nonexistent expense returns None."""
        repo = SQLAlchemyExpenseRepository(db)
        nonexistent_id = uuid4()

        retrieved_expense = repo.get_by_id(nonexistent_id)

        assert retrieved_expense is None

    def test_get_by_id_with_all_fields(self, db):
        """Test retrieving expense with all fields populated."""
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

        # Create expense with all fields
        expense = ExpenseEntity.create_expense_from_request(
            fk_user_id=user.id,
            title="Complete Expense",
            amount=250.75,
            currency="EUR",
            description="Full description with all details",
            category=ExpenseCategory.URLAUB,
            expensedate=datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc),
            vendor="Travel Agency",
        )

        repo = SQLAlchemyExpenseRepository(db)
        saved_expense = repo.save(expense)

        # Retrieve and verify
        retrieved_expense = repo.get_by_id(saved_expense.id)

        assert retrieved_expense is not None
        assert retrieved_expense.id == saved_expense.id
        assert retrieved_expense.fk_user_id == user.id
        assert retrieved_expense.title == "Complete Expense"
        assert retrieved_expense.amount == 250.75
        assert retrieved_expense.currency == "EUR"
        assert retrieved_expense.description == "Full description with all details"
        assert retrieved_expense.category == ExpenseCategory.URLAUB
        assert retrieved_expense.vendor == "Travel Agency"
        assert isinstance(retrieved_expense.created_at, datetime)


class TestExpenseRepositoryConversion:
    """Test cases for ORM conversion methods."""

    def test_to_orm_conversion(self, db):
        """Test converting domain entity to ORM model."""
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

        expense = ExpenseEntity.create_expense_from_request(
            fk_user_id=user.id,
            title="Test Expense",
            amount=100.0,
            currency="USD",
            description="Test",
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
            vendor="Vendor",
        )

        repo = SQLAlchemyExpenseRepository(db)
        orm_expense = repo._to_orm(expense)

        assert isinstance(orm_expense, SQLAlchemyExpense)
        assert orm_expense.fk_user_id == expense.fk_user_id
        assert orm_expense.title == expense.title
        assert orm_expense.amount == expense.amount
        assert orm_expense.currency == expense.currency
        assert orm_expense.description == expense.description
        assert orm_expense.category == expense.category
        assert orm_expense.vendor == expense.vendor

    def test_from_orm_conversion(self, db):
        """Test converting ORM model to domain entity."""
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

        # Create ORM model directly
        expense_id = uuid4()
        orm_expense = SQLAlchemyExpense(
            id=expense_id,
            fk_user_id=user.id,
            title="ORM Expense",
            amount=150.0,
            currency="GBP",
            description="ORM description",
            category=ExpenseCategory.KLEIDUNG,
            expensedate=datetime.now(timezone.utc),
            vendor="ORM Vendor",
        )
        db.add(orm_expense)
        db.flush()

        repo = SQLAlchemyExpenseRepository(db)
        domain_expense = repo._from_orm(orm_expense)

        assert isinstance(domain_expense, ExpenseEntity)
        assert domain_expense.id == expense_id
        assert domain_expense.fk_user_id == user.id
        assert domain_expense.title == "ORM Expense"
        assert domain_expense.amount == 150.0
        assert domain_expense.currency == "GBP"
        assert domain_expense.description == "ORM description"
        assert domain_expense.category == ExpenseCategory.KLEIDUNG
        assert domain_expense.vendor == "ORM Vendor"

    def test_roundtrip_conversion(self, db):
        """Test converting entity to ORM and back preserves data."""
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

        original_expense = ExpenseEntity.create_expense_from_request(
            fk_user_id=user.id,
            title="Roundtrip Test",
            amount=99.99,
            currency="JPY",
            description="Testing roundtrip",
            category=ExpenseCategory.LIEFERSERVICE,
            expensedate=datetime.now(timezone.utc),
            vendor="Roundtrip Vendor",
        )

        repo = SQLAlchemyExpenseRepository(db)

        # Convert to ORM and save
        orm_expense = repo._to_orm(original_expense)
        db.add(orm_expense)
        db.flush()

        # Convert back to domain entity
        converted_expense = repo._from_orm(orm_expense)

        # Verify data is preserved
        assert converted_expense.fk_user_id == original_expense.fk_user_id
        assert converted_expense.title == original_expense.title
        assert converted_expense.amount == original_expense.amount
        assert converted_expense.currency == original_expense.currency
        assert converted_expense.description == original_expense.description
        assert converted_expense.category == original_expense.category
        assert converted_expense.vendor == original_expense.vendor
