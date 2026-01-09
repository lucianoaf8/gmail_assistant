"""Unit tests for gmail_assistant.core.config.AppConfig."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import mock

import pytest

from gmail_assistant.core.config import AppConfig
from gmail_assistant.core.exceptions import ConfigError


class TestAppConfigDefaults:
    """Test default configuration creation."""

    def test_default_dir_is_in_home(self):
        """Default directory should be ~/.gmail-assistant/."""
        default_dir = AppConfig.default_dir()
        assert default_dir == Path.home() / ".gmail-assistant"

    def test_load_returns_defaults_when_no_config(self, temp_dir: Path):
        """Loading with no config file should return defaults."""
        with mock.patch.object(AppConfig, "default_dir", return_value=temp_dir):
            cfg = AppConfig.load()
            assert cfg.max_emails == 1000
            assert cfg.rate_limit_per_second == 10.0
            assert cfg.log_level == "INFO"

    def test_default_credentials_path(self, temp_dir: Path):
        """Default credentials should be in default directory."""
        with mock.patch.object(AppConfig, "default_dir", return_value=temp_dir):
            cfg = AppConfig.load()
            assert cfg.credentials_path == temp_dir / "credentials.json"

    def test_default_token_path(self, temp_dir: Path):
        """Default token should be in default directory."""
        with mock.patch.object(AppConfig, "default_dir", return_value=temp_dir):
            cfg = AppConfig.load()
            assert cfg.token_path == temp_dir / "token.json"

    def test_default_output_dir(self, temp_dir: Path):
        """Default output should be in default directory."""
        with mock.patch.object(AppConfig, "default_dir", return_value=temp_dir):
            cfg = AppConfig.load()
            assert cfg.output_dir == temp_dir / "backups"


class TestAppConfigFromFile:
    """Test configuration loading from file."""

    def test_load_from_file(self, config_file: Path, sample_config: dict):
        """Configuration should load from file."""
        cfg = AppConfig.load(config_file, allow_repo_credentials=True)
        assert cfg.max_emails == sample_config["max_emails"]
        assert cfg.rate_limit_per_second == sample_config["rate_limit_per_second"]
        assert cfg.log_level == sample_config["log_level"].upper()

    def test_load_from_explicit_path(self, config_file: Path):
        """Explicit path should be used when provided."""
        cfg = AppConfig.load(config_file, allow_repo_credentials=True)
        assert cfg is not None

    def test_load_nonexistent_raises_error(self, temp_dir: Path):
        """Loading nonexistent explicit path should raise ConfigError."""
        nonexistent = temp_dir / "does_not_exist.json"
        with pytest.raises(ConfigError, match="not found"):
            AppConfig.load(nonexistent)

    def test_load_invalid_json_raises_error(self, temp_dir: Path):
        """Loading invalid JSON should raise ConfigError."""
        bad_json = temp_dir / "bad.json"
        bad_json.write_text("{ not valid json }")
        with pytest.raises(ConfigError, match="Invalid JSON"):
            AppConfig.load(bad_json, allow_repo_credentials=True)


class TestAppConfigValidation:
    """Test configuration validation."""

    def test_unknown_keys_raise_error(self, temp_dir: Path):
        """Unknown configuration keys should raise ConfigError."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({
            "unknown_key": "value",
        }))
        with pytest.raises(ConfigError, match="Unknown"):
            AppConfig.load(config_path, allow_repo_credentials=True)

    def test_max_emails_too_low(self, temp_dir: Path):
        """max_emails below 1 should raise ConfigError."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"max_emails": 0}))
        with pytest.raises(ConfigError):
            AppConfig.load(config_path, allow_repo_credentials=True)

    def test_max_emails_too_high(self, temp_dir: Path):
        """max_emails above limit should raise ConfigError."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"max_emails": 100001}))
        with pytest.raises(ConfigError):
            AppConfig.load(config_path, allow_repo_credentials=True)

    def test_rate_limit_too_low(self, temp_dir: Path):
        """rate_limit at or below 0 should raise ConfigError."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"rate_limit_per_second": 0}))
        with pytest.raises(ConfigError):
            AppConfig.load(config_path, allow_repo_credentials=True)

    def test_rate_limit_too_high(self, temp_dir: Path):
        """rate_limit above 100 should raise ConfigError."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"rate_limit_per_second": 101}))
        with pytest.raises(ConfigError):
            AppConfig.load(config_path, allow_repo_credentials=True)

    def test_invalid_log_level(self, temp_dir: Path):
        """Invalid log level should raise ConfigError."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"log_level": "INVALID"}))
        with pytest.raises(ConfigError, match="log_level"):
            AppConfig.load(config_path, allow_repo_credentials=True)

    def test_log_level_case_insensitive(self, temp_dir: Path):
        """Log level should be case insensitive."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"log_level": "debug"}))
        cfg = AppConfig.load(config_path, allow_repo_credentials=True)
        assert cfg.log_level == "DEBUG"


class TestAppConfigTypeValidation:
    """Test type validation of configuration values."""

    def test_max_emails_must_be_int(self, temp_dir: Path):
        """max_emails must be integer."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"max_emails": "100"}))
        with pytest.raises(ConfigError, match="integer"):
            AppConfig.load(config_path, allow_repo_credentials=True)

    def test_rate_limit_accepts_int(self, temp_dir: Path):
        """rate_limit should accept integer."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"rate_limit_per_second": 5}))
        cfg = AppConfig.load(config_path, allow_repo_credentials=True)
        assert cfg.rate_limit_per_second == 5.0

    def test_log_level_must_be_string(self, temp_dir: Path):
        """log_level must be string."""
        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({"log_level": 123}))
        with pytest.raises(ConfigError, match="string"):
            AppConfig.load(config_path, allow_repo_credentials=True)


class TestAppConfigEnvVar:
    """Test environment variable configuration."""

    def test_env_var_overrides_default(self, temp_dir: Path, config_file: Path):
        """Environment variable should be used when set."""
        with mock.patch.dict(os.environ, {AppConfig.ENV_VAR: str(config_file)}):
            with mock.patch.object(AppConfig, "default_dir", return_value=temp_dir):
                cfg = AppConfig.load(allow_repo_credentials=True)
                assert cfg.max_emails == 100  # From config file

    def test_env_var_nonexistent_raises_error(self, temp_dir: Path):
        """Nonexistent env var path should raise ConfigError."""
        with mock.patch.dict(os.environ, {AppConfig.ENV_VAR: str(temp_dir / "missing.json")}):
            with pytest.raises(ConfigError, match="not found"):
                AppConfig.load()


class TestAppConfigClassVars:
    """Test class-level variables."""

    def test_env_var_name(self):
        """ENV_VAR should have expected name."""
        assert AppConfig.ENV_VAR == "gmail_assistant_CONFIG"

    def test_project_config_name(self):
        """PROJECT_CONFIG_NAME should have expected name."""
        assert AppConfig.PROJECT_CONFIG_NAME == "gmail-assistant.json"
