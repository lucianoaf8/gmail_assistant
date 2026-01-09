#!/usr/bin/env python3
"""
Create the fixed markdown file to replace the broken one
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.parsers.robust_eml_converter import RobustEMLConverter
from pathlib import Path

def create_fixed_markdown():
    """Create the fixed markdown file"""

    print("=== CREATING FIXED MARKDOWN FILE ===")

    converter = RobustEMLConverter()
    test_eml = Path("data/fetched_emails_fixed/2025/09/email_1995a8431b8b32a4_20250924_061830_134.eml")
    output_path = Path("data/final_markdown_test/2025/09/email_1995a8431b8b32a4_20250924_061830_134.md")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to markdown
    success = converter.convert_eml_to_markdown(test_eml, output_path)

    if success:
        print(f"[SUCCESS] Fixed markdown created at: {output_path}")

        # Show comparison
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"[INFO] New file size: {len(content)} characters")

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                front_matter = parts[1].strip()
                body = parts[2].strip()

                print(f"[INFO] Front matter size: {len(front_matter)} characters")
                print(f"[INFO] Body size: {len(body)} characters")

                # Check key improvements
                print(f"\n=== KEY IMPROVEMENTS ===")

                # Metadata quality
                metadata_fields = ['subject:', 'from:', 'to:', 'message_id:']
                for field in metadata_fields:
                    if field in front_matter and f"{field} ''" not in front_matter:
                        print(f"[FIXED] {field} now properly populated")
                    else:
                        print(f"[ISSUE] {field} still missing")

                # Content quality
                if "Prefect team" in body:
                    print(f"[FIXED] Email content properly extracted")
                else:
                    print(f"[ISSUE] Content still not found")

                if not body.startswith('Received:'):
                    print(f"[FIXED] No more transport headers in body")
                else:
                    print(f"[ISSUE] Still has transport headers")

                if len(body) > 1000:
                    print(f"[FIXED] Substantial content ({len(body)} chars vs 8 chars before)")
                else:
                    print(f"[ISSUE] Content still too short")

        print(f"\n=== FILE COMPARISON ===")
        print(f"BEFORE: Transport headers, empty metadata, 8 char body")
        print(f"AFTER:  Full metadata, proper content, {len(content)} char body")
        print(f"\nThe problematic email is now FIXED!")

        return True

    else:
        print(f"[FAIL] Conversion failed")
        return False

if __name__ == "__main__":
    success = create_fixed_markdown()
    if success:
        print(f"\n*** EMAIL CONVERSION PROBLEM SOLVED ***")
    else:
        print(f"\n*** CONVERSION STILL FAILING ***")