#!/usr/bin/env python
"""
Aggregate test results from category runs and generate comprehensive report.
"""
import subprocess
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def run_test_category(category_path, category_name):
    """Run tests for a specific category with coverage."""
    print(f"\nRunning {category_name} tests...")

    cmd = [
        sys.executable, '-m', 'pytest',
        category_path,
        '--cov=gmail_assistant',
        '--cov-report=json',
        '--cov-report=term',
        '-v',
        '--tb=short',
        '--no-header'
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
        timeout=180
    )

    # Save output
    output_file = Path(f'tests/test_results/{category_name}_output.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr)

    # Parse results from output
    stats = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'warnings': 0,
        'duration': 0.0,
        'exit_code': result.returncode
    }

    # Extract stats from output using regex
    # Pattern: "15 failed, 604 passed, 22 warnings in 21.51s"
    summary_pattern = r'(?:(\d+) failed,?\s*)?(?:(\d+) passed,?\s*)?(?:(\d+) skipped,?\s*)?(?:(\d+) warnings?)?\s*in\s+([\d.]+)s'

    for line in result.stdout.split('\n'):
        match = re.search(summary_pattern, line)
        if match:
            failed, passed, skipped, warnings, duration = match.groups()
            stats['failed'] = int(failed) if failed else 0
            stats['passed'] = int(passed) if passed else 0
            stats['skipped'] = int(skipped) if skipped else 0
            stats['warnings'] = int(warnings) if warnings else 0
            stats['duration'] = float(duration) if duration else 0.0
            break

    # Move coverage.json to category-specific file
    coverage_file = Path('tests/test_results/coverage.json')
    if coverage_file.exists():
        category_cov = Path(f'tests/test_results/coverage_{category_name}.json')
        coverage_file.rename(category_cov)
        with open(category_cov, 'r') as f:
            cov_data = json.load(f)
            stats['coverage'] = cov_data.get('totals', {})

    print(f"  {category_name}: {stats['passed']} passed, {stats['failed']} failed, " +
          f"{stats['skipped']} skipped in {stats['duration']:.2f}s")

    return stats


def main():
    """Run all test categories and aggregate results."""
    print("=" * 80)
    print("Gmail Assistant - Comprehensive Test Suite Report")
    print("=" * 80)

    categories = [
        ('tests/unit/', 'unit'),
        ('tests/security/', 'security'),
        ('tests/integration/', 'integration'),
        ('tests/analysis/', 'analysis'),
    ]

    all_stats = {}

    for path, name in categories:
        if Path(path).exists():
            all_stats[name] = run_test_category(path, name)
        else:
            print(f"  {name}: SKIPPED (directory not found)")

    # Aggregate totals
    totals = {
        'passed': sum(s['passed'] for s in all_stats.values()),
        'failed': sum(s['failed'] for s in all_stats.values()),
        'skipped': sum(s['skipped'] for s in all_stats.values()),
        'warnings': sum(s['warnings'] for s in all_stats.values()),
        'duration': sum(s['duration'] for s in all_stats.values()),
        'total_tests': 0
    }
    totals['total_tests'] = totals['passed'] + totals['failed'] + totals['skipped']

    # Print summary
    print("\n" + "=" * 80)
    print("OVERALL TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests:  {totals['total_tests']}")
    print(f"  Passed:     {totals['passed']} ({totals['passed']/totals['total_tests']*100:.1f}%)")
    print(f"  Failed:     {totals['failed']} ({totals['failed']/totals['total_tests']*100:.1f}%)")
    print(f"  Skipped:    {totals['skipped']} ({totals['skipped']/totals['total_tests']*100:.1f}%)")
    print(f"  Warnings:   {totals['warnings']}")
    print(f"Total Time:   {totals['duration']:.2f}s")

    # Print category breakdown
    print("\n" + "=" * 80)
    print("CATEGORY BREAKDOWN")
    print("=" * 80)
    for name, stats in all_stats.items():
        category_total = stats['passed'] + stats['failed'] + stats['skipped']
        print(f"\n{name.upper()}:")
        print(f"  Tests:    {category_total}")
        print(f"  Passed:   {stats['passed']}")
        print(f"  Failed:   {stats['failed']}")
        print(f"  Skipped:  {stats['skipped']}")
        print(f"  Duration: {stats['duration']:.2f}s")
        if 'coverage' in stats:
            cov = stats['coverage']
            print(f"  Coverage: {cov.get('percent_covered', 0):.2f}%")

    # Save JSON report
    report = {
        'timestamp': datetime.now().isoformat(),
        'totals': totals,
        'categories': all_stats,
        'platform': {
            'python_version': sys.version,
            'system': sys.platform
        }
    }

    report_file = Path('tests/test_results/comprehensive_test_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: {report_file}")

    # Return exit code (0 if no failures)
    return 0 if totals['failed'] == 0 else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
