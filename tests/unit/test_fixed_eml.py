#!/usr/bin/env python3
"""
Test if the fixed EML file can be parsed correctly
"""

import email
import email.policy

def test_eml_parsing(eml_file):
    """Test email parsing on fixed file"""
    print(f"Testing EML parsing on: {eml_file}")

    with open(eml_file, 'rb') as f:
        email_bytes = f.read()

    # Parse with default policy
    msg = email.message_from_bytes(email_bytes, policy=email.policy.default)

    print(f"Headers found: {len(msg.items())}")
    print(f"Subject: '{msg.get('Subject', 'NONE')}'")
    print(f"From: '{msg.get('From', 'NONE')}'")
    print(f"Date: '{msg.get('Date', 'NONE')}'")
    print(f"To: '{msg.get('To', 'NONE')}'")
    print(f"Is multipart: {msg.is_multipart()}")

    if len(msg.items()) > 5:
        print("[SUCCESS] Email parsing is now working correctly!")
        return True
    else:
        print("[FAILED] Email parsing still not working")
        return False

if __name__ == "__main__":
    test_eml_parsing("test_fixed.eml")