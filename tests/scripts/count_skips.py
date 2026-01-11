#!/usr/bin/env python3
"""Count and report all pytest skip calls in test suite."""

import re
from pathlib import Path

def count_skips():
    """Count all skip patterns in test files."""
    test_dir = Path(__file__).parent.parent

    skip_patterns = [
        (r'pytest\.skip\(', 'pytest.skip()'),
        (r'@pytest\.mark\.skip\b', '@pytest.mark.skip'),
        (r'@pytest\.mark\.skipif\(', '@pytest.mark.skipif'),
        (r'pytestmark\s*=\s*pytest\.mark\.skipif', 'pytestmark skipif'),
    ]

    results = {}
    total_skips = 0

    for test_file in test_dir.rglob("*.py"):
        if test_file.name.startswith("test_"):
            content = test_file.read_text(encoding='utf-8')
            file_skips = []

            for pattern, name in skip_patterns:
                matches = list(re.finditer(pattern, content))
                if matches:
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        file_skips.append((line_num, name))
                        total_skips += 1

            if file_skips:
                rel_path = test_file.relative_to(test_dir)
                results[str(rel_path)] = sorted(file_skips)

    # Print report
    print(f"SKIP ANALYSIS REPORT")
    print(f"=" * 80)
    print(f"\nTotal skip calls found: {total_skips}")
    print(f"Files with skips: {len(results)}")
    print(f"\nDETAILS:\n")

    for file_path, skips in sorted(results.items()):
        print(f"\n{file_path}:")
        for line_num, skip_type in skips:
            print(f"  Line {line_num}: {skip_type}")

    return total_skips, results

if __name__ == "__main__":
    total, _ = count_skips()
    print(f"\n" + "=" * 80)
    print(f"TOTAL SKIPS TO FIX: {total}")
