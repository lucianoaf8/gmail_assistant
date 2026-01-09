import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_python_command(*args, cwd=PROJECT_ROOT):
    result = subprocess.run(
        [sys.executable, *map(str, args)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command {' '.join(map(str, args))} failed with code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout


def test_main_help_displays_title():
    output = run_python_command('main.py', '--help')
    assert 'Gmail Fetcher Suite' in output


def test_main_fetch_help_lists_required_query_argument():
    output = run_python_command('main.py', 'fetch', '--help')
    assert '--query QUERY' in output


def test_main_delete_help_mentions_dry_run_default():
    output = run_python_command('main.py', 'delete', '--help')
    assert 'dry-run' in output.lower()


def test_cleanup_markdown_help_lists_examples():
    script = PROJECT_ROOT / 'src' / 'tools' / 'cleanup_markdown.py'
    output = run_python_command(script, '--help')
    assert 'Cleanup messy Gmail-exported Markdown files.' in output
