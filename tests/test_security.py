"""Tests for security utilities module.

This module tests password hashing, verification, and validation
functionality in app.core.security.
"""

import pytest

from app.core.security import hash_password, validate_password_strength, verify_password


class TestHashPassword:
    """Test cases for password hashing."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "test_password123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)

    def test_hash_password_returns_bcrypt_hash(self):
        """Test that hash_password returns a bcrypt hash."""
        password = "test_password123"
        hashed = hash_password(password)
        # Bcrypt hashes start with $2b$ (or $2a$ or $2y$)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")

    def test_hash_password_different_each_time(self):
        """Test that hashing the same password produces different hashes (due to salt)."""
        password = "test_password123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_password_with_special_characters(self):
        """Test hashing passwords with special characters."""
        password = "P@ssw0rd!#$%"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_with_unicode(self):
        """Test hashing passwords with unicode characters."""
        password = "Пароль123!"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_empty_string(self):
        """Test hashing an empty string."""
        password = ""
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestVerifyPassword:
    """Test cases for password verification."""

    def test_verify_password_correct_password(self):
        """Test verification with correct password."""
        password = "correct_password123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test verification with incorrect password."""
        password = "correct_password123"
        wrong_password = "wrong_password123"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "Password123"
        hashed = hash_password(password)
        assert verify_password("password123", hashed) is False
        assert verify_password("PASSWORD123", hashed) is False

    def test_verify_password_with_special_characters(self):
        """Test verification with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_with_unicode(self):
        """Test verification with unicode characters."""
        password = "Пароль123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("Другой123!", hashed) is False

    def test_verify_password_empty_string(self):
        """Test verification with empty password."""
        password = ""
        hashed = hash_password(password)
        assert verify_password("", hashed) is True
        assert verify_password("anything", hashed) is False

    def test_verify_password_with_whitespace(self):
        """Test that whitespace matters in verification."""
        password = "password with spaces"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("passwordwithspaces", hashed) is False
        assert verify_password(" password with spaces ", hashed) is False


class TestValidatePasswordStrength:
    """Test cases for password strength validation."""

    def test_valid_password(self):
        """Test validation with a valid password."""
        password = "ValidP@ss123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True
        assert message == ""

    def test_password_too_short(self):
        """Test validation with password shorter than 8 characters."""
        password = "Pass1!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert message == "Password must be at least 8 characters long"

    def test_password_exactly_8_characters(self):
        """Test validation with password exactly 8 characters."""
        password = "Pass123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True
        assert message == ""

    def test_password_no_uppercase(self):
        """Test validation with password lacking uppercase letter."""
        password = "password123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert message == "Password must contain at least one uppercase letter"

    def test_password_no_lowercase(self):
        """Test validation with password lacking lowercase letter."""
        password = "PASSWORD123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert message == "Password must contain at least one lowercase letter"

    def test_password_no_digit(self):
        """Test validation with password lacking digit."""
        password = "Password!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert message == "Password must contain at least one digit"

    def test_password_no_special_character(self):
        """Test validation with password lacking special character."""
        password = "Password123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "Password must contain at least one special character" in message

    def test_password_with_various_special_characters(self):
        """Test validation with different special characters."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for char in special_chars:
            password = f"Password123{char}"
            is_valid, message = validate_password_strength(password)
            assert is_valid is True, f"Failed for special character: {char}"
            assert message == ""

    def test_password_very_long(self):
        """Test validation with very long password."""
        password = "ValidP@ss123" * 10
        is_valid, message = validate_password_strength(password)
        assert is_valid is True
        assert message == ""

    def test_password_with_unicode_uppercase(self):
        """Test validation with unicode characters (uppercase)."""
        password = "Пароль123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True
        assert message == ""

    def test_password_all_requirements_minimal(self):
        """Test minimal password meeting all requirements."""
        password = "Aa1!bcde"  # 8 chars, upper, lower, digit, special
        is_valid, message = validate_password_strength(password)
        assert is_valid is True
        assert message == ""

    def test_password_empty_string(self):
        """Test validation with empty string."""
        password = ""
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert message == "Password must be at least 8 characters long"

    def test_password_only_spaces(self):
        """Test validation with only spaces."""
        password = "        "
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        # Should fail due to no uppercase letter (first requirement check after length)
        assert "uppercase" in message.lower()


class TestPasswordWorkflow:
    """Integration tests for complete password workflows."""

    def test_hash_and_verify_workflow(self):
        """Test complete workflow of hashing and verifying a password."""
        original_password = "SecureP@ss123"

        # Hash the password
        hashed = hash_password(original_password)

        # Verify correct password
        assert verify_password(original_password, hashed) is True

        # Verify incorrect password
        assert verify_password("WrongP@ss123", hashed) is False

    def test_validate_then_hash_workflow(self):
        """Test workflow of validating before hashing."""
        password = "ValidP@ss123"

        # Validate password strength
        is_valid, message = validate_password_strength(password)
        assert is_valid is True

        # If valid, hash it
        if is_valid:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True

    def test_reject_weak_password_workflow(self):
        """Test workflow where weak password is rejected."""
        weak_password = "weak"

        # Validate password strength
        is_valid, message = validate_password_strength(weak_password)
        assert is_valid is False
        assert len(message) > 0

        # Weak password should not be hashed (in real application)
        # But technically we can still hash it - just shouldn't in practice

    @pytest.mark.parametrize(
        "password,expected_valid",
        [
            ("ValidP@ss123", True),
            ("Short1!", False),
            ("nouppercase123!", False),
            ("NOLOWERCASE123!", False),
            ("NoDigits!", False),
            ("NoSpecial123", False),
            ("Perfect1!", True),
            ("C0mpl3x!P@ssw0rd", True),
        ],
    )
    def test_multiple_passwords(self, password: str, expected_valid: bool):
        """Test validation with multiple password examples."""
        is_valid, _message = validate_password_strength(password)
        assert is_valid == expected_valid
