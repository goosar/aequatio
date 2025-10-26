"""Tests for Expense domain entity.

This module tests the ExpenseEntity's business logic, validation,
and factory methods following DDD principles.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.domain.entities.expense import ExpenseCategory, ExpenseEntity


class TestExpenseEntityCreation:
    """Test cases for ExpenseEntity.create_expense_from_request() factory method."""

    def test_create_expense_with_valid_data(self):
        """Test successful expense creation with valid data."""
        user_id = uuid4()
        title = "Office Supplies"
        amount = 150.75
        currency = "USD"
        description = "Purchase of office supplies for Q1"
        category = ExpenseCategory.OTHER
        expensedate = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        vendor = "Office Depot"

        expense = ExpenseEntity.create_expense_from_request(
            fk_user_id=user_id,
            title=title,
            amount=amount,
            currency=currency,
            description=description,
            category=category,
            expensedate=expensedate,
            vendor=vendor,
        )

        assert expense.id is not None
        assert isinstance(expense.id, UUID)
        assert expense.fk_user_id == user_id
        assert expense.title == title
        assert expense.amount == amount
        assert expense.currency == currency
        assert expense.description == description
        assert expense.category == category
        assert expense.expensedate == expensedate
        assert expense.vendor == vendor
        assert isinstance(expense.created_at, datetime)
        assert expense.updated_at is None

    def test_create_expense_without_optional_fields(self):
        """Test expense creation without optional fields."""
        user_id = uuid4()
        expense = ExpenseEntity.create_expense_from_request(
            fk_user_id=user_id,
            title="Groceries",
            amount=50.0,
            currency="EUR",
            description=None,
            category=ExpenseCategory.LEBENSMITTEL,
            expensedate=datetime.now(timezone.utc),
            vendor=None,
        )

        assert expense.id is not None
        assert expense.fk_user_id == user_id
        assert expense.title == "Groceries"
        assert expense.amount == 50.0
        assert expense.description is None
        assert expense.vendor is None

    def test_create_expense_with_all_categories(self):
        """Test expense creation with all available categories."""
        user_id = uuid4()
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
                fk_user_id=user_id,
                title=f"Test {category.value}",
                amount=100.0,
                currency="USD",
                description=None,
                category=category,
                expensedate=datetime.now(timezone.utc),
                vendor=None,
            )
            assert expense.category == category


class TestExpenseEntityValidation:
    """Test cases for ExpenseEntity validation rules."""

    def test_amount_must_be_positive(self):
        """Test that amount must be greater than 0."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseEntity(
                fk_user_id=uuid4(),
                title="Test Expense",
                amount=0.0,  # Invalid: not positive
                currency="USD",
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("amount",) for error in errors)

    def test_amount_cannot_be_negative(self):
        """Test that amount cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseEntity(
                fk_user_id=uuid4(),
                title="Test Expense",
                amount=-50.0,  # Invalid: negative
                currency="USD",
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("amount",) for error in errors)

    def test_title_must_not_be_empty(self):
        """Test that title must have at least 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseEntity(
                fk_user_id=uuid4(),
                title="",  # Invalid: empty string
                amount=100.0,
                currency="USD",
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("title",) for error in errors)

    def test_title_max_length(self):
        """Test that title cannot exceed 100 characters."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseEntity(
                fk_user_id=uuid4(),
                title="A" * 101,  # Invalid: 101 characters
                amount=100.0,
                currency="USD",
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("title",) for error in errors)

    def test_currency_must_be_3_characters(self):
        """Test that currency must be exactly 3 characters."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseEntity(
                fk_user_id=uuid4(),
                title="Test Expense",
                amount=100.0,
                currency="US",  # Invalid: only 2 characters
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("currency",) for error in errors)

    def test_currency_must_be_uppercase(self):
        """Test that currency must match the pattern (uppercase)."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseEntity(
                fk_user_id=uuid4(),
                title="Test Expense",
                amount=100.0,
                currency="usd",  # Invalid: lowercase
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("currency",) for error in errors)

    def test_description_max_length(self):
        """Test that description cannot exceed 500 characters."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseEntity(
                fk_user_id=uuid4(),
                title="Test Expense",
                amount=100.0,
                currency="USD",
                description="A" * 501,  # Invalid: 501 characters
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("description",) for error in errors)

    def test_vendor_max_length(self):
        """Test that vendor cannot exceed 100 characters."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseEntity(
                fk_user_id=uuid4(),
                title="Test Expense",
                amount=100.0,
                currency="USD",
                vendor="A" * 101,  # Invalid: 101 characters
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("vendor",) for error in errors)

    def test_valid_currency_codes(self):
        """Test that valid currency codes are accepted."""
        user_id = uuid4()
        valid_currencies = ["USD", "EUR", "GBP", "JPY"]

        for currency in valid_currencies:
            expense = ExpenseEntity(
                fk_user_id=user_id,
                title="Test Expense",
                amount=100.0,
                currency=currency,
                category=ExpenseCategory.OTHER,
                expensedate=datetime.now(timezone.utc),
            )
            assert expense.currency == currency


class TestExpenseEntityEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_minimum_valid_amount(self):
        """Test minimum valid positive amount."""
        expense = ExpenseEntity(
            fk_user_id=uuid4(),
            title="Minimal Expense",
            amount=0.01,  # Smallest positive amount
            currency="USD",
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
        )
        assert expense.amount == 0.01

    def test_large_amount(self):
        """Test large expense amount."""
        expense = ExpenseEntity(
            fk_user_id=uuid4(),
            title="Large Expense",
            amount=999999.99,
            currency="USD",
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
        )
        assert expense.amount == 999999.99

    def test_title_minimum_length(self):
        """Test title with minimum valid length (1 character)."""
        expense = ExpenseEntity(
            fk_user_id=uuid4(),
            title="A",  # Minimum length
            amount=100.0,
            currency="USD",
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
        )
        assert expense.title == "A"

    def test_title_maximum_length(self):
        """Test title with maximum valid length (100 characters)."""
        long_title = "A" * 100
        expense = ExpenseEntity(
            fk_user_id=uuid4(),
            title=long_title,
            amount=100.0,
            currency="USD",
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
        )
        assert expense.title == long_title
        assert len(expense.title) == 100

    def test_description_maximum_length(self):
        """Test description with maximum valid length (500 characters)."""
        long_description = "A" * 500
        expense = ExpenseEntity(
            fk_user_id=uuid4(),
            title="Test",
            amount=100.0,
            currency="USD",
            description=long_description,
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
        )
        assert expense.description == long_description
        assert len(expense.description) == 500

    def test_vendor_maximum_length(self):
        """Test vendor with maximum valid length (100 characters)."""
        long_vendor = "A" * 100
        expense = ExpenseEntity(
            fk_user_id=uuid4(),
            title="Test",
            amount=100.0,
            currency="USD",
            vendor=long_vendor,
            category=ExpenseCategory.OTHER,
            expensedate=datetime.now(timezone.utc),
        )
        assert expense.vendor == long_vendor
        assert len(expense.vendor) == 100

    def test_expense_date_in_past(self):
        """Test expense with date in the past."""
        past_date = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        expense = ExpenseEntity(
            fk_user_id=uuid4(),
            title="Past Expense",
            amount=100.0,
            currency="USD",
            category=ExpenseCategory.OTHER,
            expensedate=past_date,
        )
        assert expense.expensedate == past_date

    def test_expense_date_in_future(self):
        """Test expense with date in the future."""
        future_date = datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        expense = ExpenseEntity(
            fk_user_id=uuid4(),
            title="Future Expense",
            amount=100.0,
            currency="USD",
            category=ExpenseCategory.OTHER,
            expensedate=future_date,
        )
        assert expense.expensedate == future_date
