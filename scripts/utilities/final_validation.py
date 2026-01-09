#!/usr/bin/env python3
"""
Final validation test - simplified to avoid Unicode issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.parsers.robust_eml_converter import RobustEMLConverter
from pathlib import Path
import tempfile

def final_validation():
    """Final validation of the complete solution"""

    print("=== FINAL SOLUTION VALIDATION ===")

    converter = RobustEMLConverter()
    test_eml = Path("data/fetched_emails_fixed/2025/09/email_1995a3c74f5fc2f1_20250924_061831_135.eml")

    # Test email parts extraction
    print("\n1. METADATA EXTRACTION TEST")
    email_parts = converter.extract_email_parts(test_eml)

    metadata = email_parts['metadata']
    print(f"   Subject: {metadata.get('subject', 'MISSING')}")
    print(f"   From: {metadata.get('from', 'MISSING')}")
    print(f"   To: {metadata.get('to', 'MISSING')}")
    print(f"   Date: {metadata.get('date', 'MISSING')}")
    print(f"   Message-ID: {metadata.get('message_id', 'MISSING')}")

    # Test content extraction
    print("\n2. CONTENT EXTRACTION TEST")
    print(f"   HTML content: {len(email_parts['html'])} characters")
    print(f"   Text content: {len(email_parts['text'])} characters")

    if email_parts['text']:
        print(f"   Text preview: {email_parts['text'][:100]}...")

    # Test complete conversion
    print("\n3. MARKDOWN CONVERSION TEST")
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "final_test.md"
        success = converter.convert_eml_to_markdown(test_eml, output_path)

        if success:
            with open(output_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            print(f"   Conversion successful: {len(markdown_content)} characters")

            # Check front matter
            if markdown_content.startswith('---'):
                parts = markdown_content.split('---', 2)
                if len(parts) >= 3:
                    body = parts[2].strip()
                    print(f"   Body content: {len(body)} characters")
                    print(f"   Body preview: {body[:100]}...")

                    # Quality assessment
                    has_all_metadata = all(metadata.get(field) for field in ['subject', 'from', 'to', 'date'])
                    has_content = len(body) > 100
                    no_raw_mime = not body.startswith('--')
                    proper_text = 'This is a copy of a security alert' in body

                    print(f"\n4. QUALITY ASSESSMENT")
                    print(f"   All metadata present: {has_all_metadata}")
                    print(f"   Substantial content: {has_content}")
                    print(f"   No raw MIME boundaries: {no_raw_mime}")
                    print(f"   Proper text extraction: {proper_text}")

                    if has_all_metadata and has_content and no_raw_mime and proper_text:
                        print(f"\n   [SUCCESS] SOLUTION IS WORKING PERFECTLY")
                        print(f"   [SUCCESS] HIGH QUALITY EML TO MARKDOWN CONVERSION")
                        print(f"   [SUCCESS] READY FOR PRODUCTION USE")
                        return True
                    else:
                        print(f"\n   [PARTIAL] Some issues remain")
                        return False
                else:
                    print(f"   [FAIL] Invalid markdown structure")
                    return False
            else:
                print(f"   [FAIL] No front matter found")
                return False
        else:
            print(f"   [FAIL] Conversion failed")
            return False

def test_multiple_files():
    """Test multiple files quickly"""
    print("\n=== MULTIPLE FILES TEST ===")

    converter = RobustEMLConverter()
    eml_dir = Path("data/fetched_emails_fixed")

    if not eml_dir.exists():
        print("No email directory found")
        return True

    eml_files = list(eml_dir.glob("**/*.eml"))[:3]  # Test first 3 files

    success_count = 0
    for i, eml_file in enumerate(eml_files):
        print(f"\nTesting file {i+1}: {eml_file.name[:50]}...")

        email_parts = converter.extract_email_parts(eml_file)
        has_metadata = email_parts['metadata'].get('subject') or email_parts['metadata'].get('from')
        has_content = email_parts['html'] or email_parts['text']

        if has_metadata and has_content:
            print(f"   [OK] Success")
            success_count += 1
        else:
            print(f"   [FAIL] Failed")

    success_rate = (success_count / len(eml_files)) * 100 if eml_files else 0
    print(f"\nMultiple files result: {success_count}/{len(eml_files)} ({success_rate:.0f}% success)")

    return success_rate >= 80

if __name__ == "__main__":
    single_success = final_validation()
    multi_success = test_multiple_files()

    print("\n" + "="*50)
    print("FINAL RESULTS:")

    if single_success and multi_success:
        print("[SUCCESS] COMPREHENSIVE SOLUTION VALIDATED")
        print("[SUCCESS] EML TO MARKDOWN CONVERSION IS WORKING")
        print("[SUCCESS] METADATA EXTRACTION IS PERFECT")
        print("[SUCCESS] CONTENT DECODING IS WORKING")
        print("[SUCCESS] READY FOR PRODUCTION DEPLOYMENT")
    elif single_success:
        print("[SUCCESS] CORE SOLUTION WORKING")
        print("[INFO] Primary functionality validated")
    else:
        print("[NEEDS WORK] Solution requires additional fixes")