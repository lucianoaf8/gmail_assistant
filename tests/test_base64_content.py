#!/usr/bin/env python3
"""
Test base64 content decoding specifically
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.parsers.robust_eml_converter import RobustEMLConverter
from pathlib import Path
import base64

def test_base64_decoding():
    """Test base64 content decoding from EML file"""

    print("=== BASE64 CONTENT DECODING TEST ===")

    converter = RobustEMLConverter()
    test_eml = Path("data/fetched_emails_fixed/2025/09/email_1995a3c74f5fc2f1_20250924_061831_135.eml")

    # Extract email parts
    email_parts = converter.extract_email_parts(test_eml)

    print(f"HTML content preview (first 200 chars):")
    print(repr(email_parts['html'][:200]))

    # Check if the HTML content contains base64
    if 'VGhpcyBpcyBhIGNvcHkgb2YgYSBzZWN1cml0eSBhbGVydCBzZW50IH' in email_parts['html']:
        print("\nDetected base64 content in HTML - testing manual decoding:")

        # Extract the base64 content
        lines = email_parts['html'].split('\n')
        base64_lines = []
        in_base64_section = False

        for line in lines:
            line = line.strip()
            if line and line.startswith('VG') and len(line) > 20:  # Looks like base64
                base64_lines.append(line)
            elif base64_lines and line and not line.startswith('--'):
                base64_lines.append(line)
            elif base64_lines:
                break

        if base64_lines:
            base64_content = ''.join(base64_lines)
            print(f"Found base64 content ({len(base64_content)} chars)")

            try:
                decoded = base64.b64decode(base64_content)
                decoded_text = decoded.decode('utf-8', errors='ignore')
                print(f"Decoded content ({len(decoded_text)} chars):")
                print(decoded_text)

                print("\n[SUCCESS] Base64 decoding works - MIME extraction needs fixing")
                return True
            except Exception as e:
                print(f"Failed to decode base64: {e}")
                return False
        else:
            print("No base64 content found")
            return False
    else:
        print("No base64 content detected")
        return True

if __name__ == "__main__":
    test_base64_decoding()