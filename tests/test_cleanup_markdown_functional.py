import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MARKDOWN = PROJECT_ROOT / 'backup_unread' / '2024' / '06' / '2024-06-17_143517_Your O_NET Web Services registration is complete_190269fb3948b6b6.md'
SCRIPT_PATH = PROJECT_ROOT / 'src' / 'tools' / 'cleanup_markdown.py'


@pytest.mark.skipif(not SAMPLE_MARKDOWN.exists(), reason='Sample markdown export is required for this test')
def test_cleanup_markdown_dry_run(tmp_path):
    working_copy = tmp_path / SAMPLE_MARKDOWN.name
    shutil.copy2(SAMPLE_MARKDOWN, working_copy)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), '--dry-run', str(working_copy)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert 'processed 1 file' in result.stdout.lower()
    assert 'dry-run mode' in result.stdout.lower()
