#!/usr/bin/env python3
"""Markdown fixer for processed Gmail exports.

This post-processing script attempts to repair common formatting issues
observed in the generated Markdown, specifically:

* Ensure the `Email Details` table has a header separator row.
* Split collapsed table rows such as "---|--- Item | $Value" into proper
  Markdown tables with one row per key/value pair.
* Normalise decorative horizontal rule variants ("* * *" → "---") and
  collapse duplicate rules.
* Leave all other content untouched, writing files back only when changes
  occur.

Usage:
    python tools/markdown_post_fixer.py --root backup_unread_processed

Use `--dry-run` to preview which files would change. By default, files are
rewritten in-place using UTF-8 encoding.
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Iterable, List

EMAIL_HEADER_PATTERN = re.compile(r"^\|\s*Field\s*\|\s*Value\s*\|\s*$")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\|\s*-{3,}\s*\|\s*-{3,}\s*\|\s*$")
CURRENCY_SPLIT_PATTERN = re.compile(r"^([$€£₹]\S*)(?:\s+(.*))?$")
NUMBER_SPLIT_PATTERN = re.compile(r"^([+-]?[0-9][0-9,\.]*)(?:\s+(.*))?$")
HYPHEN_ONLY_PATTERN = re.compile(r"^-+$")
H_RULE_ALIASES = re.compile(r"^(?:\*\s*){3}|(?:-\s*){3}$")


def _expand_token(token: str) -> List[str]:
    token = token.strip()
    if not token:
        return []
    token = re.sub(r"^-+\s*", "", token)
    token = re.sub(r"\s*-+$", "", token)
    token = token.strip()
    if not token:
        return []
    if HYPHEN_ONLY_PATTERN.fullmatch(token.replace(" ", "")):
        return []
    currency_match = CURRENCY_SPLIT_PATTERN.match(token)
    if currency_match and currency_match.group(2):
        return [currency_match.group(1).strip(), currency_match.group(2).strip()]
    number_match = NUMBER_SPLIT_PATTERN.match(token)
    if number_match and number_match.group(2):
        return [number_match.group(1).strip(), number_match.group(2).strip()]
    return [token]


def split_inline_table(line: str) -> List[str] | None:
    """Convert inline key/value sequences into individual Markdown rows."""
    if "|" not in line:
        return None
    stripped = line.strip()
    if stripped.startswith("|"):
        return None
    if "http" in line:
        # Links embedded in such lines tend to be legitimate text, skip.
        return None

    raw_tokens = [part.strip() for part in line.split("|") if part.strip()]
    if not raw_tokens:
        return None

    if all(HYPHEN_ONLY_PATTERN.fullmatch(tok.replace(" ", "")) for tok in raw_tokens):
        return ["| " + " | ".join("---" for _ in raw_tokens) + " |"]

    data_tokens: List[str] = []
    for token in raw_tokens:
        data_tokens.extend(_expand_token(token))

    if len(data_tokens) < 2 or len(data_tokens) % 2 != 0:
        return None

    rows = [f"| {left} | {right} |" for left, right in zip(data_tokens[0::2], data_tokens[1::2])]
    return rows


def normalise_line(line: str) -> str:
    stripped = line.strip()
    if H_RULE_ALIASES.fullmatch(stripped):
        return "---"
    return line.rstrip()


def ensure_email_table_header(lines: List[str]) -> List[str]:
    result: List[str] = []
    for idx, line in enumerate(lines):
        result.append(line)
        if EMAIL_HEADER_PATTERN.match(line.strip()):
            next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
            if not TABLE_SEPARATOR_PATTERN.match(next_line):
                result.append("| --- | --- |")
    return result


def collapse_rules(lines: Iterable[str]) -> List[str]:
    collapsed: List[str] = []
    previous_non_blank = ""
    for line in lines:
        if line == "" and collapsed and collapsed[-1] == "":
            continue
        if line == "---" and previous_non_blank == "---":
            continue
        collapsed.append(line)
        if line.strip():
            previous_non_blank = line.strip()
    return collapsed


def fix_markdown(text: str) -> str:
    lines = text.splitlines()
    lines = [normalise_line(line) for line in lines]

    fixed_lines: List[str] = []
    idx = 0
    total = len(lines)
    while idx < total:
        line = lines[idx]
        split_rows = split_inline_table(line)
        if split_rows:
            fixed_lines.extend(split_rows)
        else:
            fixed_lines.append(line)
        idx += 1

    fixed_lines = ensure_email_table_header(fixed_lines)
    fixed_lines = collapse_rules(fixed_lines)
    return "\n".join(fixed_lines).strip("\n") + "\n"


def process_file(path: Path, dry_run: bool) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    fixed = fix_markdown(original)
    if fixed == original:
        return False
    if dry_run:
        logging.info("Would update %s", path)
        return True
    path.write_text(fixed, encoding="utf-8", newline="\n")
    logging.info("Updated %s", path)
    return True


def find_markdown_files(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair common Markdown issues in Gmail exports.")
    parser.add_argument("--root", default="backup_unread_processed", help="Directory to scan for .md files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N files (0 = all)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(args.root)
    if not root.exists():
        logging.error("Root directory not found: %s", root)
        raise SystemExit(2)

    files = find_markdown_files(root)
    if args.limit > 0:
        files = files[: args.limit]

    changed = 0
    for path in files:
        try:
            if process_file(path, args.dry_run):
                changed += 1
        except Exception as exc:  # retain existing file on failure
            logging.error("Failed processing %s: %s", path, exc)
    logging.info("Checked %d file(s); %d updated.", len(files), changed)


if __name__ == "__main__":
    main()
