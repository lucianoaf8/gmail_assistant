#!/usr/bin/env python3
"""
Fix malformed EML files by correcting line endings and structure

The Gmail API provides proper RFC822 format, but our UTF-8 decoding corrupted line endings.
This utility fixes existing EML files and provides proper EML generation for future use.
"""

import base64
import logging
from pathlib import Path
import re
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_line_endings(content: str) -> str:
    """
    Fix corrupted line endings in EML content

    Args:
        content: EML content with potentially corrupted line endings

    Returns:
        Fixed EML content with proper RFC822 line endings
    """
    # Replace various corrupted line ending patterns

    # Fix double carriage returns: \r\r\n -> \r\n
    content = re.sub(r'\r\r\n', '\r\n', content)

    # Fix standalone \r -> \r\n
    content = re.sub(r'\r(?!\n)', '\r\n', content)

    # Fix standalone \n -> \r\n (but not if already \r\n)
    content = re.sub(r'(?<!\r)\n', '\r\n', content)

    return content

def validate_eml_structure(content: str) -> bool:
    """
    Validate that EML content has proper RFC822 structure

    Args:
        content: EML content to validate

    Returns:
        True if structure is valid
    """
    lines = content.split('\r\n')

    # Should have at least some headers
    if len(lines) < 5:
        return False

    # First line should be a header
    if ':' not in lines[0]:
        return False

    # Should have header/body separator (blank line)
    blank_line_found = False
    for line in lines:
        if line.strip() == '':
            blank_line_found = True
            break

    return blank_line_found

def fix_eml_file(input_path: Path, output_path: Path) -> bool:
    """
    Fix a single EML file

    Args:
        input_path: Path to malformed EML file
        output_path: Path for fixed EML file

    Returns:
        True if successful
    """
    try:
        logger.info(f"Fixing {input_path.name}...")

        # Read the malformed file
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Fix line endings
        fixed_content = fix_line_endings(content)

        # Validate structure
        if not validate_eml_structure(fixed_content):
            logger.warning(f"Fixed file still has structural issues: {input_path.name}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write fixed file with binary mode to preserve line endings
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            f.write(fixed_content)

        logger.info(f"Successfully fixed: {input_path.name}")
        return True

    except Exception as e:
        logger.error(f"Failed to fix {input_path}: {e}")
        return False

def fix_directory(input_dir: Path, output_dir: Path = None) -> dict:
    """
    Fix all EML files in a directory tree

    Args:
        input_dir: Directory containing malformed EML files
        output_dir: Directory for fixed files (default: input_dir_fixed)

    Returns:
        Statistics dictionary
    """
    if output_dir is None:
        output_dir = input_dir.parent / f"{input_dir.name}_fixed"

    # Find all EML files
    eml_files = list(input_dir.glob("**/*.eml"))

    stats = {
        'total': len(eml_files),
        'success': 0,
        'failed': 0
    }

    logger.info(f"Found {stats['total']} EML files to fix")
    logger.info(f"Output directory: {output_dir}")

    for eml_file in eml_files:
        # Preserve directory structure
        rel_path = eml_file.relative_to(input_dir)
        output_path = output_dir / rel_path

        if fix_eml_file(eml_file, output_path):
            stats['success'] += 1
        else:
            stats['failed'] += 1

    logger.info(f"Fix complete: {stats['success']} success, {stats['failed']} failed")
    return stats

def create_proper_eml_from_gmail_api(raw_base64: str) -> str:
    """
    Properly convert Gmail API raw response to EML format

    Args:
        raw_base64: Base64-encoded raw email from Gmail API

    Returns:
        Properly formatted EML content
    """
    try:
        # Decode base64 to bytes first
        raw_bytes = base64.urlsafe_b64decode(raw_base64)

        # Decode to string with proper error handling
        eml_content = raw_bytes.decode('utf-8', errors='replace')

        # Ensure proper line endings (Gmail API should already provide correct format)
        eml_content = fix_line_endings(eml_content)

        return eml_content

    except Exception as e:
        logger.error(f"Failed to create proper EML from Gmail API: {e}")
        return ""

def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Fix malformed EML files")
    parser.add_argument("--input", required=True, help="Input directory with malformed EML files")
    parser.add_argument("--output", help="Output directory for fixed files")
    parser.add_argument("--test", action="store_true", help="Test a single file first")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output) if args.output else None

    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return

    if args.test:
        # Test with first EML file found
        eml_files = list(input_dir.glob("**/*.eml"))
        if not eml_files:
            logger.error("No EML files found for testing")
            return

        test_file = eml_files[0]
        test_output = Path("test_fixed.eml")

        logger.info(f"Testing fix on: {test_file}")
        success = fix_eml_file(test_file, test_output)

        if success:
            print(f"\n✅ Test successful! Fixed file: {test_output}")
            print("You can now run without --test to fix all files")
        else:
            print("❌ Test failed")
    else:
        # Fix all files
        stats = fix_directory(input_dir, output_dir)

        print(f"\n📊 Results:")
        print(f"Total files: {stats['total']}")
        print(f"Successfully fixed: {stats['success']}")
        print(f"Failed: {stats['failed']}")
        print(f"Success rate: {stats['success']/stats['total']*100:.1f}%")

if __name__ == "__main__":
    main()