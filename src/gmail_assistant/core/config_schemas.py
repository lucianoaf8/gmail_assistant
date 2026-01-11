"""
Configuration schema validation using Pydantic.

Provides validated configuration models for all JSON config files.
"""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


# =============================================================================
# AI Newsletter Detection Config
# =============================================================================

class AIKeywordsConfig(BaseModel):
    """Configuration for AI newsletter detection."""
    ai_keywords: list[str] = Field(default_factory=list, description="Keywords indicating AI content")
    ai_newsletter_domains: list[str] = Field(default_factory=list, description="Known AI newsletter domains")
    newsletter_patterns: list[str] = Field(default_factory=list, description="Regex patterns for newsletters")
    unsubscribe_patterns: list[str] = Field(default_factory=list, description="Unsubscribe link patterns")
    confidence_weights: dict[str, int] = Field(default_factory=dict, description="Scoring weights")
    decision_threshold: dict[str, int] = Field(default_factory=dict, description="Decision thresholds")

    @field_validator('confidence_weights')
    @classmethod
    def validate_weights(cls, v):
        """Validate required weight keys exist."""
        required = {'ai_keywords_subject', 'ai_keywords_sender', 'known_domain'}
        if not required.issubset(v.keys()):
            missing = required - set(v.keys())
            logger.warning(f"Missing confidence weights: {missing}. Using defaults.")
            # Add defaults for missing keys
            defaults = {
                'ai_keywords_subject': 3,
                'ai_keywords_sender': 2,
                'known_domain': 4,
                'newsletter_pattern': 2,
                'unsubscribe_link': 1,
                'automated_sender': 1
            }
            for key in missing:
                v[key] = defaults.get(key, 1)
        return v

    @field_validator('decision_threshold')
    @classmethod
    def validate_threshold(cls, v):
        """Validate decision threshold has required keys."""
        if 'minimum_confidence' not in v:
            v['minimum_confidence'] = 4
        if 'minimum_reasons' not in v:
            v['minimum_reasons'] = 2
        return v


# =============================================================================
# Gmail Assistant Main Config
# =============================================================================

class GmailAssistantConfig(BaseModel):
    """Main application configuration."""
    default_max_emails: int = Field(default=100, ge=1, le=10000, description="Default max emails to fetch")
    default_format: str = Field(default="both", description="Output format: eml, markdown, both")
    default_organize_by: str = Field(default="date", description="Organization: date, sender, none")
    output_directory: str = Field(default="gmail_backup", description="Default output directory")
    predefined_queries: dict[str, str] = Field(default_factory=dict, description="Named queries")

    @field_validator('default_format')
    @classmethod
    def validate_format(cls, v):
        """Validate output format."""
        valid = {'eml', 'markdown', 'both'}
        if v not in valid:
            raise ValueError(f"default_format must be one of {valid}, got '{v}'")
        return v

    @field_validator('default_organize_by')
    @classmethod
    def validate_organize_by(cls, v):
        """Validate organization method."""
        valid = {'date', 'sender', 'none'}
        if v not in valid:
            raise ValueError(f"default_organize_by must be one of {valid}, got '{v}'")
        return v


# =============================================================================
# Deletion Config
# =============================================================================

class DeletionConfig(BaseModel):
    """Deletion operation configuration."""
    require_confirmation: bool = Field(default=True, description="Require user confirmation")
    default_dry_run: bool = Field(default=True, description="Default to dry-run mode")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Emails per batch")
    rate_limit_delay: float = Field(default=0.1, ge=0, description="Delay between batches")
    max_deletions_per_run: int | None = Field(default=None, description="Safety limit")


# =============================================================================
# Analysis Config
# =============================================================================

class AnalysisConfig(BaseModel):
    """Analysis pipeline configuration."""
    quality_thresholds: dict[str, float] = Field(
        default_factory=lambda: {'block': 0.0, 'warning': 0.3, 'good': 0.7},
        description="Quality score thresholds"
    )
    parsing_strategies: list[str] = Field(
        default_factory=lambda: ['smart', 'readability', 'trafilatura', 'html2text', 'markdownify'],
        description="Parsing strategies in order of preference"
    )
    max_content_length: int = Field(default=500000, description="Max content length to process")
    enable_caching: bool = Field(default=True, description="Enable result caching")


# =============================================================================
# Database Config
# =============================================================================

class DatabaseConfig(BaseModel):
    """Database configuration."""
    db_path: str = Field(default="data/databases/emails.db", description="Database file path")
    journal_mode: str = Field(default="WAL", description="SQLite journal mode")
    cache_size: int = Field(default=10000, description="SQLite cache size")
    enable_fts: bool = Field(default=True, description="Enable full-text search")
    vacuum_threshold_mb: int = Field(default=100, description="Auto-vacuum threshold")


# =============================================================================
# Rate Limiting Config
# =============================================================================

class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_second: float = Field(default=10.0, gt=0, description="Max requests per second")
    burst_size: int = Field(default=20, ge=1, description="Burst allowance")
    backoff_base: float = Field(default=1.0, ge=0, description="Exponential backoff base")
    max_backoff: float = Field(default=60.0, ge=1, description="Maximum backoff seconds")
    jitter_factor: float = Field(default=0.1, ge=0, le=1, description="Random jitter factor")


# =============================================================================
# Complete Application Config
# =============================================================================

class AppConfig(BaseModel):
    """Complete application configuration combining all sections."""
    gmail: GmailAssistantConfig = Field(default_factory=GmailAssistantConfig)
    ai_detection: AIKeywordsConfig = Field(default_factory=AIKeywordsConfig)
    deletion: DeletionConfig = Field(default_factory=DeletionConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

    model_config = ConfigDict(extra='ignore')


# =============================================================================
# Config Loading Functions
# =============================================================================

def load_validated_config(path: Path, model: type[BaseModel]) -> BaseModel:
    """
    Load and validate a config file against its schema.

    Args:
        path: Path to JSON config file
        model: Pydantic model class to validate against

    Returns:
        Validated config instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config doesn't match schema
    """
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return model.model_validate(data)


def load_config_safe(path: Path, model: type[BaseModel], default: BaseModel | None = None) -> BaseModel:
    """
    Load config with fallback to defaults on error.

    Args:
        path: Path to JSON config file
        model: Pydantic model class
        default: Default instance to use on error

    Returns:
        Config instance (loaded or default)
    """
    try:
        return load_validated_config(path, model)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {path}. Using defaults.")
        return default or model()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}. Using defaults.")
        return default or model()
    except Exception as e:
        logger.error(f"Error loading config {path}: {e}. Using defaults.")
        return default or model()


def generate_json_schema(model: type[BaseModel], output_path: Path | None = None) -> dict[str, Any]:
    """
    Generate JSON Schema from Pydantic model.

    Args:
        model: Pydantic model class
        output_path: Optional path to write schema file

    Returns:
        JSON Schema dictionary
    """
    schema = model.model_json_schema()

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        logger.info(f"Generated JSON Schema: {output_path}")

    return schema


def validate_all_configs(config_dir: Path) -> dict[str, bool]:
    """
    Validate all config files in a directory.

    Args:
        config_dir: Directory containing config files

    Returns:
        Dictionary mapping filename to validation status
    """
    config_mapping = {
        'config.json': AIKeywordsConfig,
        'gmail_assistant_config.json': GmailAssistantConfig,
        'deletion_config.json': DeletionConfig,
        'analysis.json': AnalysisConfig,
    }

    results = {}
    for filename, model in config_mapping.items():
        filepath = config_dir / filename
        try:
            if filepath.exists():
                load_validated_config(filepath, model)
                results[filename] = True
                logger.info(f"✓ {filename} validated successfully")
            else:
                results[filename] = None  # File not found
                logger.warning(f"? {filename} not found")
        except Exception as e:
            results[filename] = False
            logger.error(f"✗ {filename} validation failed: {e}")

    return results
