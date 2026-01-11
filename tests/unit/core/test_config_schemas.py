"""
Comprehensive tests for config_schemas.py module.
Tests Pydantic models for configuration validation.
"""

import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from pydantic import ValidationError

from gmail_assistant.core.config_schemas import (
    AIKeywordsConfig,
    AnalysisConfig,
    AppConfig,
    DatabaseConfig,
    DeletionConfig,
    GmailAssistantConfig,
    RateLimitConfig,
    generate_json_schema,
    load_config_safe,
    load_validated_config,
    validate_all_configs,
)


class TestAIKeywordsConfig:
    """Tests for AIKeywordsConfig model."""

    def test_default_values(self):
        """AIKeywordsConfig should have proper default values."""
        config = AIKeywordsConfig()

        assert config.ai_keywords == []
        assert config.ai_newsletter_domains == []
        assert config.newsletter_patterns == []
        assert config.unsubscribe_patterns == []
        assert config.confidence_weights == {}
        assert config.decision_threshold == {}

    def test_create_with_values(self):
        """AIKeywordsConfig should accept custom values."""
        config = AIKeywordsConfig(
            ai_keywords=["AI", "GPT", "LLM"],
            ai_newsletter_domains=["example.com"],
            newsletter_patterns=["newsletter.*"],
            unsubscribe_patterns=["unsubscribe"],
            confidence_weights={"ai_keywords_subject": 3},
            decision_threshold={"minimum_confidence": 5}
        )

        assert len(config.ai_keywords) == 3
        assert "AI" in config.ai_keywords
        assert config.ai_newsletter_domains == ["example.com"]

    def test_validate_weights_adds_missing_keys(self):
        """Validator should add missing confidence weight keys."""
        config = AIKeywordsConfig(
            confidence_weights={}
        )

        # Validator should add required keys with defaults
        assert "ai_keywords_subject" in config.confidence_weights
        assert "ai_keywords_sender" in config.confidence_weights
        assert "known_domain" in config.confidence_weights

    def test_validate_weights_preserves_existing_keys(self):
        """Validator should preserve existing weight values."""
        config = AIKeywordsConfig(
            confidence_weights={
                "ai_keywords_subject": 10,
                "ai_keywords_sender": 5,
                "known_domain": 8,
                "custom_key": 3
            }
        )

        assert config.confidence_weights["ai_keywords_subject"] == 10
        assert config.confidence_weights["ai_keywords_sender"] == 5
        assert config.confidence_weights["known_domain"] == 8
        assert config.confidence_weights["custom_key"] == 3

    def test_validate_threshold_adds_missing_keys(self):
        """Validator should add missing threshold keys."""
        config = AIKeywordsConfig(
            decision_threshold={}
        )

        assert "minimum_confidence" in config.decision_threshold
        assert "minimum_reasons" in config.decision_threshold
        assert config.decision_threshold["minimum_confidence"] == 4
        assert config.decision_threshold["minimum_reasons"] == 2

    def test_validate_threshold_preserves_existing_keys(self):
        """Validator should preserve existing threshold values."""
        config = AIKeywordsConfig(
            decision_threshold={
                "minimum_confidence": 10,
                "minimum_reasons": 5,
                "custom_threshold": 3
            }
        )

        assert config.decision_threshold["minimum_confidence"] == 10
        assert config.decision_threshold["minimum_reasons"] == 5
        assert config.decision_threshold["custom_threshold"] == 3

    def test_serialization(self):
        """AIKeywordsConfig should serialize to dict."""
        config = AIKeywordsConfig(
            ai_keywords=["AI", "GPT"],
            confidence_weights={"ai_keywords_subject": 3}
        )

        data = config.model_dump()

        assert isinstance(data, dict)
        assert "ai_keywords" in data
        assert data["ai_keywords"] == ["AI", "GPT"]


class TestGmailAssistantConfig:
    """Tests for GmailAssistantConfig model."""

    def test_default_values(self):
        """GmailAssistantConfig should have proper defaults."""
        config = GmailAssistantConfig()

        assert config.default_max_emails == 100
        assert config.default_format == "both"
        assert config.default_organize_by == "date"
        assert config.output_directory == "gmail_backup"
        assert config.predefined_queries == {}

    def test_create_with_custom_values(self):
        """GmailAssistantConfig should accept custom values."""
        config = GmailAssistantConfig(
            default_max_emails=500,
            default_format="markdown",
            default_organize_by="sender",
            output_directory="custom_backup",
            predefined_queries={"unread": "is:unread"}
        )

        assert config.default_max_emails == 500
        assert config.default_format == "markdown"
        assert config.default_organize_by == "sender"
        assert config.output_directory == "custom_backup"
        assert config.predefined_queries["unread"] == "is:unread"

    def test_max_emails_validation_minimum(self):
        """default_max_emails should be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            GmailAssistantConfig(default_max_emails=0)

        assert "default_max_emails" in str(exc_info.value)

    def test_max_emails_validation_maximum(self):
        """default_max_emails should not exceed 10000."""
        with pytest.raises(ValidationError) as exc_info:
            GmailAssistantConfig(default_max_emails=10001)

        assert "default_max_emails" in str(exc_info.value)

    def test_max_emails_boundary_values(self):
        """default_max_emails should accept boundary values."""
        config_min = GmailAssistantConfig(default_max_emails=1)
        config_max = GmailAssistantConfig(default_max_emails=10000)

        assert config_min.default_max_emails == 1
        assert config_max.default_max_emails == 10000

    def test_format_validation_valid_values(self):
        """default_format should accept valid format values."""
        for format_value in ["eml", "markdown", "both"]:
            config = GmailAssistantConfig(default_format=format_value)
            assert config.default_format == format_value

    def test_format_validation_invalid_value(self):
        """default_format should reject invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            GmailAssistantConfig(default_format="invalid")

        error_str = str(exc_info.value)
        assert "default_format" in error_str

    def test_organize_by_validation_valid_values(self):
        """default_organize_by should accept valid organization values."""
        for org_value in ["date", "sender", "none"]:
            config = GmailAssistantConfig(default_organize_by=org_value)
            assert config.default_organize_by == org_value

    def test_organize_by_validation_invalid_value(self):
        """default_organize_by should reject invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            GmailAssistantConfig(default_organize_by="invalid")

        error_str = str(exc_info.value)
        assert "default_organize_by" in error_str


class TestDeletionConfig:
    """Tests for DeletionConfig model."""

    def test_default_values(self):
        """DeletionConfig should have proper defaults."""
        config = DeletionConfig()

        assert config.require_confirmation is True
        assert config.default_dry_run is True
        assert config.batch_size == 100
        assert config.rate_limit_delay == 0.1
        assert config.max_deletions_per_run is None

    def test_create_with_custom_values(self):
        """DeletionConfig should accept custom values."""
        config = DeletionConfig(
            require_confirmation=False,
            default_dry_run=False,
            batch_size=200,
            rate_limit_delay=0.5,
            max_deletions_per_run=1000
        )

        assert config.require_confirmation is False
        assert config.default_dry_run is False
        assert config.batch_size == 200
        assert config.rate_limit_delay == 0.5
        assert config.max_deletions_per_run == 1000

    def test_batch_size_validation_minimum(self):
        """batch_size should be at least 1."""
        with pytest.raises(ValidationError):
            DeletionConfig(batch_size=0)

    def test_batch_size_validation_maximum(self):
        """batch_size should not exceed 1000."""
        with pytest.raises(ValidationError):
            DeletionConfig(batch_size=1001)

    def test_batch_size_boundary_values(self):
        """batch_size should accept boundary values."""
        config_min = DeletionConfig(batch_size=1)
        config_max = DeletionConfig(batch_size=1000)

        assert config_min.batch_size == 1
        assert config_max.batch_size == 1000

    def test_rate_limit_delay_validation(self):
        """rate_limit_delay should be non-negative."""
        with pytest.raises(ValidationError):
            DeletionConfig(rate_limit_delay=-0.1)

    def test_rate_limit_delay_zero(self):
        """rate_limit_delay should accept zero."""
        config = DeletionConfig(rate_limit_delay=0.0)
        assert config.rate_limit_delay == 0.0

    def test_max_deletions_none_allowed(self):
        """max_deletions_per_run should allow None."""
        config = DeletionConfig(max_deletions_per_run=None)
        assert config.max_deletions_per_run is None


class TestAnalysisConfig:
    """Tests for AnalysisConfig model."""

    def test_default_values(self):
        """AnalysisConfig should have proper defaults."""
        config = AnalysisConfig()

        assert config.quality_thresholds == {"block": 0.0, "warning": 0.3, "good": 0.7}
        assert "smart" in config.parsing_strategies
        assert config.max_content_length == 500000
        assert config.enable_caching is True

    def test_create_with_custom_values(self):
        """AnalysisConfig should accept custom values."""
        config = AnalysisConfig(
            quality_thresholds={"low": 0.0, "high": 0.9},
            parsing_strategies=["html2text", "markdown"],
            max_content_length=1000000,
            enable_caching=False
        )

        assert config.quality_thresholds == {"low": 0.0, "high": 0.9}
        assert config.parsing_strategies == ["html2text", "markdown"]
        assert config.max_content_length == 1000000
        assert config.enable_caching is False

    def test_parsing_strategies_order_preserved(self):
        """parsing_strategies should preserve order."""
        strategies = ["trafilatura", "readability", "html2text"]
        config = AnalysisConfig(parsing_strategies=strategies)

        assert config.parsing_strategies == strategies

    def test_quality_thresholds_custom_keys(self):
        """quality_thresholds should accept custom keys."""
        thresholds = {"minimum": 0.2, "excellent": 0.95}
        config = AnalysisConfig(quality_thresholds=thresholds)

        assert config.quality_thresholds == thresholds


class TestDatabaseConfig:
    """Tests for DatabaseConfig model."""

    def test_default_values(self):
        """DatabaseConfig should have proper defaults."""
        config = DatabaseConfig()

        assert config.db_path == "data/databases/emails.db"
        assert config.journal_mode == "WAL"
        assert config.cache_size == 10000
        assert config.enable_fts is True
        assert config.vacuum_threshold_mb == 100

    def test_create_with_custom_values(self):
        """DatabaseConfig should accept custom values."""
        config = DatabaseConfig(
            db_path="custom/path/db.sqlite",
            journal_mode="DELETE",
            cache_size=20000,
            enable_fts=False,
            vacuum_threshold_mb=200
        )

        assert config.db_path == "custom/path/db.sqlite"
        assert config.journal_mode == "DELETE"
        assert config.cache_size == 20000
        assert config.enable_fts is False
        assert config.vacuum_threshold_mb == 200

    def test_path_handling(self):
        """DatabaseConfig should handle various path formats."""
        paths = [
            "emails.db",
            "data/emails.db",
            "/absolute/path/emails.db",
            "C:\\Windows\\path\\emails.db"
        ]

        for path in paths:
            config = DatabaseConfig(db_path=path)
            assert config.db_path == path


class TestRateLimitConfig:
    """Tests for RateLimitConfig model."""

    def test_default_values(self):
        """RateLimitConfig should have proper defaults."""
        config = RateLimitConfig()

        assert config.requests_per_second == 10.0
        assert config.burst_size == 20
        assert config.backoff_base == 1.0
        assert config.max_backoff == 60.0
        assert config.jitter_factor == 0.1

    def test_create_with_custom_values(self):
        """RateLimitConfig should accept custom values."""
        config = RateLimitConfig(
            requests_per_second=5.0,
            burst_size=10,
            backoff_base=2.0,
            max_backoff=120.0,
            jitter_factor=0.2
        )

        assert config.requests_per_second == 5.0
        assert config.burst_size == 10
        assert config.backoff_base == 2.0
        assert config.max_backoff == 120.0
        assert config.jitter_factor == 0.2

    def test_requests_per_second_validation(self):
        """requests_per_second should be positive."""
        with pytest.raises(ValidationError):
            RateLimitConfig(requests_per_second=0.0)

        with pytest.raises(ValidationError):
            RateLimitConfig(requests_per_second=-1.0)

    def test_burst_size_validation(self):
        """burst_size should be at least 1."""
        with pytest.raises(ValidationError):
            RateLimitConfig(burst_size=0)

    def test_backoff_base_validation(self):
        """backoff_base should be non-negative."""
        with pytest.raises(ValidationError):
            RateLimitConfig(backoff_base=-0.1)

        # Zero should be allowed
        config = RateLimitConfig(backoff_base=0.0)
        assert config.backoff_base == 0.0

    def test_max_backoff_validation(self):
        """max_backoff should be at least 1."""
        with pytest.raises(ValidationError):
            RateLimitConfig(max_backoff=0.5)

    def test_jitter_factor_validation_range(self):
        """jitter_factor should be between 0 and 1."""
        with pytest.raises(ValidationError):
            RateLimitConfig(jitter_factor=-0.1)

        with pytest.raises(ValidationError):
            RateLimitConfig(jitter_factor=1.1)

        # Boundary values should work
        config_min = RateLimitConfig(jitter_factor=0.0)
        config_max = RateLimitConfig(jitter_factor=1.0)

        assert config_min.jitter_factor == 0.0
        assert config_max.jitter_factor == 1.0


class TestAppConfig:
    """Tests for AppConfig complete configuration model."""

    def test_default_values(self):
        """AppConfig should have proper nested defaults."""
        config = AppConfig()

        assert isinstance(config.gmail, GmailAssistantConfig)
        assert isinstance(config.ai_detection, AIKeywordsConfig)
        assert isinstance(config.deletion, DeletionConfig)
        assert isinstance(config.analysis, AnalysisConfig)
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.rate_limit, RateLimitConfig)

    def test_create_with_nested_configs(self):
        """AppConfig should accept nested config objects."""
        gmail_config = GmailAssistantConfig(default_max_emails=500)
        deletion_config = DeletionConfig(batch_size=200)

        config = AppConfig(
            gmail=gmail_config,
            deletion=deletion_config
        )

        assert config.gmail.default_max_emails == 500
        assert config.deletion.batch_size == 200

    def test_create_from_dict(self):
        """AppConfig should be created from dictionary."""
        data = {
            "gmail": {
                "default_max_emails": 500,
                "default_format": "markdown"
            },
            "deletion": {
                "batch_size": 200
            },
            "rate_limit": {
                "requests_per_second": 5.0
            }
        }

        config = AppConfig.model_validate(data)

        assert config.gmail.default_max_emails == 500
        assert config.deletion.batch_size == 200
        assert config.rate_limit.requests_per_second == 5.0

    def test_extra_fields_ignored(self):
        """AppConfig should ignore extra fields."""
        data = {
            "gmail": {"default_max_emails": 100},
            "unknown_field": "should be ignored"
        }

        config = AppConfig.model_validate(data)

        assert config.gmail.default_max_emails == 100
        # Should not raise error for unknown_field

    def test_nested_validation_errors(self):
        """AppConfig should propagate validation errors from nested configs."""
        data = {
            "gmail": {
                "default_format": "invalid"  # Should fail validation
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            AppConfig.model_validate(data)

        assert "default_format" in str(exc_info.value)

    def test_serialization_to_dict(self):
        """AppConfig should serialize to dictionary."""
        config = AppConfig(
            gmail=GmailAssistantConfig(default_max_emails=500)
        )

        data = config.model_dump()

        assert isinstance(data, dict)
        assert "gmail" in data
        assert data["gmail"]["default_max_emails"] == 500

    def test_serialization_to_json(self):
        """AppConfig should serialize to JSON."""
        config = AppConfig(
            gmail=GmailAssistantConfig(default_max_emails=500)
        )

        json_str = config.model_dump_json()

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["gmail"]["default_max_emails"] == 500


class TestLoadValidatedConfig:
    """Tests for load_validated_config function."""

    def test_load_valid_config(self):
        """load_validated_config should load valid config file."""
        data = {
            "default_max_emails": 500,
            "default_format": "markdown"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            config = load_validated_config(temp_path, GmailAssistantConfig)

            assert isinstance(config, GmailAssistantConfig)
            assert config.default_max_emails == 500
            assert config.default_format == "markdown"
        finally:
            temp_path.unlink()

    def test_load_config_file_not_found(self):
        """load_validated_config should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_validated_config(Path("nonexistent.json"), GmailAssistantConfig)

    def test_load_config_invalid_json(self):
        """load_validated_config should raise on invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {")
            temp_path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                load_validated_config(temp_path, GmailAssistantConfig)
        finally:
            temp_path.unlink()

    def test_load_config_validation_error(self):
        """load_validated_config should raise ValidationError on invalid data."""
        data = {
            "default_format": "invalid_format"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValidationError):
                load_validated_config(temp_path, GmailAssistantConfig)
        finally:
            temp_path.unlink()


class TestLoadConfigSafe:
    """Tests for load_config_safe function."""

    def test_load_valid_config(self):
        """load_config_safe should load valid config file."""
        data = {
            "default_max_emails": 500,
            "default_format": "markdown"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            config = load_config_safe(temp_path, GmailAssistantConfig)

            assert isinstance(config, GmailAssistantConfig)
            assert config.default_max_emails == 500
        finally:
            temp_path.unlink()

    def test_load_config_file_not_found_returns_default(self):
        """load_config_safe should return default on file not found."""
        config = load_config_safe(Path("nonexistent.json"), GmailAssistantConfig)

        assert isinstance(config, GmailAssistantConfig)
        assert config.default_max_emails == 100  # Default value

    def test_load_config_invalid_json_returns_default(self):
        """load_config_safe should return default on invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            temp_path = Path(f.name)

        try:
            config = load_config_safe(temp_path, GmailAssistantConfig)

            assert isinstance(config, GmailAssistantConfig)
            assert config.default_max_emails == 100  # Default value
        finally:
            temp_path.unlink()

    def test_load_config_validation_error_returns_default(self):
        """load_config_safe should return default on validation error."""
        data = {
            "default_format": "invalid"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            config = load_config_safe(temp_path, GmailAssistantConfig)

            assert isinstance(config, GmailAssistantConfig)
            assert config.default_format == "both"  # Default value
        finally:
            temp_path.unlink()

    def test_load_config_with_custom_default(self):
        """load_config_safe should use custom default when provided."""
        custom_default = GmailAssistantConfig(default_max_emails=999)

        config = load_config_safe(
            Path("nonexistent.json"),
            GmailAssistantConfig,
            default=custom_default
        )

        assert config.default_max_emails == 999


class TestGenerateJsonSchema:
    """Tests for generate_json_schema function."""

    def test_generate_schema_returns_dict(self):
        """generate_json_schema should return dictionary."""
        schema = generate_json_schema(GmailAssistantConfig)

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "default_max_emails" in schema["properties"]

    def test_generate_schema_to_file(self):
        """generate_json_schema should write to file when path provided."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            schema = generate_json_schema(GmailAssistantConfig, temp_path)

            assert temp_path.exists()
            with open(temp_path) as f:
                file_schema = json.load(f)
            assert file_schema == schema
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_generate_schema_contains_validations(self):
        """Generated schema should include field validations."""
        schema = generate_json_schema(GmailAssistantConfig)

        # Check that validation constraints are in schema
        max_emails_schema = schema["properties"]["default_max_emails"]
        assert "minimum" in max_emails_schema or "anyOf" in max_emails_schema

    def test_generate_schema_for_nested_model(self):
        """generate_json_schema should work for nested models."""
        schema = generate_json_schema(AppConfig)

        assert "properties" in schema
        assert "gmail" in schema["properties"]
        assert "deletion" in schema["properties"]


class TestValidateAllConfigs:
    """Tests for validate_all_configs function."""

    def test_validate_all_configs_success(self):
        """validate_all_configs should validate all found configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create valid config files
            gmail_config = {"default_max_emails": 100, "default_format": "both"}
            with open(config_dir / "gmail_assistant_config.json", 'w') as f:
                json.dump(gmail_config, f)

            results = validate_all_configs(config_dir)

            assert "gmail_assistant_config.json" in results
            assert results["gmail_assistant_config.json"] is True

    def test_validate_all_configs_missing_files(self):
        """validate_all_configs should handle missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            results = validate_all_configs(config_dir)

            # All files should be None (not found)
            for filename, result in results.items():
                assert result is None

    def test_validate_all_configs_invalid_file(self):
        """validate_all_configs should mark invalid configs as False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create invalid config file
            invalid_config = {"default_format": "invalid_value"}
            with open(config_dir / "gmail_assistant_config.json", 'w') as f:
                json.dump(invalid_config, f)

            results = validate_all_configs(config_dir)

            assert results["gmail_assistant_config.json"] is False

    def test_validate_all_configs_mixed_results(self):
        """validate_all_configs should handle mixed valid/invalid/missing configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create one valid config
            valid_config = {"default_max_emails": 100}
            with open(config_dir / "gmail_assistant_config.json", 'w') as f:
                json.dump(valid_config, f)

            # Create one invalid config - use fields that exist in DeletionConfig but are invalid
            invalid_config = {"batch_size": -1}  # Invalid: must be >= 1
            with open(config_dir / "deletion_config.json", 'w') as f:
                json.dump(invalid_config, f)

            # config.json is missing

            results = validate_all_configs(config_dir)

            assert results["gmail_assistant_config.json"] is True
            assert results["deletion_config.json"] is False
            assert results["config.json"] is None


class TestConfigIntegration:
    """Integration tests for config schemas."""

    def test_full_app_config_roundtrip(self):
        """AppConfig should serialize and deserialize correctly."""
        original = AppConfig(
            gmail=GmailAssistantConfig(default_max_emails=500),
            deletion=DeletionConfig(batch_size=200),
            rate_limit=RateLimitConfig(requests_per_second=5.0)
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back
        restored = AppConfig.model_validate(data)

        assert restored.gmail.default_max_emails == 500
        assert restored.deletion.batch_size == 200
        assert restored.rate_limit.requests_per_second == 5.0

    def test_partial_config_with_defaults(self):
        """Partial config should fill in defaults for missing fields."""
        data = {
            "gmail": {
                "default_max_emails": 500
                # Other fields should use defaults
            }
        }

        config = AppConfig.model_validate(data)

        assert config.gmail.default_max_emails == 500
        assert config.gmail.default_format == "both"  # Default
        assert config.gmail.output_directory == "gmail_backup"  # Default

    def test_config_file_workflow(self):
        """Test complete workflow: create, save, load, validate config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"

            # Create config
            original = GmailAssistantConfig(
                default_max_emails=500,
                default_format="markdown"
            )

            # Save to file
            with open(config_path, 'w') as f:
                json.dump(original.model_dump(), f)

            # Load and validate
            loaded = load_validated_config(config_path, GmailAssistantConfig)

            assert loaded.default_max_emails == 500
            assert loaded.default_format == "markdown"
