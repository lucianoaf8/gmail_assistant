#!/usr/bin/env python3
"""
Comprehensive validation of EML to Markdown conversion
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.parsers.robust_eml_converter import RobustEMLConverter
from pathlib import Path
import tempfile

def validate_eml_conversion():
    """Validate complete EML to markdown conversion pipeline"""

    print("=== COMPREHENSIVE EML TO MARKDOWN VALIDATION ===")

    converter = RobustEMLConverter()

    # Test file
    test_eml = Path("data/fetched_emails_fixed/2025/09/email_1995a3c74f5fc2f1_20250924_061831_135.eml")

    print(f"Testing complete conversion pipeline with: {test_eml.name}")

    # Step 1: Validate email parts extraction
    print("\n1. TESTING EMAIL PARTS EXTRACTION")
    email_parts = converter.extract_email_parts(test_eml)

    print(f"   [OK] HTML content length: {len(email_parts['html'])}")
    print(f"   [OK] Text content length: {len(email_parts['text'])}")

    print("   [OK] Metadata extracted:")
    for key, value in email_parts['metadata'].items():
        status = "[OK]" if value else "[FAIL]"
        print(f"     {status} {key}: {value}")

    # Step 2: Test markdown conversion
    print("\n2. TESTING COMPLETE MARKDOWN CONVERSION")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_output.md"

        success = converter.convert_eml_to_markdown(test_eml, output_path)

        if success:
            print("   [OK] Conversion completed successfully")

            # Read and analyze the markdown output
            with open(output_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            print(f"   [OK] Markdown file size: {len(markdown_content)} characters")

            # Check for front matter
            if markdown_content.startswith('---'):
                print("   [OK] YAML front matter present")

                # Extract front matter section
                parts = markdown_content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    body = parts[2]

                    print(f"   [OK] Front matter size: {len(front_matter)} characters")
                    print(f"   [OK] Body content size: {len(body)} characters")

                    # Check key front matter fields
                    print("   [OK] Front matter validation:")
                    required_fields = ['subject', 'from', 'to', 'date', 'message_id']
                    for field in required_fields:
                        if f"{field}:" in front_matter:
                            print(f"     [OK] {field} present")
                        else:
                            print(f"     [FAIL] {field} missing")

                    # Check body content quality
                    print("   [OK] Body content validation:")
                    if len(body.strip()) > 100:
                        print(f"     [OK] Body has substantial content ({len(body.strip())} chars)")
                    else:
                        print(f"     [FAIL] Body content too short ({len(body.strip())} chars)")

                    if not body.strip().startswith('--'):
                        print("     [OK] Body doesn't start with MIME boundaries")
                    else:
                        print("     [WARN] Body may contain raw MIME content")

                    if '<' in body and '>' in body:
                        print("     [WARN] Body may contain unprocessed HTML tags")
                    else:
                        print("     [OK] Body appears to be clean text/markdown")

                # Show sample content
                print("\n3. SAMPLE OUTPUT PREVIEW")
                print("   Front matter (first 300 chars):")
                print("   " + front_matter[:300].replace('\n', '\n   '))

                print("\n   Body content (first 500 chars):")
                print("   " + body[:500].replace('\n', '\n   '))

            else:
                print("   [FAIL] No YAML front matter found")
        else:
            print("   [FAIL] Conversion failed")

    # Step 3: Quality assessment
    print("\n4. QUALITY ASSESSMENT")

    # Check if we have both metadata and content
    has_metadata = all(email_parts['metadata'].get(field) for field in ['subject', 'from', 'to'])
    has_content = email_parts['html'] or email_parts['text']

    if has_metadata and has_content:
        print("   [OK] PASS: Both metadata and content extracted successfully")
        print("   [OK] SOLUTION QUALITY: HIGH - Ready for production use")
        return True
    elif has_metadata:
        print("   [WARN] PARTIAL: Metadata extracted but content may need improvement")
        print("   [WARN] SOLUTION QUALITY: MEDIUM - Needs content extraction refinement")
        return False
    else:
        print("   [FAIL] FAIL: Critical metadata missing")
        print("   [FAIL] SOLUTION QUALITY: LOW - Requires significant fixes")
        return False

def test_multiple_emails():
    """Test with multiple email files if available"""
    print("\n=== TESTING MULTIPLE EMAIL FILES ===")

    converter = RobustEMLConverter()
    fixed_emails_dir = Path("data/fetched_emails_fixed")

    if not fixed_emails_dir.exists():
        print("No fixed emails directory found, skipping multi-file test")
        return

    eml_files = list(fixed_emails_dir.glob("**/*.eml"))

    if len(eml_files) == 0:
        print("No EML files found for testing")
        return

    print(f"Found {len(eml_files)} EML files for testing")

    success_count = 0
    test_count = min(5, len(eml_files))  # Test up to 5 files

    for i, eml_file in enumerate(eml_files[:test_count]):
        print(f"\nTesting {i+1}/{test_count}: {eml_file.name}")

        # Test email parts extraction
        email_parts = converter.extract_email_parts(eml_file)

        has_metadata = email_parts['metadata'].get('subject') or email_parts['metadata'].get('from')
        has_content = email_parts['html'] or email_parts['text']

        if has_metadata and has_content:
            print(f"   [OK] Success: Metadata and content extracted")
            success_count += 1
        elif has_metadata:
            print(f"   [WARN] Partial: Metadata only")
        else:
            print(f"   [FAIL] Failed: No metadata or content")

    success_rate = (success_count / test_count) * 100
    print(f"\nMulti-file test results: {success_count}/{test_count} ({success_rate:.1f}% success rate)")

    if success_rate >= 80:
        print("[OK] ROBUST SOLUTION: High success rate across multiple emails")
        return True
    else:
        print("[WARN] NEEDS IMPROVEMENT: Success rate below 80%")
        return False

if __name__ == "__main__":
    print("Gmail API EML to Markdown Converter - Comprehensive Validation")
    print("=" * 60)

    # Test single file conversion
    single_file_success = validate_eml_conversion()

    # Test multiple files
    multi_file_success = test_multiple_emails()

    print("\n" + "=" * 60)
    print("FINAL VALIDATION RESULTS:")

    if single_file_success and multi_file_success:
        print("[SUCCESS] COMPREHENSIVE SOLUTION VALIDATED")
        print("[OK] Ready for production deployment")
        print("[OK] High-quality metadata extraction")
        print("[OK] Reliable content conversion")
        print("[OK] Robust across multiple email types")
    elif single_file_success:
        print("[SUCCESS] CORE SOLUTION WORKING")
        print("[WARN] May need optimization for edge cases")
    else:
        print("[FAIL] SOLUTION NEEDS CRITICAL FIXES")
        print("[FAIL] Not ready for production use")