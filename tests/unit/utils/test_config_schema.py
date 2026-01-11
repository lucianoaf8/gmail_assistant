"""
Comprehensive tests for config_schema.py module.
Tests ConfigSchema class for configuration validation.
"""

import pytest

from gmail_assistant.utils.config_schema import (
    ConfigSchema,
    ConfigValidationError,
    ConfigValidator,
    validate_config_file,
)


class TestConfigValidationError:
    """Tests for ConfigValidationError exception."""

    def test_exception_with_message(self):
        """Test exception stores message."""
        with pytest.raises(ConfigValidationError) as exc_info:
            raise ConfigValidationError("Test error message")
        assert str(exc_info.value) == "Test error message"

    def test_exception_is_exception_subclass(self):
        """Test ConfigValidationError is an Exception subclass."""
        assert issubclass(ConfigValidationError, Exception)


class TestValidStrategies:
    """Tests for VALID_STRATEGIES constant."""

    def test_valid_strategies_contains_smart(self):
        """Test VALID_STRATEGIES contains 'smart'."""
        assert "smart" in ConfigSchema.VALID_STRATEGIES

    def test_valid_strategies_contains_readability(self):
        """Test VALID_STRATEGIES contains 'readability'."""
        assert "readability" in ConfigSchema.VALID_STRATEGIES

    def test_valid_strategies_contains_trafilatura(self):
        """Test VALID_STRATEGIES contains 'trafilatura'."""
        assert "trafilatura" in ConfigSchema.VALID_STRATEGIES

    def test_valid_strategies_contains_html2text(self):
        """Test VALID_STRATEGIES contains 'html2text'."""
        assert "html2text" in ConfigSchema.VALID_STRATEGIES

    def test_valid_strategies_contains_markdownify(self):
        """Test VALID_STRATEGIES contains 'markdownify'."""
        assert "markdownify" in ConfigSchema.VALID_STRATEGIES


class TestValidateParserConfig:
    """Tests for validate_parser_config method."""

    def test_valid_empty_config(self):
        """Test empty config is valid."""
        config = {}
        result = ConfigSchema.validate_parser_config(config)
        assert result == config

    def test_valid_strategies_list(self):
        """Test valid strategies list passes."""
        config = {"strategies": ["smart", "readability"]}
        result = ConfigSchema.validate_parser_config(config)
        assert result == config

    def test_invalid_strategy_raises(self):
        """Test invalid strategy raises error."""
        config = {"strategies": ["invalid_strategy"]}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "Invalid strategy" in str(exc_info.value)

    def test_strategies_not_list_raises(self):
        """Test strategies as non-list raises error."""
        config = {"strategies": "smart"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "strategies must be a list" in str(exc_info.value)

    def test_config_not_dict_raises(self):
        """Test non-dict config raises error."""
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config("not a dict")
        assert "Configuration must be a dictionary" in str(exc_info.value)

    def test_valid_cleaning_rules(self):
        """Test valid cleaning_rules passes."""
        config = {
            "cleaning_rules": {
                "max_image_width": 800,
                "remove_tags": ["script", "style"]
            }
        }
        result = ConfigSchema.validate_parser_config(config)
        assert result == config

    def test_cleaning_rules_not_dict_raises(self):
        """Test cleaning_rules as non-dict raises error."""
        config = {"cleaning_rules": "not a dict"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "cleaning_rules must be a dictionary" in str(exc_info.value)

    def test_max_image_width_too_small(self):
        """Test max_image_width below minimum raises error."""
        config = {"cleaning_rules": {"max_image_width": 50}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "max_image_width must be integer 100-2000" in str(exc_info.value)

    def test_max_image_width_too_large(self):
        """Test max_image_width above maximum raises error."""
        config = {"cleaning_rules": {"max_image_width": 3000}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "max_image_width must be integer 100-2000" in str(exc_info.value)

    def test_max_image_width_not_int(self):
        """Test max_image_width as non-int raises error."""
        config = {"cleaning_rules": {"max_image_width": "800"}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "max_image_width must be integer" in str(exc_info.value)

    def test_remove_tags_not_list(self):
        """Test remove_tags as non-list raises error."""
        config = {"cleaning_rules": {"remove_tags": "script"}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "remove_tags must be a list" in str(exc_info.value)

    def test_remove_tags_non_string_item(self):
        """Test remove_tags with non-string item raises error."""
        config = {"cleaning_rules": {"remove_tags": ["script", 123]}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "remove_tags items must be strings" in str(exc_info.value)

    def test_valid_formatting(self):
        """Test valid formatting config passes."""
        config = {"formatting": {"max_line_length": 80}}
        result = ConfigSchema.validate_parser_config(config)
        assert result == config

    def test_formatting_not_dict(self):
        """Test formatting as non-dict raises error."""
        config = {"formatting": "not a dict"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "formatting must be a dictionary" in str(exc_info.value)

    def test_max_line_length_too_small(self):
        """Test max_line_length below minimum raises error."""
        config = {"formatting": {"max_line_length": 30}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "max_line_length must be integer 40-200" in str(exc_info.value)

    def test_max_line_length_too_large(self):
        """Test max_line_length above maximum raises error."""
        config = {"formatting": {"max_line_length": 300}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_parser_config(config)
        assert "max_line_length must be integer 40-200" in str(exc_info.value)


class TestValidateAIConfig:
    """Tests for validate_ai_config method."""

    def test_valid_empty_config(self):
        """Test empty config is valid."""
        config = {}
        result = ConfigSchema.validate_ai_config(config)
        assert result == config

    def test_valid_ai_keywords(self):
        """Test valid ai_keywords passes."""
        config = {"ai_keywords": ["chatgpt", "llm", "ai"]}
        result = ConfigSchema.validate_ai_config(config)
        assert result == config

    def test_ai_keywords_not_list(self):
        """Test ai_keywords as non-list raises error."""
        config = {"ai_keywords": "chatgpt"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "ai_keywords must be a list" in str(exc_info.value)

    def test_ai_keywords_non_string_item(self):
        """Test ai_keywords with non-string item raises error."""
        config = {"ai_keywords": ["valid", 123]}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "ai_keywords items must be strings" in str(exc_info.value)

    def test_ai_keyword_too_long(self):
        """Test ai_keyword exceeding max length raises error."""
        config = {"ai_keywords": ["a" * 101]}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "ai_keyword too long" in str(exc_info.value)

    def test_valid_ai_newsletter_domains(self):
        """Test valid ai_newsletter_domains passes."""
        config = {"ai_newsletter_domains": ["openai.com", "anthropic.com"]}
        result = ConfigSchema.validate_ai_config(config)
        assert result == config

    def test_ai_newsletter_domains_not_list(self):
        """Test ai_newsletter_domains as non-list raises error."""
        config = {"ai_newsletter_domains": "openai.com"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "ai_newsletter_domains must be a list" in str(exc_info.value)

    def test_ai_newsletter_domains_non_string(self):
        """Test ai_newsletter_domains with non-string item raises error."""
        config = {"ai_newsletter_domains": ["valid.com", 123]}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "ai_newsletter_domains items must be strings" in str(exc_info.value)

    def test_domain_too_long(self):
        """Test domain exceeding max length raises error."""
        config = {"ai_newsletter_domains": ["a" * 254]}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "Domain too long" in str(exc_info.value)

    def test_valid_confidence_weights(self):
        """Test valid confidence_weights passes."""
        config = {"confidence_weights": {"keyword": 50, "domain": 30}}
        result = ConfigSchema.validate_ai_config(config)
        assert result == config

    def test_confidence_weights_not_dict(self):
        """Test confidence_weights as non-dict raises error."""
        config = {"confidence_weights": "not a dict"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "confidence_weights must be a dictionary" in str(exc_info.value)

    def test_confidence_weight_non_numeric(self):
        """Test confidence_weight with non-numeric value raises error."""
        config = {"confidence_weights": {"keyword": "fifty"}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "confidence_weights values must be numbers" in str(exc_info.value)

    def test_confidence_weight_out_of_range(self):
        """Test confidence_weight out of range raises error."""
        config = {"confidence_weights": {"keyword": 150}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "must be 0-100" in str(exc_info.value)

    def test_confidence_weight_negative(self):
        """Test negative confidence_weight raises error."""
        config = {"confidence_weights": {"keyword": -10}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "must be 0-100" in str(exc_info.value)

    def test_valid_decision_threshold(self):
        """Test valid decision_threshold passes."""
        config = {
            "decision_threshold": {
                "minimum_confidence": 70,
                "minimum_reasons": 3
            }
        }
        result = ConfigSchema.validate_ai_config(config)
        assert result == config

    def test_decision_threshold_not_dict(self):
        """Test decision_threshold as non-dict raises error."""
        config = {"decision_threshold": "not a dict"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "decision_threshold must be a dictionary" in str(exc_info.value)

    def test_minimum_confidence_invalid(self):
        """Test minimum_confidence out of range raises error."""
        config = {"decision_threshold": {"minimum_confidence": 150}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "minimum_confidence must be 0-100" in str(exc_info.value)

    def test_minimum_reasons_invalid(self):
        """Test minimum_reasons out of range raises error."""
        config = {"decision_threshold": {"minimum_reasons": 15}}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "minimum_reasons must be integer 1-10" in str(exc_info.value)

    def test_valid_newsletter_patterns(self):
        """Test valid newsletter_patterns passes."""
        config = {"newsletter_patterns": ["pattern1", "pattern2"]}
        result = ConfigSchema.validate_ai_config(config)
        assert result == config

    def test_newsletter_patterns_not_list(self):
        """Test newsletter_patterns as non-list raises error."""
        config = {"newsletter_patterns": "pattern"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "newsletter_patterns must be a list" in str(exc_info.value)

    def test_newsletter_pattern_too_long(self):
        """Test newsletter_pattern exceeding max length raises error."""
        config = {"newsletter_patterns": ["a" * 501]}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_ai_config(config)
        assert "newsletter_pattern too long" in str(exc_info.value)


class TestValidateGmailConfig:
    """Tests for validate_gmail_config method."""

    def test_valid_empty_config(self):
        """Test empty config is valid."""
        config = {}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_valid_output_format_eml(self):
        """Test output_format 'eml' is valid."""
        config = {"output_format": "eml"}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_valid_output_format_markdown(self):
        """Test output_format 'markdown' is valid."""
        config = {"output_format": "markdown"}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_valid_output_format_both(self):
        """Test output_format 'both' is valid."""
        config = {"output_format": "both"}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_invalid_output_format(self):
        """Test invalid output_format raises error."""
        config = {"output_format": "pdf"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_gmail_config(config)
        assert "Invalid output_format" in str(exc_info.value)

    def test_valid_organization_date(self):
        """Test organization 'date' is valid."""
        config = {"organization": "date"}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_valid_organization_sender(self):
        """Test organization 'sender' is valid."""
        config = {"organization": "sender"}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_valid_organization_none(self):
        """Test organization 'none' is valid."""
        config = {"organization": "none"}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_invalid_organization(self):
        """Test invalid organization raises error."""
        config = {"organization": "thread"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_gmail_config(config)
        assert "Invalid organization" in str(exc_info.value)

    def test_valid_max_emails(self):
        """Test valid max_emails passes."""
        config = {"max_emails": 1000}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_max_emails_too_small(self):
        """Test max_emails below minimum raises error."""
        config = {"max_emails": 0}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_gmail_config(config)
        assert "max_emails must be integer 1-100000" in str(exc_info.value)

    def test_max_emails_too_large(self):
        """Test max_emails above maximum raises error."""
        config = {"max_emails": 200000}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_gmail_config(config)
        assert "max_emails must be integer 1-100000" in str(exc_info.value)

    def test_max_emails_not_int(self):
        """Test max_emails as non-int raises error."""
        config = {"max_emails": "1000"}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_gmail_config(config)
        assert "max_emails must be integer" in str(exc_info.value)

    def test_valid_rate_limit(self):
        """Test valid rate_limit passes."""
        config = {"rate_limit": 5.0}
        result = ConfigSchema.validate_gmail_config(config)
        assert result == config

    def test_rate_limit_too_small(self):
        """Test rate_limit below minimum raises error."""
        config = {"rate_limit": 0.05}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_gmail_config(config)
        assert "rate_limit must be 0.1-100" in str(exc_info.value)

    def test_rate_limit_too_large(self):
        """Test rate_limit above maximum raises error."""
        config = {"rate_limit": 150}
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigSchema.validate_gmail_config(config)
        assert "rate_limit must be 0.1-100" in str(exc_info.value)


class TestValidateConfigFile:
    """Tests for validate_config_file function."""

    def test_validate_parser_type(self):
        """Test validate_config_file with parser type."""
        config = {"strategies": ["smart"]}
        result = validate_config_file(config, "parser")
        assert result == config

    def test_validate_ai_type(self):
        """Test validate_config_file with ai type."""
        config = {"ai_keywords": ["chatgpt"]}
        result = validate_config_file(config, "ai")
        assert result == config

    def test_validate_gmail_type(self):
        """Test validate_config_file with gmail type."""
        config = {"output_format": "eml"}
        result = validate_config_file(config, "gmail")
        assert result == config

    def test_unknown_config_type(self):
        """Test unknown config type raises error."""
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config_file({}, "unknown")
        assert "Unknown config type" in str(exc_info.value)


class TestConfigValidator:
    """Tests for ConfigValidator class."""

    def test_validator_init(self):
        """Test ConfigValidator initialization."""
        validator = ConfigValidator()
        assert "parser" in validator.schemas
        assert "ai" in validator.schemas
        assert "gmail" in validator.schemas

    def test_validate_valid_config(self):
        """Test validate returns valid result for valid config."""
        validator = ConfigValidator()
        result = validator.validate({"strategies": ["smart"]}, "parser")
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_invalid_config(self):
        """Test validate returns invalid result for invalid config."""
        validator = ConfigValidator()
        result = validator.validate({"strategies": ["invalid"]}, "parser")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_handles_exception(self):
        """Test validate handles unexpected exceptions."""
        validator = ConfigValidator()
        # Pass something that might cause an unexpected error
        result = validator.validate(None, "parser")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_get_schema_returns_validator(self):
        """Test get_schema returns correct validator."""
        validator = ConfigValidator()
        parser_schema = validator.get_schema("parser")
        assert parser_schema is not None
        assert callable(parser_schema)

    def test_get_schema_unknown_returns_none(self):
        """Test get_schema returns None for unknown type."""
        validator = ConfigValidator()
        result = validator.get_schema("unknown")
        assert result is None


class TestValidOutputFormats:
    """Tests for VALID_OUTPUT_FORMATS constant."""

    def test_contains_eml(self):
        """Test VALID_OUTPUT_FORMATS contains 'eml'."""
        assert "eml" in ConfigSchema.VALID_OUTPUT_FORMATS

    def test_contains_markdown(self):
        """Test VALID_OUTPUT_FORMATS contains 'markdown'."""
        assert "markdown" in ConfigSchema.VALID_OUTPUT_FORMATS

    def test_contains_both(self):
        """Test VALID_OUTPUT_FORMATS contains 'both'."""
        assert "both" in ConfigSchema.VALID_OUTPUT_FORMATS


class TestValidOrganizationTypes:
    """Tests for VALID_ORGANIZATION_TYPES constant."""

    def test_contains_date(self):
        """Test VALID_ORGANIZATION_TYPES contains 'date'."""
        assert "date" in ConfigSchema.VALID_ORGANIZATION_TYPES

    def test_contains_sender(self):
        """Test VALID_ORGANIZATION_TYPES contains 'sender'."""
        assert "sender" in ConfigSchema.VALID_ORGANIZATION_TYPES

    def test_contains_none(self):
        """Test VALID_ORGANIZATION_TYPES contains 'none'."""
        assert "none" in ConfigSchema.VALID_ORGANIZATION_TYPES
