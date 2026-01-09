#!/usr/bin/env python3
"""
Import resolution checker - validates imports actually resolve.

Must be run AFTER pip install -e . in a clean environment.
CORRECTED: Includes isolation verification and clear guidance.
"""
from __future__ import annotations

import sys
from pathlib import Path


def check_environment() -> tuple[bool, list[str]]:
    """
    Verify we're not importing from source directory.
  
    Returns:
        (is_safe, warnings)
    """
    warnings = []
    cwd = Path.cwd().resolve()
  
    # Check sys.path doesn't include src/ directly
    for p in sys.path:
        if not p:
            continue
        path = Path(p).resolve()
        if path == cwd / "src":
            warnings.append(f"sys.path contains src/: {path}")
        elif path == cwd:
            warnings.append(f"sys.path contains repo root: {path}")
  
    is_safe = len(warnings) == 0
    return is_safe, warnings


def check_imports() -> bool:
    """Try importing key modules."""
    imports_to_check = [
        "gmail_assistant",
        "gmail_assistant.cli.main",
        "gmail_assistant.core.config",
        "gmail_assistant.core.exceptions",
    ]
  
    all_ok = True
  
    for module in imports_to_check:
        try:
            __import__(module)
            print(f"  [OK] import {module}")
        except ImportError as e:
            print(f"  [FAIL] import {module}: {e}")
            all_ok = False
  
    return all_ok


def check_version() -> bool:
    """Verify __version__ is accessible."""
    try:
        import gmail_assistant
        version = gmail_assistant.__version__
        print(f"  [OK] gmail_assistant.__version__ = {version}")
        return True
    except Exception as e:
        print(f"  [FAIL] Could not access __version__: {e}")
        return False


def check_exception_taxonomy() -> bool:
    """Verify exception hierarchy is correct and unified."""
    try:
        from gmail_assistant.core.exceptions import (
            GmailAssistantError,
            ConfigError,
            AuthError,
            NetworkError,
        )
      
        # Verify inheritance
        assert issubclass(ConfigError, GmailAssistantError), "ConfigError must inherit GmailAssistantError"
        assert issubclass(AuthError, GmailAssistantError), "AuthError must inherit GmailAssistantError"
        assert issubclass(NetworkError, GmailAssistantError), "NetworkError must inherit GmailAssistantError"
      
        print("  [OK] Exception taxonomy correct")
        return True
    except Exception as e:
        print(f"  [FAIL] Exception taxonomy: {e}")
        return False


def check_no_duplicate_configerror() -> bool:
    """Verify ConfigError is not duplicated in config.py."""
    try:
        # Import both modules
        from gmail_assistant.core import config
        from gmail_assistant.core import exceptions
      
        # Check that config.ConfigError IS exceptions.ConfigError
        if hasattr(config, 'ConfigError'):
            config_error_class = getattr(config, 'ConfigError')
            if config_error_class is not exceptions.ConfigError:
                print("  [FAIL] config.ConfigError is not exceptions.ConfigError (duplicate class)")
                return False
      
        print("  [OK] No duplicate ConfigError")
        return True
    except Exception as e:
        print(f"  [FAIL] ConfigError check: {e}")
        return False


def check_file_location() -> bool:
    """Verify package is installed, not from source."""
    try:
        import gmail_assistant
        location = Path(gmail_assistant.__file__).resolve()
        cwd = Path.cwd().resolve()
      
        # Should NOT be under current working directory's src/
        if location.is_relative_to(cwd / "src"):
            print(f"  [WARN] Importing from source: {location}")
            print("         This may mask packaging issues.")
            return True  # Warning only
        else:
            print(f"  [OK] Package location: {location}")
            return True
    except Exception as e:
        print(f"  [FAIL] Could not check location: {e}")
        return False


def main() -> int:
    print("=== Import Resolution Check ===")
    print()
  
    print("Checking environment...")
    is_safe, warnings = check_environment()
    if not is_safe:
        print()
        print("WARNING: Environment may produce unreliable results:")
        for w in warnings:
            print(f"  - {w}")
        print()
        print("For accurate results, run from outside the repo directory")
        print("or ensure PYTHONPATH does not include repo/src paths.")
        print()
  
    print()
    print("Checking imports...")
    imports_ok = check_imports()
  
    print()
    print("Checking version...")
    version_ok = check_version()
  
    print()
    print("Checking exception taxonomy...")
    exceptions_ok = check_exception_taxonomy()
  
    print()
    print("Checking for duplicate ConfigError...")
    no_duplicate_ok = check_no_duplicate_configerror()
  
    print()
    print("Checking package location...")
    location_ok = check_file_location()
  
    print()
    all_ok = imports_ok and version_ok and exceptions_ok and no_duplicate_ok and location_ok
  
    if all_ok:
        print("PASSED: All import resolution checks passed")
        return 0
    else:
        print("FAILED: Some import resolution checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
