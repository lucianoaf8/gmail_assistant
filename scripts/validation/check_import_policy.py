#!/usr/bin/env python3
"""
Import policy checker - validates imports follow post-migration conventions.

Checks:
1. No sys.path manipulation
2. No imports from old package roots
3. No invalid relative imports
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    file: Path
    line: int
    message: str


# Old package roots that should not be imported directly
OLD_PACKAGE_ROOTS = frozenset({
    "src",
    "analysis",
    "deletion",
    "handlers",
    "parsers",
    "plugins",
    "tools",
    "utils",
    "core",
    "cli",
})

# These are never valid as import roots
INVALID_IMPORT_ROOTS = frozenset({"src"})


def check_file(path: Path) -> list[Violation]:
    """Check a single Python file for import policy violations."""
    violations = []
  
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return [Violation(path, 0, f"Could not read file: {e}")]
  
    # Check for sys.path manipulation
    if "sys.path.insert" in content or "sys.path.append" in content:
        for i, line in enumerate(content.splitlines(), 1):
            if "sys.path.insert" in line or "sys.path.append" in line:
                # Skip comments
                stripped = line.lstrip()
                if not stripped.startswith("#"):
                    violations.append(Violation(
                        path, i,
                        "sys.path manipulation is forbidden"
                    ))
  
    # Parse AST for import analysis
    try:
        tree = ast.parse(content, filename=str(path))
    except SyntaxError as e:
        return violations + [Violation(path, e.lineno or 0, f"Syntax error: {e}")]
  
    for node in ast.walk(tree):
        # Check Import statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in INVALID_IMPORT_ROOTS:
                    violations.append(Violation(
                        path, node.lineno,
                        f"Invalid import root '{root}' - 'src' is never importable"
                    ))
                elif root in OLD_PACKAGE_ROOTS:
                    violations.append(Violation(
                        path, node.lineno,
                        f"Old import '{alias.name}' - use 'gmail_assistant.{alias.name}'"
                    ))
      
        # Check ImportFrom statements
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in INVALID_IMPORT_ROOTS:
                    violations.append(Violation(
                        path, node.lineno,
                        f"Invalid import root '{root}' - 'src' is never importable"
                    ))
                elif root in OLD_PACKAGE_ROOTS:
                    violations.append(Violation(
                        path, node.lineno,
                        f"Old import 'from {node.module}' - use 'from gmail_assistant.{node.module}'"
                    ))
          
            # Check relative imports
            if node.level > 0:
                # Relative imports are only allowed within src/gmail_assistant
                try:
                    rel = path.relative_to(Path.cwd() / "src" / "gmail_assistant")
                    # Check that relative import doesn't escape package
                    depth = len(rel.parts) - 1  # -1 for the file itself
                    if node.level > depth:
                        violations.append(Violation(
                            path, node.lineno,
                            f"Relative import level {node.level} escapes package boundary"
                        ))
                except ValueError:
                    # File not in src/gmail_assistant - relative imports not allowed
                    violations.append(Violation(
                        path, node.lineno,
                        "Relative imports only allowed within src/gmail_assistant/"
                    ))
  
    return violations


def main() -> int:
    """Run import policy checks on all Python files."""
    repo_root = Path.cwd()
  
    # Directories to check
    check_dirs = [
        repo_root / "src",
        repo_root / "tests",
        repo_root / "scripts",
    ]
  
    # Exclusions
    exclude_patterns = {
        "__pycache__",
        ".venv",
        "venv",
        ".git",
        "dist",
        "build",
    }
  
    all_violations: list[Violation] = []
    files_checked = 0
  
    for check_dir in check_dirs:
        if not check_dir.exists():
            continue
      
        for py_file in check_dir.rglob("*.py"):
            # Skip excluded directories
            if any(excl in py_file.parts for excl in exclude_patterns):
                continue
          
            violations = check_file(py_file)
            all_violations.extend(violations)
            files_checked += 1
  
    # Report results
    print(f"Checked {files_checked} files")
    print()
  
    if all_violations:
        print(f"Found {len(all_violations)} violations:")
        print()
        for v in all_violations:
            rel_path = v.file.relative_to(repo_root) if v.file.is_relative_to(repo_root) else v.file
            print(f"  {rel_path}:{v.line}: {v.message}")
        print()
        print("FAILED: Import policy violations found")
        return 1
    else:
        print("PASSED: No import policy violations")
        return 0


if __name__ == "__main__":
    sys.exit(main())
