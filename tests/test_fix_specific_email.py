#!/usr/bin/env python3
"""
Test converting the specific problematic email to verify the fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.parsers.robust_eml_converter import RobustEMLConverter
from pathlib import Path
import tempfile

def test_fix_specific_email():
    """Test converting the specific problematic email"""

    print("=== TESTING FIXED EMAIL CONVERSION ===")

    converter = RobustEMLConverter()
    test_eml = Path("data/fetched_emails_fixed/2025/09/email_1995a8431b8b32a4_20250924_061830_134.eml")

    # Convert to markdown
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "fixed_email_test.md"
        success = converter.convert_eml_to_markdown(test_eml, output_path)

        if success:
            print("[SUCCESS] Conversion completed")

            # Read and analyze the output
            with open(output_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            print(f"[INFO] Markdown length: {len(markdown_content)} characters")

            # Check front matter
            if markdown_content.startswith('---'):
                parts = markdown_content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    body = parts[2].strip()

                    print(f"[INFO] Front matter length: {len(front_matter)} characters")
                    print(f"[INFO] Body length: {len(body)} characters")

                    # Check metadata quality
                    print(f"\n=== FRONT MATTER ANALYSIS ===")
                    required_fields = ['subject:', 'from:', 'to:', 'date:', 'message_id:']
                    for field in required_fields:
                        if field in front_matter and f"{field} ''" not in front_matter and f"{field} null" not in front_matter:
                            print(f"[OK] {field} populated")
                        else:
                            print(f"[FAIL] {field} missing or empty")

                    # Check body quality
                    print(f"\n=== BODY ANALYSIS ===")
                    if "The Prefect team is coming to a city near you" in body:
                        print(f"[OK] Proper email content found")
                    else:
                        print(f"[FAIL] Expected content not found")

                    if body.startswith('Received:') or body.startswith('ARC-'):
                        print(f"[FAIL] Body starts with transport headers")
                    else:
                        print(f"[OK] Body doesn't start with transport headers")

                    if len(body) > 500:
                        print(f"[OK] Substantial body content ({len(body)} chars)")
                    else:
                        print(f"[WARN] Short body content ({len(body)} chars)")

                    # Show samples
                    print(f"\n=== SAMPLE CONTENT ===")
                    print(f"Front matter sample:")
                    print(front_matter[:200])
                    print(f"\nBody sample (first 300 chars):")
                    print(body[:300])

                    # Overall assessment
                    print(f"\n=== OVERALL ASSESSMENT ===")
                    has_metadata = all(field in front_matter and f"{field} ''" not in front_matter for field in required_fields)
                    has_proper_content = "The Prefect team" in body and not body.startswith('Received:')

                    if has_metadata and has_proper_content:
                        print(f"[SUCCESS] EMAIL CONVERSION FULLY FIXED!")
                        print(f"[SUCCESS] Ready for production use")
                        return True
                    else:
                        print(f"[PARTIAL] Some issues remain")
                        return False

        else:
            print("[FAIL] Conversion failed")
            return False

if __name__ == "__main__":
    success = test_fix_specific_email()
    if success:
        print(f"\n*** SOLUTION VALIDATION: PASSED ***")
    else:
        print(f"\n*** SOLUTION VALIDATION: NEEDS MORE WORK ***")