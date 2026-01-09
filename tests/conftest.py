"""Shared test fixtures for Gmail Assistant."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir: Path) -> dict:
    """Return a sample configuration dictionary."""
    return {
        "credentials_path": str(temp_dir / "credentials.json"),
        "token_path": str(temp_dir / "token.json"),
        "output_dir": str(temp_dir / "backups"),
        "max_emails": 100,
        "rate_limit_per_second": 5.0,
        "log_level": "DEBUG",
    }


@pytest.fixture
def config_file(temp_dir: Path, sample_config: dict) -> Path:
    """Create a temporary config file."""
    config_path = temp_dir / "config.json"
    config_path.write_text(json.dumps(sample_config))
    return config_path


@pytest.fixture
def mock_credentials(temp_dir: Path) -> Path:
    """Create mock credentials file."""
    creds_path = temp_dir / "credentials.json"
    creds_path.write_text(json.dumps({
        "installed": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
        }
    }))
    return creds_path
