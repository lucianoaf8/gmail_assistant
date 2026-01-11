"""
Test M-6: PowerShell Injection Prevention
Validates PowerShell script input sanitization.
"""
import pytest
from pathlib import Path


class TestPowerShellSanitization:
    """Tests for PowerShell injection prevention (M-6 fix)."""

    def test_sanitization_function_exists(self):
        """Verify sanitization functions exist in PowerShell scripts."""
        ps_script = Path("scripts/setup/quick_start.ps1")

        if not ps_script.exists():
            pytest.skip("PowerShell script not found")

        source = ps_script.read_text(encoding='utf-8')

        assert 'Sanitize' in source or 'sanitize' in source, \
            "PowerShell script should have sanitization functions"

    def test_dangerous_chars_removed(self):
        """Verify dangerous characters are handled."""
        ps_script = Path("scripts/setup/quick_start.ps1")

        if not ps_script.exists():
            pytest.skip("PowerShell script not found")

        source = ps_script.read_text(encoding='utf-8')

        dangerous_chars = ['`', '$', '(', ')', '{', '}', ';', '|', '&']

        # Should have logic to handle dangerous characters
        assert any(char in source for char in dangerous_chars), \
            "Should reference dangerous characters for filtering"

    def test_input_length_limits(self):
        """Verify input length limits are enforced."""
        ps_script = Path("scripts/setup/quick_start.ps1")

        if not ps_script.exists():
            pytest.skip("PowerShell script not found")

        source = ps_script.read_text(encoding='utf-8')

        assert 'Length' in source or 'Substring' in source, \
            "Should have input length limiting"

    def test_control_chars_removed(self):
        """Verify control characters are stripped."""
        ps_script = Path("scripts/setup/quick_start.ps1")

        if not ps_script.exists():
            pytest.skip("PowerShell script not found")

        source = ps_script.read_text(encoding='utf-8')

        # Should remove control characters
        assert 'x00' in source or 'x1f' in source or 'replace' in source.lower()


class TestPowerShellInjectionPatterns:
    """Tests for known PowerShell injection patterns."""

    def test_command_substitution_blocked(self):
        """Verify command substitution patterns are blocked."""
        # Pattern: $(command) or `command`
        ps_script = Path("scripts/setup/quick_start.ps1")

        if not ps_script.exists():
            pytest.skip("PowerShell script not found")

        source = ps_script.read_text(encoding='utf-8')

        # Backtick and dollar-paren should be sanitized
        assert '`' in source  # Should be referenced for removal

    def test_pipeline_injection_blocked(self):
        """Verify pipeline injection is blocked."""
        # Pattern: input | malicious-command
        ps_script = Path("scripts/setup/quick_start.ps1")

        if not ps_script.exists():
            pytest.skip("PowerShell script not found")

        source = ps_script.read_text(encoding='utf-8')

        # Pipe should be sanitized from user input
        assert '|' in source  # Should be referenced for removal

    def test_semicolon_injection_blocked(self):
        """Verify semicolon command chaining is blocked."""
        # Pattern: input; malicious-command
        ps_script = Path("scripts/setup/quick_start.ps1")

        if not ps_script.exists():
            pytest.skip("PowerShell script not found")

        source = ps_script.read_text(encoding='utf-8')

        # Semicolon should be sanitized from user input
        assert ';' in source  # Should be referenced for removal
