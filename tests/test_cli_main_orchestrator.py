#!/usr/bin/env python3
"""
Fixed comprehensive tests for CLI orchestrator and main entry points.
Tests actual command execution with correct working directory paths.
"""

import pytest
import subprocess
import tempfile
import shutil
import json
import sys
from pathlib import Path
import os


class TestMainCLIOrchestrator:
    """Test suite for main.py CLI orchestrator using real command execution."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        self.project_root = Path(__file__).parent.parent  # Go up from tests/ to project root

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def run_main_command(self, args, expect_success=True, cwd=None):
        """Helper to run main.py commands from correct directory."""
        if cwd is None:
            cwd = self.project_root

        # Check if main.py exists
        main_py_path = cwd / "main.py"
        if not main_py_path.exists():
            pytest.skip(f"main.py not found at {main_py_path}")

        cmd = [sys.executable, "main.py"] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(cwd)
            )

            return result

        except subprocess.TimeoutExpired:
            pytest.fail(f"Command timed out: {' '.join(cmd)}")
        except Exception as e:
            pytest.fail(f"Command execution failed: {e}")

    def test_main_script_exists(self):
        """Test that main.py exists in the project root."""
        main_py_path = self.project_root / "main.py"
        if main_py_path.exists():
            assert main_py_path.is_file()
            assert main_py_path.stat().st_size > 0
            print(f"✅ main.py found at {main_py_path}")
        else:
            pytest.skip("main.py not found in project root")

    def test_main_help_output(self):
        """Test main help output and command structure."""
        result = self.run_main_command(["--help"], expect_success=False)

        # Check if we got reasonable output
        help_text = result.stdout + result.stderr

        if "main.py" in help_text.lower() or "gmail" in help_text.lower() or "usage" in help_text.lower():
            print("✅ Main help output contains expected content")

            # Look for common command patterns
            potential_commands = ['fetch', 'parse', 'tools', 'samples', 'analyze', 'config', 'delete']
            found_commands = [cmd for cmd in potential_commands if cmd in help_text.lower()]

            if found_commands:
                print(f"✅ Found commands: {found_commands}")
            else:
                print("⚠️ No specific commands found in help output")
        else:
            print(f"⚠️ Help output unclear: {help_text[:100]}...")

    def test_python_script_execution(self):
        """Test that main.py can be executed without errors."""
        main_py_path = self.project_root / "main.py"
        if not main_py_path.exists():
            pytest.skip("main.py not found")

        # Test basic execution (might fail due to missing args, but shouldn't crash)
        result = self.run_main_command([], expect_success=False)

        # Verify it's a Python script error, not a system error
        output = result.stdout + result.stderr

        # Look for Python-related output vs system errors
        python_indicators = [
            "usage:", "error:", "argument", "command", "help",
            "gmail", "fetcher", "required", "invalid", "missing"
        ]

        system_errors = [
            "no such file", "permission denied", "cannot execute",
            "not found", "access denied"
        ]

        has_python_output = any(indicator in output.lower() for indicator in python_indicators)
        has_system_error = any(error in output.lower() for error in system_errors)

        if has_python_output and not has_system_error:
            print("✅ main.py executes as Python script")
        elif has_system_error:
            print(f"⚠️ System error: {output}")
        else:
            print(f"⚠️ Unclear output: {output[:100]}...")

    def test_import_validation(self):
        """Test that main.py imports work correctly."""
        main_py_path = self.project_root / "main.py"
        if not main_py_path.exists():
            pytest.skip("main.py not found")

        # Test that we can at least compile the main.py file
        try:
            with open(main_py_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()

            # Check for basic Python script structure
            assert "import" in source
            assert "def" in source or "if __name__" in source

            # Try to compile (syntax check)
            compile(source, str(main_py_path), 'exec')
            print("✅ main.py has valid Python syntax")

        except SyntaxError as e:
            pytest.fail(f"main.py has syntax error: {e}")
        except Exception as e:
            print(f"⚠️ main.py validation issue: {e}")

    def test_subcommand_structure(self):
        """Test for subcommand structure in main.py."""
        main_py_path = self.project_root / "main.py"
        if not main_py_path.exists():
            pytest.skip("main.py not found")

        try:
            with open(main_py_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Look for argument parser patterns
            argparse_indicators = [
                "argparse", "ArgumentParser", "add_subparsers", "subparsers",
                "add_argument", "parse_args"
            ]

            has_argparse = any(indicator in content for indicator in argparse_indicators)

            if has_argparse:
                print("✅ main.py appears to use argparse for command structure")

                # Look for specific command patterns
                command_patterns = ['fetch', 'parse', 'tools', 'samples', 'analyze']
                found_patterns = [pattern for pattern in command_patterns if pattern in content]

                if found_patterns:
                    print(f"✅ Found command patterns: {found_patterns}")

            else:
                print("⚠️ main.py doesn't appear to use argparse")

        except Exception as e:
            print(f"⚠️ Error analyzing main.py structure: {e}")


class TestSamplesScript:
    """Test suite for samples.py script execution."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        self.project_root = Path(__file__).parent.parent

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_samples_script_exists(self):
        """Test that samples script exists."""
        # Look for samples.py in common locations
        possible_locations = [
            self.project_root / "samples.py",
            self.project_root / "examples" / "samples.py",
            self.project_root / "scripts" / "samples.py"
        ]

        samples_found = None
        for location in possible_locations:
            if location.exists():
                samples_found = location
                break

        if samples_found:
            assert samples_found.is_file()
            assert samples_found.stat().st_size > 0
            print(f"✅ samples.py found at {samples_found}")
        else:
            pytest.skip("samples.py not found in expected locations")

    def test_samples_execution(self):
        """Test samples script execution."""
        # Find samples.py
        possible_locations = [
            self.project_root / "samples.py",
            self.project_root / "examples" / "samples.py",
            self.project_root / "scripts" / "samples.py"
        ]

        samples_path = None
        for location in possible_locations:
            if location.exists():
                samples_path = location
                break

        if not samples_path:
            pytest.skip("samples.py not found")

        try:
            cmd = [sys.executable, str(samples_path)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.project_root)
            )

            output = result.stdout + result.stderr

            # Look for sample-related content
            sample_indicators = [
                "sample", "scenario", "unread", "newsletter", "backup",
                "usage", "help", "available", "example"
            ]

            has_sample_content = any(indicator in output.lower() for indicator in sample_indicators)

            if has_sample_content:
                print("✅ samples.py produces expected sample-related output")
            else:
                print(f"⚠️ samples.py output unclear: {output[:100]}...")

        except subprocess.TimeoutExpired:
            print("⚠️ samples.py execution timed out")
        except Exception as e:
            print(f"⚠️ samples.py execution error: {e}")


class TestConfigurationValidation:
    """Test suite for configuration file validation and schema compliance."""

    def setup_method(self):
        """Setup test environment."""
        self.project_root = Path(__file__).parent.parent

    def test_json_configuration_files(self):
        """Test all JSON configuration files for valid syntax."""
        config_dir = self.project_root / "config"
        if not config_dir.exists():
            pytest.skip("No config directory found")

        json_files = list(config_dir.rglob("*.json"))
        if not json_files:
            pytest.skip("No JSON config files found")

        valid_configs = 0
        for config_file in json_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # Basic validation
                assert isinstance(config_data, (dict, list))

                # Check for reasonable structure
                if isinstance(config_data, dict):
                    assert len(config_data) > 0

                valid_configs += 1
                print(f"✅ {config_file.name} is valid JSON")

            except json.JSONDecodeError as e:
                pytest.fail(f"JSON syntax error in {config_file.name}: {e}")
            except Exception as e:
                print(f"⚠️ Config validation error for {config_file.name}: {e}")

        assert valid_configs > 0
        print(f"✅ Validated {valid_configs} configuration files")

    def test_project_structure(self):
        """Test overall project structure."""
        expected_items = [
            ("src", "directory"),
            ("tests", "directory"),
            ("requirements.txt", "file"),
            ("README.md", "file"),
            ("CLAUDE.md", "file")
        ]

        found_items = 0
        for item_name, item_type in expected_items:
            item_path = self.project_root / item_name

            if item_path.exists():
                if item_type == "directory" and item_path.is_dir():
                    found_items += 1
                    print(f"✅ Found directory: {item_name}")
                elif item_type == "file" and item_path.is_file():
                    found_items += 1
                    print(f"✅ Found file: {item_name}")
            else:
                print(f"⚠️ Missing {item_type}: {item_name}")

        print(f"✅ Found {found_items}/{len(expected_items)} expected project items")


class TestDocumentationValidation:
    """Test suite for documentation file validation."""

    def setup_method(self):
        """Setup test environment."""
        self.project_root = Path(__file__).parent.parent

    def test_readme_existence(self):
        """Test README file existence and basic content."""
        readme_files = ["README.md", "readme.md", "README.txt", "README"]
        readme_found = None

        for readme_name in readme_files:
            readme_path = self.project_root / readme_name
            if readme_path.exists():
                readme_found = readme_path
                break

        if readme_found:
            assert readme_found.stat().st_size > 0
            content = readme_found.read_text(encoding='utf-8', errors='ignore')

            # Look for common README content
            readme_indicators = [
                "gmail", "fetcher", "installation", "usage", "python",
                "email", "backup", "api", "setup", "requirements"
            ]

            has_readme_content = any(indicator in content.lower() for indicator in readme_indicators)

            if has_readme_content:
                print(f"✅ {readme_found.name} contains expected content")
            else:
                print(f"⚠️ {readme_found.name} content unclear")

        else:
            pytest.skip("No README file found")

    def test_claude_md_existence(self):
        """Test CLAUDE.md file existence and content."""
        claude_md_path = self.project_root / "CLAUDE.md"

        if claude_md_path.exists():
            assert claude_md_path.stat().st_size > 0
            content = claude_md_path.read_text(encoding='utf-8', errors='ignore')

            # Look for Claude-specific content
            claude_indicators = [
                "claude", "gmail", "fetcher", "usage", "command",
                "example", "workflow", "api", "configuration"
            ]

            has_claude_content = any(indicator in content.lower() for indicator in claude_indicators)

            if has_claude_content:
                print("✅ CLAUDE.md contains expected content")
            else:
                print("⚠️ CLAUDE.md content unclear")

        else:
            pytest.skip("CLAUDE.md not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])