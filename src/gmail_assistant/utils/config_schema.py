"""
Configuration schema validation for Gmail Assistant.
Validates JSON configuration files against defined schemas.

Security: Prevents unsafe configuration injection (M-5 fix)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors"""
    pass


class ConfigSchema:
    """Schema definitions and validation for configuration files (M-5 security fix)"""

    # Valid strategies for email parsing
    VALID_STRATEGIES: set[str] = {
        "smart", "readability", "trafilatura", "html2text", "markdownify"
    }

    # Valid output formats
    VALID_OUTPUT_FORMATS: set[str] = {"eml", "markdown", "both"}

    # Valid organization types
    VALID_ORGANIZATION_TYPES: set[str] = {"date", "sender", "none"}

    @classmethod
    def validate_parser_config(cls, config: dict[str, Any]) -> dict[str, Any]:
        """
        Validate parser configuration against schema.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ConfigValidationError("Configuration must be a dictionary")

        # Check for unknown top-level keys
        allowed_keys = {
            'strategies', 'newsletter_patterns', 'cleaning_rules',
            'formatting', 'output', 'api_settings'
        }
        unknown_keys = set(config.keys()) - allowed_keys
        if unknown_keys:
            logger.warning(f"Unknown configuration keys ignored: {unknown_keys}")

        # Validate strategies
        if "strategies" in config:
            strategies = config["strategies"]
            if not isinstance(strategies, list):
                raise ConfigValidationError("strategies must be a list")

            for strategy in strategies:
                if strategy not in cls.VALID_STRATEGIES:
                    raise ConfigValidationError(
                        f"Invalid strategy: {strategy}. "
                        f"Valid options: {cls.VALID_STRATEGIES}"
                    )

        # Validate cleaning_rules
        if "cleaning_rules" in config:
            rules = config["cleaning_rules"]
            if not isinstance(rules, dict):
                raise ConfigValidationError("cleaning_rules must be a dictionary")

            if "max_image_width" in rules:
                width = rules["max_image_width"]
                if not isinstance(width, int) or not (100 <= width <= 2000):
                    raise ConfigValidationError(
                        f"max_image_width must be integer 100-2000, got {width}"
                    )

            if "remove_tags" in rules:
                tags = rules["remove_tags"]
                if not isinstance(tags, list):
                    raise ConfigValidationError("remove_tags must be a list")
                for tag in tags:
                    if not isinstance(tag, str):
                        raise ConfigValidationError(
                            f"remove_tags items must be strings, got {type(tag)}"
                        )

        # Validate formatting
        if "formatting" in config:
            fmt = config["formatting"]
            if not isinstance(fmt, dict):
                raise ConfigValidationError("formatting must be a dictionary")

            if "max_line_length" in fmt:
                length = fmt["max_line_length"]
                if not isinstance(length, int) or not (40 <= length <= 200):
                    raise ConfigValidationError(
                        f"max_line_length must be integer 40-200, got {length}"
                    )

        return config

    @classmethod
    def validate_ai_config(cls, config: dict[str, Any]) -> dict[str, Any]:
        """
        Validate AI newsletter detection configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ConfigValidationError("Configuration must be a dictionary")

        # Validate ai_keywords
        if "ai_keywords" in config:
            keywords = config["ai_keywords"]
            if not isinstance(keywords, list):
                raise ConfigValidationError("ai_keywords must be a list")
            for kw in keywords:
                if not isinstance(kw, str):
                    raise ConfigValidationError("ai_keywords items must be strings")
                if len(kw) > 100:
                    raise ConfigValidationError(
                        f"ai_keyword too long (max 100 chars): {kw[:50]}..."
                    )

        # Validate ai_newsletter_domains
        if "ai_newsletter_domains" in config:
            domains = config["ai_newsletter_domains"]
            if not isinstance(domains, list):
                raise ConfigValidationError("ai_newsletter_domains must be a list")
            for domain in domains:
                if not isinstance(domain, str):
                    raise ConfigValidationError(
                        "ai_newsletter_domains items must be strings"
                    )
                # Basic domain format validation
                if len(domain) > 253:
                    raise ConfigValidationError(f"Domain too long: {domain[:50]}...")

        # Validate confidence_weights
        if "confidence_weights" in config:
            weights = config["confidence_weights"]
            if not isinstance(weights, dict):
                raise ConfigValidationError("confidence_weights must be a dictionary")
            for key, value in weights.items():
                if not isinstance(value, (int, float)):
                    raise ConfigValidationError(
                        f"confidence_weights values must be numbers, "
                        f"got {type(value)} for {key}"
                    )
                if not (0 <= value <= 100):
                    raise ConfigValidationError(
                        f"confidence_weight {key} must be 0-100, got {value}"
                    )

        # Validate decision_threshold
        if "decision_threshold" in config:
            thresholds = config["decision_threshold"]
            if not isinstance(thresholds, dict):
                raise ConfigValidationError("decision_threshold must be a dictionary")

            if "minimum_confidence" in thresholds:
                mc = thresholds["minimum_confidence"]
                if not isinstance(mc, (int, float)) or not (0 <= mc <= 100):
                    raise ConfigValidationError(
                        f"minimum_confidence must be 0-100, got {mc}"
                    )

            if "minimum_reasons" in thresholds:
                mr = thresholds["minimum_reasons"]
                if not isinstance(mr, int) or not (1 <= mr <= 10):
                    raise ConfigValidationError(
                        f"minimum_reasons must be integer 1-10, got {mr}"
                    )

        # Validate newsletter_patterns (regex patterns)
        if "newsletter_patterns" in config:
            patterns = config["newsletter_patterns"]
            if not isinstance(patterns, list):
                raise ConfigValidationError("newsletter_patterns must be a list")
            for pattern in patterns:
                if not isinstance(pattern, str):
                    raise ConfigValidationError(
                        "newsletter_patterns items must be strings"
                    )
                if len(pattern) > 500:
                    raise ConfigValidationError(
                        "newsletter_pattern too long (max 500 chars)"
                    )

        return config

    @classmethod
    def validate_gmail_config(cls, config: dict[str, Any]) -> dict[str, Any]:
        """
        Validate Gmail fetcher configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ConfigValidationError("Configuration must be a dictionary")

        # Validate output format
        if "output_format" in config:
            fmt = config["output_format"]
            if fmt not in cls.VALID_OUTPUT_FORMATS:
                raise ConfigValidationError(
                    f"Invalid output_format: {fmt}. "
                    f"Valid options: {cls.VALID_OUTPUT_FORMATS}"
                )

        # Validate organization type
        if "organization" in config:
            org = config["organization"]
            if org not in cls.VALID_ORGANIZATION_TYPES:
                raise ConfigValidationError(
                    f"Invalid organization: {org}. "
                    f"Valid options: {cls.VALID_ORGANIZATION_TYPES}"
                )

        # Validate max_emails
        if "max_emails" in config:
            max_emails = config["max_emails"]
            if not isinstance(max_emails, int) or not (1 <= max_emails <= 100000):
                raise ConfigValidationError(
                    f"max_emails must be integer 1-100000, got {max_emails}"
                )

        # Validate rate_limit
        if "rate_limit" in config:
            rate = config["rate_limit"]
            if not isinstance(rate, (int, float)) or not (0.1 <= rate <= 100):
                raise ConfigValidationError(
                    f"rate_limit must be 0.1-100, got {rate}"
                )

        return config


def validate_config_file(config: dict[str, Any], config_type: str) -> dict[str, Any]:
    """
    Validate a configuration file against its schema.

    Args:
        config: Configuration dictionary to validate
        config_type: Type of config ('parser', 'ai', 'gmail')

    Returns:
        Validated configuration

    Raises:
        ConfigValidationError: If configuration is invalid
    """
    validators = {
        'parser': ConfigSchema.validate_parser_config,
        'ai': ConfigSchema.validate_ai_config,
        'gmail': ConfigSchema.validate_gmail_config,
    }

    validator = validators.get(config_type)
    if validator is None:
        raise ConfigValidationError(
            f"Unknown config type: {config_type}. "
            f"Valid types: {list(validators.keys())}"
        )

    return validator(config)


class ConfigValidator:
    """
    Wrapper class for configuration validation.
    Provides validate() method that tests expect.
    """

    def __init__(self) -> None:
        """Initialize validator with available schemas."""
        self.schemas: dict[str, Any] = {
            'parser': ConfigSchema.validate_parser_config,
            'ai': ConfigSchema.validate_ai_config,
            'gmail': ConfigSchema.validate_gmail_config,
        }

    def validate(self, config: dict[str, Any], config_type: str) -> dict[str, Any]:
        """
        Validate a configuration dictionary.

        Args:
            config: Configuration dictionary to validate
            config_type: Type of config ('parser', 'ai', 'gmail')

        Returns:
            Dictionary with 'valid' bool and 'errors' list
        """
        try:
            validate_config_file(config, config_type)
            return {'valid': True, 'errors': []}
        except ConfigValidationError as e:
            return {'valid': False, 'errors': [str(e)]}
        except Exception as e:
            return {'valid': False, 'errors': [f"Validation failed: {e}"]}

    def get_schema(self, config_type: str) -> Any | None:
        """Get validator for config type."""
        return self.schemas.get(config_type)
