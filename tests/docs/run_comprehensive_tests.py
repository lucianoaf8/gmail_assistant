#!/usr/bin/env python3
"""
Comprehensive test runner for Gmail Fetcher test suite.
Demonstrates current test coverage and working functionality.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description, timeout=60):
    """Run a command and return results."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd()
        )

        end_time = time.time()
        duration = end_time - start_time

        print(f"[TIME] Execution time: {duration:.2f} seconds")

        if result.returncode == 0:
            print(f"[SUCCESS] {description}")
        else:
            print(f"[FAILED] {description}")
            print(f"Return code: {result.returncode}")

        # Always show output for transparency
        if result.stdout:
            print("\n[STDOUT]:")
            print(result.stdout)

        if result.stderr:
            print("\n[STDERR]:")
            print(result.stderr)

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {description} exceeded {timeout} seconds")
        return False, "", f"Timeout after {timeout} seconds"
    except Exception as e:
        print(f"[ERROR] {description} failed with exception: {e}")
        return False, "", str(e)

def main():
    """Run comprehensive test demonstration."""
    print("GMAIL FETCHER COMPREHENSIVE TEST SUITE")
    print("======================================")
    print("Demonstrating current test coverage and working functionality")

    # Track results
    results = {}

    # 1. Core Simple Tests (Always work)
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/test_core_simple.py", "-v"],
        "Core Functionality Tests (100% reliable)"
    )
    results["core_simple"] = success

    # 2. Email Processing Tests (Work with or without real data)
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/test_email_processing_comprehensive.py", "-v"],
        "Email Processing Tests (EML/Markdown conversion)"
    )
    results["email_processing"] = success

    # 3. Gmail API Tests (May skip if no credentials)
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/test_gmail_api_integration_comprehensive.py", "-v"],
        "Gmail API Integration Tests (requires credentials.json)"
    )
    results["gmail_api"] = success

    # 4. Coverage Analysis on Working Tests
    working_tests = [
        "tests/test_core_simple.py",
        "tests/test_email_processing_comprehensive.py"
    ]

    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest"] + working_tests + [
            "--cov=src", "--cov-report=term-missing", "--tb=no", "-q"
        ],
        "Coverage Analysis on Working Tests"
    )
    results["coverage"] = success

    # 5. Classification Tests (Partial success expected)
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/test_email_classification_comprehensive.py", "-v", "--tb=short"],
        "Email Classification Tests (62% success rate expected)"
    )
    results["classification"] = success

    # 6. Test Collection Summary
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/"],
        "Test Collection Summary (count all tests)"
    )
    results["collection"] = success

    # Print Summary
    print(f"\n{'='*60}")
    print("TEST EXECUTION SUMMARY")
    print(f"{'='*60}")

    test_descriptions = {
        "core_simple": "Core Functionality (10 tests)",
        "email_processing": "Email Processing (9 tests)",
        "gmail_api": "Gmail API Integration (12 tests)",
        "coverage": "Coverage Analysis",
        "classification": "Classification Tests (13 tests)",
        "collection": "Test Discovery"
    }

    passed_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    for key, success in results.items():
        status = "[PASSED]" if success else "[FAILED]"
        description = test_descriptions.get(key, key)
        print(f"{status} {description}")

    print(f"\nOverall Success Rate: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")

    # Recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")

    if results.get("core_simple"):
        print("[OK] Core functionality tests are working perfectly")
    else:
        print("[ISSUE] Core functionality tests need attention")

    if results.get("email_processing"):
        print("[OK] Email processing pipeline is fully validated")
    else:
        print("[ISSUE] Email processing tests need debugging")

    if results.get("gmail_api"):
        print("[OK] Gmail API integration is working (credentials available)")
    else:
        print("[WARN] Gmail API tests skipped (no credentials.json) or failed")

    if results.get("classification"):
        print("[PARTIAL] Classification tests partially working")
    else:
        print("[FIX] Classification tests need method signature fixes")

    print(f"\nFor detailed documentation, see:")
    print(f"   - tests/docs/TESTING_STATUS_AND_ROADMAP.md")
    print(f"   - tests/docs/QUICK_TEST_GUIDE.md")

    # Next steps
    print(f"\nNEXT STEPS:")
    print(f"   1. Fix classification test method signatures")
    print(f"   2. Add parser comprehensive tests")
    print(f"   3. Expand core module coverage")
    print(f"   4. Implement database operation tests")

if __name__ == "__main__":
    main()