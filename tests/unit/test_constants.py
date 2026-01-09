"""Unit tests for gmail_assistant.core.constants module."""
from __future__ import annotations

from pathlib import Path

import pytest

from gmail_assistant.core.constants import (
    # Application Metadata
    APP_NAME,
    APP_VERSION,
    DEFAULT_CONFIG_DIR_NAME,
    DEFAULT_CONFIG_FILE_NAME,
    # Gmail API OAuth Scopes
    GMAIL_READONLY_SCOPE,
    GMAIL_MODIFY_SCOPE,
    SCOPES_READONLY,
    SCOPES_MODIFY,
    SCOPES_FULL,
    DEFAULT_SCOPES,
    # Default Paths
    PROJECT_ROOT,
    CONFIG_DIR,
    DEFAULT_CONFIG_PATH,
    AI_CONFIG_PATH,
    DATA_DIR,
    DEFAULT_DB_PATH,
    BACKUP_DIR,
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_TOKEN_PATH,
    CACHE_DIR,
    # API Rate Limits
    DEFAULT_RATE_LIMIT,
    DEFAULT_REQUESTS_PER_SECOND,
    CONSERVATIVE_REQUESTS_PER_SECOND,
    MAX_RATE_LIMIT,
    BATCH_SIZE,
    MAX_EMAILS_LIMIT,
    MAX_EMAILS_DEFAULT,
    DEFAULT_MAX_EMAILS,
    # Keyring Configuration
    KEYRING_SERVICE,
    KEYRING_USERNAME,
    # Logging Configuration
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
    # Output Formats
    SUPPORTED_OUTPUT_FORMATS,
    DEFAULT_OUTPUT_FORMAT,
    SUPPORTED_ORGANIZATION_TYPES,
    DEFAULT_ORGANIZATION,
)


@pytest.mark.unit
class TestApplicationMetadata:
    """Test application metadata constants."""

    def test_app_name_is_string(self):
        """APP_NAME should be a non-empty string."""
        assert isinstance(APP_NAME, str)
        assert len(APP_NAME) > 0

    def test_app_name_value(self):
        """APP_NAME should have expected value."""
        assert APP_NAME == "gmail-assistant"

    def test_app_version_format(self):
        """APP_VERSION should follow semantic versioning format."""
        assert isinstance(APP_VERSION, str)
        parts = APP_VERSION.split(".")
        assert len(parts) >= 2  # At least major.minor
        assert all(part.isdigit() for part in parts)

    def test_config_dir_name(self):
        """DEFAULT_CONFIG_DIR_NAME should start with dot."""
        assert DEFAULT_CONFIG_DIR_NAME.startswith(".")

    def test_config_file_name(self):
        """DEFAULT_CONFIG_FILE_NAME should be JSON."""
        assert DEFAULT_CONFIG_FILE_NAME.endswith(".json")


@pytest.mark.unit
class TestOAuthScopes:
    """Test OAuth scope constants."""

    def test_readonly_scope_is_valid_url(self):
        """GMAIL_READONLY_SCOPE should be a valid Google API URL."""
        assert isinstance(GMAIL_READONLY_SCOPE, str)
        assert GMAIL_READONLY_SCOPE.startswith("https://www.googleapis.com/auth/")
        assert "readonly" in GMAIL_READONLY_SCOPE

    def test_modify_scope_is_valid_url(self):
        """GMAIL_MODIFY_SCOPE should be a valid Google API URL."""
        assert isinstance(GMAIL_MODIFY_SCOPE, str)
        assert GMAIL_MODIFY_SCOPE.startswith("https://www.googleapis.com/auth/")
        assert "modify" in GMAIL_MODIFY_SCOPE

    def test_scopes_readonly_contains_readonly_scope(self):
        """SCOPES_READONLY should contain the readonly scope."""
        assert isinstance(SCOPES_READONLY, list)
        assert GMAIL_READONLY_SCOPE in SCOPES_READONLY

    def test_scopes_modify_contains_modify_scope(self):
        """SCOPES_MODIFY should contain the modify scope."""
        assert isinstance(SCOPES_MODIFY, list)
        assert GMAIL_MODIFY_SCOPE in SCOPES_MODIFY

    def test_scopes_full_is_list(self):
        """SCOPES_FULL should be a list."""
        assert isinstance(SCOPES_FULL, list)
        assert len(SCOPES_FULL) > 0

    def test_default_scopes_is_readonly(self):
        """DEFAULT_SCOPES should default to readonly."""
        assert DEFAULT_SCOPES == SCOPES_READONLY


@pytest.mark.unit
class TestDefaultPaths:
    """Test default path constants."""

    def test_project_root_is_path(self):
        """PROJECT_ROOT should be a Path object."""
        assert isinstance(PROJECT_ROOT, Path)

    def test_config_dir_is_path(self):
        """CONFIG_DIR should be a Path object."""
        assert isinstance(CONFIG_DIR, Path)

    def test_data_dir_is_path(self):
        """DATA_DIR should be a Path object."""
        assert isinstance(DATA_DIR, Path)

    def test_backup_dir_is_path(self):
        """BACKUP_DIR should be a Path object."""
        assert isinstance(BACKUP_DIR, Path)

    def test_cache_dir_in_home(self):
        """CACHE_DIR should be under home directory."""
        assert isinstance(CACHE_DIR, Path)
        assert CACHE_DIR.is_relative_to(Path.home())

    def test_default_config_path_is_json(self):
        """DEFAULT_CONFIG_PATH should be a JSON file."""
        assert isinstance(DEFAULT_CONFIG_PATH, Path)
        assert DEFAULT_CONFIG_PATH.suffix == ".json"

    def test_ai_config_path_is_json(self):
        """AI_CONFIG_PATH should be a JSON file."""
        assert isinstance(AI_CONFIG_PATH, Path)
        assert AI_CONFIG_PATH.suffix == ".json"

    def test_default_db_path_is_sqlite(self):
        """DEFAULT_DB_PATH should be a SQLite file."""
        assert isinstance(DEFAULT_DB_PATH, Path)
        assert DEFAULT_DB_PATH.suffix == ".db"

    def test_default_credentials_path_is_json(self):
        """DEFAULT_CREDENTIALS_PATH should be a JSON filename."""
        assert isinstance(DEFAULT_CREDENTIALS_PATH, str)
        assert DEFAULT_CREDENTIALS_PATH.endswith(".json")

    def test_default_token_path_is_json(self):
        """DEFAULT_TOKEN_PATH should be a JSON filename."""
        assert isinstance(DEFAULT_TOKEN_PATH, str)
        assert DEFAULT_TOKEN_PATH.endswith(".json")


@pytest.mark.unit
class TestRateLimits:
    """Test rate limit constants."""

    def test_default_rate_limit_is_positive(self):
        """DEFAULT_RATE_LIMIT should be a positive number."""
        assert isinstance(DEFAULT_RATE_LIMIT, (int, float))
        assert DEFAULT_RATE_LIMIT > 0

    def test_requests_per_second_alias(self):
        """DEFAULT_REQUESTS_PER_SECOND should equal DEFAULT_RATE_LIMIT."""
        assert DEFAULT_REQUESTS_PER_SECOND == DEFAULT_RATE_LIMIT

    def test_conservative_rate_is_less_than_default(self):
        """CONSERVATIVE_REQUESTS_PER_SECOND should be less than default."""
        assert CONSERVATIVE_REQUESTS_PER_SECOND < DEFAULT_RATE_LIMIT

    def test_conservative_rate_is_positive(self):
        """CONSERVATIVE_REQUESTS_PER_SECOND should be positive."""
        assert CONSERVATIVE_REQUESTS_PER_SECOND > 0

    def test_max_rate_limit_exceeds_default(self):
        """MAX_RATE_LIMIT should be greater than default."""
        assert MAX_RATE_LIMIT > DEFAULT_RATE_LIMIT

    def test_batch_size_is_positive_integer(self):
        """BATCH_SIZE should be a positive integer."""
        assert isinstance(BATCH_SIZE, int)
        assert BATCH_SIZE > 0

    def test_max_emails_limit_is_reasonable(self):
        """MAX_EMAILS_LIMIT should be a large but reasonable number."""
        assert isinstance(MAX_EMAILS_LIMIT, int)
        assert MAX_EMAILS_LIMIT > 0
        assert MAX_EMAILS_LIMIT <= 1000000  # Not unreasonably large

    def test_max_emails_default_within_limit(self):
        """MAX_EMAILS_DEFAULT should be within MAX_EMAILS_LIMIT."""
        assert MAX_EMAILS_DEFAULT <= MAX_EMAILS_LIMIT
        assert MAX_EMAILS_DEFAULT > 0

    def test_default_max_emails_alias(self):
        """DEFAULT_MAX_EMAILS should equal MAX_EMAILS_DEFAULT."""
        assert DEFAULT_MAX_EMAILS == MAX_EMAILS_DEFAULT


@pytest.mark.unit
class TestKeyringConfiguration:
    """Test keyring configuration constants."""

    def test_keyring_service_is_string(self):
        """KEYRING_SERVICE should be a non-empty string."""
        assert isinstance(KEYRING_SERVICE, str)
        assert len(KEYRING_SERVICE) > 0

    def test_keyring_username_is_string(self):
        """KEYRING_USERNAME should be a non-empty string."""
        assert isinstance(KEYRING_USERNAME, str)
        assert len(KEYRING_USERNAME) > 0


@pytest.mark.unit
class TestLoggingConfiguration:
    """Test logging configuration constants."""

    def test_log_format_contains_placeholders(self):
        """DEFAULT_LOG_FORMAT should contain log format placeholders."""
        assert isinstance(DEFAULT_LOG_FORMAT, str)
        assert "%(asctime)s" in DEFAULT_LOG_FORMAT
        assert "%(levelname)s" in DEFAULT_LOG_FORMAT

    def test_log_level_is_valid(self):
        """DEFAULT_LOG_LEVEL should be a valid Python log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert DEFAULT_LOG_LEVEL in valid_levels


@pytest.mark.unit
class TestOutputFormats:
    """Test output format constants."""

    def test_supported_output_formats_is_list(self):
        """SUPPORTED_OUTPUT_FORMATS should be a non-empty list."""
        assert isinstance(SUPPORTED_OUTPUT_FORMATS, list)
        assert len(SUPPORTED_OUTPUT_FORMATS) > 0

    def test_supported_formats_contains_eml(self):
        """SUPPORTED_OUTPUT_FORMATS should contain 'eml'."""
        assert "eml" in SUPPORTED_OUTPUT_FORMATS

    def test_supported_formats_contains_markdown(self):
        """SUPPORTED_OUTPUT_FORMATS should contain 'markdown'."""
        assert "markdown" in SUPPORTED_OUTPUT_FORMATS

    def test_supported_formats_contains_both(self):
        """SUPPORTED_OUTPUT_FORMATS should contain 'both'."""
        assert "both" in SUPPORTED_OUTPUT_FORMATS

    def test_default_output_format_is_supported(self):
        """DEFAULT_OUTPUT_FORMAT should be a supported format."""
        assert DEFAULT_OUTPUT_FORMAT in SUPPORTED_OUTPUT_FORMATS

    def test_supported_organization_types_is_list(self):
        """SUPPORTED_ORGANIZATION_TYPES should be a non-empty list."""
        assert isinstance(SUPPORTED_ORGANIZATION_TYPES, list)
        assert len(SUPPORTED_ORGANIZATION_TYPES) > 0

    def test_supported_organization_contains_date(self):
        """SUPPORTED_ORGANIZATION_TYPES should contain 'date'."""
        assert "date" in SUPPORTED_ORGANIZATION_TYPES

    def test_supported_organization_contains_sender(self):
        """SUPPORTED_ORGANIZATION_TYPES should contain 'sender'."""
        assert "sender" in SUPPORTED_ORGANIZATION_TYPES

    def test_supported_organization_contains_none(self):
        """SUPPORTED_ORGANIZATION_TYPES should contain 'none'."""
        assert "none" in SUPPORTED_ORGANIZATION_TYPES

    def test_default_organization_is_supported(self):
        """DEFAULT_ORGANIZATION should be a supported organization type."""
        assert DEFAULT_ORGANIZATION in SUPPORTED_ORGANIZATION_TYPES
