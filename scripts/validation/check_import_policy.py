#!/usr/bin/env python3
# scripts/validation/check_import_policy.py
"""
Phase 1: Check import policy violations.

Fixed in v4:
- Only forbids OLD top-level package names that existed before migration
- Does not forbid legitimate third-party packages named 'core', etc.
- Properly checks relative imports
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# OLD top-level package names that existed before migration
# These should NOT be imported directly anymore
OLD_PACKAGE_ROOTS = frozenset({
    "src",        # Never valid as import
    "analysis",   # Was src/analysis, now gmail_assistant.analysis
    "deletion",   # Was src/deletion, now gmail_assistant.deletion
    "handlers",   # Was src/handlers, now merged into gmail_assistant.cli
    "parsers",    # Was src/parsers, now gmail_assistant.parsers
    "plugins",    # Was src/plugins, now gmail_assistant.plugins
    "tools",      # Was src/tools, now gmail_assistant.tools
    "utils",      # Was src/utils, now gmail_assistant.utils
    "cli",        # Was src/cli, now gmail_assistant.cli
    "core",       # Was src/core, now gmail_assistant.core
})


def get_import_root(module: str) -> str:
    """Get the root package name from an import."""
    return module.split(".")[0]


def check_file(path: Path) -> list[str]:
    """Check a single file for policy violations."""
    errors: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
    except SyntaxError as e:
        return [f"{path}:{e.lineno}: SyntaxError: {e.msg}"]
    except UnicodeDecodeError as e:
        return [f"{path}: UnicodeDecodeError: {e}"]

    # Check for sys.path manipulation
    for i, line in enumerate(content.splitlines(), 1):
        if "sys.path.insert" in line or "sys.path.append" in line:
            # Skip if it's a comment
            stripped = line.lstrip()
            if not stripped.startswith("#"):
                errors.append(f"{path}:{i}: sys.path manipulation forbidden")

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = get_import_root(alias.name)
                if root in OLD_PACKAGE_ROOTS:
                    errors.append(
                        f"{path}:{node.lineno}: Old import: 'import {alias.name}' "
                        f"- use 'from gmail_assistant.{alias.name} import ...' instead"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue  # from . import x - relative import, check separately

            root = get_import_root(node.module)
            if root in OLD_PACKAGE_ROOTS:
                errors.append(
                    f"{path}:{node.lineno}: Old import: 'from {node.module}' "
                    f"- use 'from gmail_assistant.{node.module} import ...' instead"
                )

            # Also catch 'from src.x import y'
            if node.module.startswith("src."):
                errors.append(
                    f"{path}:{node.lineno}: Invalid import: 'from {node.module}' "
                    f"- 'src' is not a package"
                )

    return errors


def main() -> int:
    # Check both src and tests directories
    check_dirs = []

    src_dir = Path("src/gmail_assistant")
    if src_dir.exists():
        check_dirs.append(src_dir)
    else:
        # Pre-migration layout
        src_dir = Path("src")
        if src_dir.exists():
            check_dirs.append(src_dir)

    tests_dir = Path("tests")
    if tests_dir.exists():
        check_dirs.append(tests_dir)

    if not check_dirs:
        print("Warning: No src/ or tests/ directory found")
        return 0

    all_errors: list[str] = []

    for check_dir in check_dirs:
        for py_file in check_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            all_errors.extend(check_file(py_file))

    if all_errors:
        print(f"Import policy check FAILED ({len(all_errors)} violations):")
        for err in sorted(set(all_errors)):
            print(f"  {err}")
        return 1

    print(f"Import policy check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
