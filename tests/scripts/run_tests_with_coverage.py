#!/usr/bin/env python
"""
Workaround script to run pytest with coverage avoiding Python 3.13 I/O bugs.
"""
import subprocess
import sys
import json
from pathlib import Path

def main():
    """Run pytest with coverage and save results."""

    # Run pytest with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '--cov=gmail_assistant',
        '--cov-report=term',
        '--cov-report=html',
        '--cov-report=json',
        '--tb=short',
        '-v'
    ]

    print("Running test suite with coverage...")
    print(f"Command: {' '.join(cmd)}\n")

    # Run with captured output
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
        timeout=300
    )

    # Save output to files
    output_file = Path('tests/test_results/pytest_output.txt')
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n\n=== STDERR ===\n")
        f.write(result.stderr)
        f.write(f"\n\n=== EXIT CODE: {result.returncode} ===\n")

    # Print summary
    print(f"Exit code: {result.returncode}")
    print(f"Output saved to: {output_file}")

    # Print last part of stdout (summary)
    if result.stdout:
        lines = result.stdout.split('\n')
        summary_start = -50
        for i in range(len(lines) - 1, max(0, len(lines) - 100), -1):
            if '=====' in lines[i] and ('passed' in lines[i] or 'failed' in lines[i]):
                summary_start = i - 5
                break
        print("\n=== TEST SUMMARY ===")
        print('\n'.join(lines[summary_start:]))

    # Check if coverage.json was created
    coverage_file = Path('tests/test_results/coverage.json')
    if coverage_file.exists():
        with open(coverage_file, 'r') as f:
            cov_data = json.load(f)
            totals = cov_data.get('totals', {})
            print(f"\n=== COVERAGE SUMMARY ===")
            print(f"Coverage: {totals.get('percent_covered', 0):.2f}%")
            print(f"Statements: {totals.get('num_statements', 0)}")
            print(f"Missing: {totals.get('missing_lines', 0)}")
            print(f"Excluded: {totals.get('excluded_lines', 0)}")

    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
