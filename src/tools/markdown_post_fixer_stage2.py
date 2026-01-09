#!/usr/bin/env python3
"""Secondary Markdown fixer for Gmail exports.

This script addresses residual formatting issues left after the first
post-processing pass:

* Restores paragraph spacing by inserting blank lines between sentences when
  long lines contain multiple sentences.
* Splits inline, pipe-delimited image/link blocks (often marketing hero
  sections) into individual lines even when URLs are present.
* Normalises glued punctuation such as `)and`, `)If`, or `!Thank` to ensure
  there is a space after closing brackets or punctuation.
* Collapses excessive blank lines while preserving intentional spacing.

Example:
    python tools/markdown_post_fixer_stage2.py --root backup_unread_processed --limit 10 --dry-run
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Iterable, List

PIPE_BLOCK_RE = re.compile(r"\\|")
HTTP_RE = re.compile(r"https?://", re.IGNORECASE)
SENTENCE_BOUNDARY_RE = re.compile(r"([.!?])\s+(?=[A-Z])")
PAREN_ADHESION_RE = re.compile(r"([)\]])(?=[A-Za-z])")
PUNCT_ADHESION_RE = re.compile(r"([!?])(?=[A-Za-z])")
PERIOD_ADHESION_RE = re.compile(r"([.])(?=[A-Z])")
TRAILING_HANGING_RE = re.compile(r"[)\]]—-?")

def _split_pipe_media_line(line: str) -> List[str] | None:
    """Split marketing hero lines, keeping meaningful tokens only."""
    if "|" not in line or "http" not in line:
        return None
    if line.strip().startswith("|"):
        # Likely a legitimate table row; leave to the primary fixer.
        return None
    tokens = [tok.strip().strip('-') for tok in line.split("|")]
    tokens = [tok for tok in tokens if tok]
    if len(tokens) <= 1:
        return None
    return tokens

def _expand_sentences(line: str) -> List[str]:
    """Insert blank lines between sentences for long collapsed paragraphs."""
    if len(line) < 160:
        return [line]
    if not SENTENCE_BOUNDARY_RE.search(line):
        return [line]
    expanded = SENTENCE_BOUNDARY_RE.sub(r"\1\n\n", line)
    return expanded.splitlines()

def _normalise_spacing(line: str) -> str:
    line = PAREN_ADHESION_RE.sub(r"\1 ", line)
    line = PUNCT_ADHESION_RE.sub(r"\1 ", line)
    line = PERIOD_ADHESION_RE.sub(r"\1 ", line)
    line = re.sub(r"([,;])(?=[A-Za-z])", r" ", line)
    line = TRAILING_HANGING_RE.sub(lambda m: m.group(0)[0] + " ", line)
    # Clean up accidental double spaces that are not Markdown line breaks.
    line = re.sub(r"(?<! ) {3,}", "  ", line)
    line = re.sub(r"(Team)\s+(This email)", r"\1.\n\n\2", line)
    return line.strip()



def collapse_blank_lines(lines: Iterable[str]) -> List[str]:
    collapsed: List[str] = []
    blank_run = 0
    for line in lines:
        if line.strip():
            blank_run = 0
            collapsed.append(line)
        else:
            blank_run += 1
            if blank_run <= 2:
                collapsed.append("")
    return collapsed

def fix_markdown(text: str) -> str:
    lines = text.splitlines()
    interim: List[str] = []
    for line in lines:
        media_split = _split_pipe_media_line(line)
        if media_split:
            interim.extend(media_split)
            continue
        expanded = _expand_sentences(line)
        interim.extend(expanded)
    # Normalise spacing and flatten
    normalised: List[str] = []
    for entry in interim:
        if "\n" in entry:
            parts = entry.splitlines()
        else:
            parts = [entry]
        for part in parts:
            normalised.append(_normalise_spacing(part))
    result_lines = collapse_blank_lines([line.rstrip() for line in normalised])
    # Trim leading/trailing blank lines
    while result_lines and not result_lines[0].strip():
        result_lines.pop(0)
    while result_lines and not result_lines[-1].strip():
        result_lines.pop()
    return "\n".join(result_lines) + "\n"

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

def gather_files(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Additional Markdown cleanup for Gmail exports.")
    parser.add_argument("--root", default="backup_unread_processed", help="Directory tree to scan")
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

    files = gather_files(root)
    if args.limit > 0:
        files = files[: args.limit]

    changed = 0
    for file_path in files:
        try:
            if process_file(file_path, args.dry_run):
                changed += 1
        except Exception as exc:
            logging.error("Failed processing %s: %s", file_path, exc)
    logging.info("Checked %d file(s); %d updated.", len(files), changed)

if __name__ == "__main__":
    main()
