"""Unit tests for gmail_assistant.utils.input_validator module."""
from __future__ import annotations

from pathlib import Path

import pytest

from gmail_assistant.utils.input_validator import (
    ValidationError,
    InputValidator,
)


@pytest.mark.unit
class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_is_exception(self):
        """ValidationError should inherit from Exception."""
        assert issubclass(ValidationError, Exception)

    def test_validation_error_with_message(self):
        """ValidationError should preserve message."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"


@pytest.mark.unit
class TestValidateGmailQuery:
    """Test validate_gmail_query method."""

    def test_valid_simple_query(self):
        """Should accept simple search queries."""
        result = InputValidator.validate_gmail_query("is:unread")
        assert result == "is:unread"

    def test_valid_complex_query(self):
        """Should accept complex search queries."""
        query = 'from:example.com subject:"Test" after:2024/01/01'
        result = InputValidator.validate_gmail_query(query)
        assert "from:example.com" in result
        assert "subject:" in result

    def test_query_with_multiple_operators(self):
        """Should accept queries with multiple operators."""
        query = "from:test@example.com to:user@example.com has:attachment"
        result = InputValidator.validate_gmail_query(query)
        assert result == query

    def test_removes_excessive_whitespace(self):
        """Should normalize whitespace in queries."""
        query = "is:unread     from:test@example.com"
        result = InputValidator.validate_gmail_query(query)
        assert "  " not in result

    def test_empty_query_raises_error(self):
        """Should raise ValidationError for empty query."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_gmail_query("")

    def test_whitespace_only_query_raises_error(self):
        """Should raise ValidationError for whitespace-only query."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_gmail_query("   ")

    def test_non_string_query_raises_error(self):
        """Should raise ValidationError for non-string query."""
        with pytest.raises(ValidationError, match="must be a string"):
            InputValidator.validate_gmail_query(123)

    def test_query_too_long_raises_error(self):
        """Should raise ValidationError for query over 1000 chars."""
        long_query = "is:unread " * 200
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_gmail_query(long_query)

    def test_rejects_script_injection(self):
        """Should reject queries with script tags."""
        with pytest.raises(ValidationError, match="dangerous"):
            InputValidator.validate_gmail_query("<script>alert('xss')</script>")

    def test_rejects_javascript_protocol(self):
        """Should reject queries with javascript: protocol."""
        with pytest.raises(ValidationError, match="dangerous"):
            InputValidator.validate_gmail_query("javascript:alert(1)")


@pytest.mark.unit
class TestValidateFilePath:
    """Test validate_file_path method."""

    def test_valid_relative_path(self):
        """Should accept valid relative paths."""
        path = Path("test_folder") / "test.txt"
        result = InputValidator.validate_file_path(path)
        assert result == path

    def test_accepts_string_relative_path(self):
        """Should accept string paths and return Path object."""
        path_str = "test_folder/test.txt"
        result = InputValidator.validate_file_path(path_str)
        assert isinstance(result, Path)

    def test_path_too_long_raises_error(self):
        """Should raise ValidationError for paths over 260 chars."""
        long_path = "a" * 300

        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_file_path(long_path)

    def test_non_path_type_raises_error(self):
        """Should raise ValidationError for non-string/Path input."""
        with pytest.raises(ValidationError, match="must be a string or Path"):
            InputValidator.validate_file_path(123)

    def test_path_traversal_blocked(self):
        """Should reject paths with path traversal attempts."""
        with pytest.raises(ValidationError, match="dangerous"):
            InputValidator.validate_file_path("../../../etc/passwd")

    def test_relative_path_with_subdirectory(self):
        """Should accept relative paths with subdirectories."""
        path = Path("output") / "emails" / "2024" / "email.eml"
        result = InputValidator.validate_file_path(path)
        assert result.name == "email.eml"


@pytest.mark.unit
class TestValidateEmailAddress:
    """Test validate_email_address method."""

    def test_valid_email(self):
        """Should accept valid email addresses."""
        result = InputValidator.validate_email_address("user@example.com")
        assert result == "user@example.com"

    def test_email_normalized_lowercase(self):
        """Should normalize email to lowercase."""
        result = InputValidator.validate_email_address("User@Example.COM")
        assert result == "user@example.com"

    def test_email_trimmed(self):
        """Should trim whitespace from email."""
        result = InputValidator.validate_email_address("  user@example.com  ")
        assert result == "user@example.com"

    def test_empty_email_raises_error(self):
        """Should raise ValidationError for empty email."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_email_address("")

    def test_non_string_email_raises_error(self):
        """Should raise ValidationError for non-string email."""
        with pytest.raises(ValidationError, match="must be a string"):
            InputValidator.validate_email_address(123)

    def test_email_too_long_raises_error(self):
        """Should raise ValidationError for email over 254 chars."""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_email_address(long_email)

    def test_invalid_email_format_raises_error(self):
        """Should raise ValidationError for invalid email format."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user@example",
            "user name@example.com",
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError, match="Invalid email"):
                InputValidator.validate_email_address(email)


@pytest.mark.unit
class TestValidateInteger:
    """Test validate_integer method."""

    def test_valid_integer(self):
        """Should accept valid integers."""
        result = InputValidator.validate_integer(42)
        assert result == 42

    def test_string_integer_converted(self):
        """Should convert string integers."""
        result = InputValidator.validate_integer("42")
        assert result == 42

    def test_min_value_validation(self):
        """Should raise ValidationError when below minimum."""
        with pytest.raises(ValidationError, match="below minimum"):
            InputValidator.validate_integer(5, min_val=10)

    def test_max_value_validation(self):
        """Should raise ValidationError when above maximum."""
        with pytest.raises(ValidationError, match="above maximum"):
            InputValidator.validate_integer(100, max_val=50)

    def test_within_range(self):
        """Should accept values within min/max range."""
        result = InputValidator.validate_integer(25, min_val=10, max_val=50)
        assert result == 25

    def test_non_numeric_string_raises_error(self):
        """Should raise ValidationError for non-numeric strings."""
        with pytest.raises(ValidationError, match="Invalid integer"):
            InputValidator.validate_integer("not a number")

    def test_float_raises_error(self):
        """Should raise ValidationError for float values."""
        with pytest.raises(ValidationError, match="Invalid integer"):
            InputValidator.validate_integer(3.14)


@pytest.mark.unit
class TestValidateString:
    """Test validate_string method."""

    def test_valid_string(self):
        """Should accept valid strings."""
        result = InputValidator.validate_string("hello")
        assert result == "hello"

    def test_min_length_validation(self):
        """Should raise ValidationError when below minimum length."""
        with pytest.raises(ValidationError, match="too short"):
            InputValidator.validate_string("hi", min_length=5)

    def test_max_length_validation(self):
        """Should raise ValidationError when above maximum length."""
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_string("hello world", max_length=5)

    def test_non_string_raises_error(self):
        """Should raise ValidationError for non-string values."""
        with pytest.raises(ValidationError, match="must be a string"):
            InputValidator.validate_string(123)

    def test_allowed_chars_validation(self):
        """Should raise ValidationError for disallowed characters."""
        with pytest.raises(ValidationError, match="invalid characters"):
            InputValidator.validate_string("abc123!", allowed_chars=r"^[a-z]+$")

    def test_allowed_chars_accepted(self):
        """Should accept strings matching allowed pattern."""
        result = InputValidator.validate_string("hello", allowed_chars=r"^[a-z]+$")
        assert result == "hello"


@pytest.mark.unit
class TestValidateDateString:
    """Test validate_date_string method."""

    def test_valid_yyyy_mm_dd_slash(self):
        """Should accept YYYY/MM/DD format."""
        result = InputValidator.validate_date_string("2024/01/15")
        assert result == "2024/01/15"

    def test_valid_yyyy_mm_dd_dash(self):
        """Should accept YYYY-MM-DD format."""
        result = InputValidator.validate_date_string("2024-01-15")
        assert result == "2024-01-15"

    def test_valid_mm_dd_yyyy(self):
        """Should accept MM/DD/YYYY format."""
        result = InputValidator.validate_date_string("1/15/2024")
        assert result == "1/15/2024"

    def test_valid_relative_days(self):
        """Should accept relative day formats."""
        valid_dates = ["7d", "14d", "30days"]
        for date_str in valid_dates:
            result = InputValidator.validate_date_string(date_str)
            assert result == date_str

    def test_valid_relative_weeks(self):
        """Should accept relative week formats."""
        result = InputValidator.validate_date_string("2w")
        assert result == "2w"

    def test_valid_relative_months(self):
        """Should accept relative month formats."""
        result = InputValidator.validate_date_string("3m")
        assert result == "3m"

    def test_empty_date_raises_error(self):
        """Should raise ValidationError for empty date."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_date_string("")

    def test_non_string_date_raises_error(self):
        """Should raise ValidationError for non-string date."""
        with pytest.raises(ValidationError, match="must be a string"):
            InputValidator.validate_date_string(20240115)

    def test_invalid_format_raises_error(self):
        """Should raise ValidationError for invalid date format."""
        with pytest.raises(ValidationError, match="Invalid date"):
            InputValidator.validate_date_string("not-a-date")


@pytest.mark.unit
class TestSanitizeFilename:
    """Test sanitize_filename method."""

    def test_valid_filename_unchanged(self):
        """Should not modify valid filenames."""
        result = InputValidator.sanitize_filename("valid_filename.txt")
        assert result == "valid_filename.txt"

    def test_removes_dangerous_characters(self):
        """Should remove/replace dangerous characters."""
        result = InputValidator.sanitize_filename('file<>:"/\\|?*.txt')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_truncates_long_filenames(self):
        """Should truncate filenames exceeding max length."""
        long_name = "a" * 250 + ".txt"
        result = InputValidator.sanitize_filename(long_name, max_length=100)
        assert len(result) <= 100

    def test_preserves_extension_when_truncating(self):
        """Should preserve file extension when truncating."""
        long_name = "a" * 250 + ".txt"
        result = InputValidator.sanitize_filename(long_name, max_length=100)
        assert result.endswith(".txt")

    def test_empty_filename_raises_error(self):
        """Should raise ValidationError for empty filename."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.sanitize_filename("")

    def test_non_string_filename_raises_error(self):
        """Should raise ValidationError for non-string filename."""
        with pytest.raises(ValidationError, match="must be a string"):
            InputValidator.sanitize_filename(123)

    def test_filename_becomes_empty_raises_error(self):
        """Should raise ValidationError if sanitization produces empty string."""
        with pytest.raises(ValidationError, match="empty after sanitization"):
            InputValidator.sanitize_filename("...")


@pytest.mark.unit
class TestValidateBatchSize:
    """Test validate_batch_size method."""

    def test_valid_batch_size(self):
        """Should accept valid batch size."""
        result = InputValidator.validate_batch_size(100)
        assert result == 100

    def test_batch_size_at_minimum(self):
        """Should accept batch size of 1."""
        result = InputValidator.validate_batch_size(1)
        assert result == 1

    def test_batch_size_at_maximum(self):
        """Should accept batch size at max_allowed."""
        result = InputValidator.validate_batch_size(1000, max_allowed=1000)
        assert result == 1000

    def test_batch_size_zero_raises_error(self):
        """Should raise ValidationError for batch size of 0."""
        with pytest.raises(ValidationError):
            InputValidator.validate_batch_size(0)

    def test_batch_size_negative_raises_error(self):
        """Should raise ValidationError for negative batch size."""
        with pytest.raises(ValidationError):
            InputValidator.validate_batch_size(-1)

    def test_batch_size_exceeds_max_raises_error(self):
        """Should raise ValidationError when exceeding max_allowed."""
        with pytest.raises(ValidationError):
            InputValidator.validate_batch_size(2000, max_allowed=1000)


@pytest.mark.unit
class TestValidateConfigDict:
    """Test validate_config_dict method."""

    def test_valid_config_with_required_keys(self):
        """Should accept config with all required keys."""
        config = {"key1": "value1", "key2": "value2"}
        result = InputValidator.validate_config_dict(config, ["key1", "key2"])
        assert result == config

    def test_missing_required_key_raises_error(self):
        """Should raise ValidationError for missing required keys."""
        config = {"key1": "value1"}
        with pytest.raises(ValidationError, match="Missing required"):
            InputValidator.validate_config_dict(config, ["key1", "key2"])

    def test_non_dict_config_raises_error(self):
        """Should raise ValidationError for non-dict config."""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            InputValidator.validate_config_dict("not a dict", ["key1"])

    def test_extra_keys_allowed(self):
        """Should allow extra keys beyond required."""
        config = {"key1": "value1", "key2": "value2", "extra": "value"}
        result = InputValidator.validate_config_dict(config, ["key1"])
        assert result == config

    def test_empty_required_keys_accepts_any_dict(self):
        """Should accept any dict when no required keys specified."""
        config = {"any": "value"}
        result = InputValidator.validate_config_dict(config, [])
        assert result == config


@pytest.mark.unit
class TestGmailSearchOperators:
    """Test Gmail search operators constant."""

    def test_contains_common_operators(self):
        """Should contain common Gmail search operators."""
        expected_operators = {
            "from", "to", "subject", "has", "is", "in", "category",
            "before", "after", "label"
        }

        assert expected_operators.issubset(InputValidator.GMAIL_SEARCH_OPERATORS)


@pytest.mark.unit
class TestEmailPattern:
    """Test email validation pattern."""

    def test_pattern_accepts_valid_emails(self):
        """Email pattern should match valid emails."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@subdomain.example.com",
        ]

        for email in valid_emails:
            assert InputValidator.EMAIL_PATTERN.match(email) is not None

    def test_pattern_rejects_invalid_emails(self):
        """Email pattern should reject invalid emails."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@example",
        ]

        for email in invalid_emails:
            assert InputValidator.EMAIL_PATTERN.match(email) is None
