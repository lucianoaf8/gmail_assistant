#!/usr/bin/env python3
"""gmail markdown cleanup
==========================

Command-line utility that normalises Gmail-exported markdown into something
pleasant to read (and diff). Reads files from backup_unread and saves processed
versions to backup_unread_processed (or custom output directory).

The script is designed to be idempotent: running it multiple times over the same
file should never introduce further changes.

Usage examples
--------------
* `python tools/cleanup_markdown.py backup_unread/`
* `python tools/cleanup_markdown.py -r backup_unread/ -o backup_cleaned/`
* `python tools/cleanup_markdown.py -n --limit 20 backup_unread/*.md`
* `python tools/cleanup_markdown.py --stats-only backup_unread/2025`
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, List, Optional

LOG = logging.getLogger(__name__)
Transform = Callable[[List[str]], List[str]]


@dataclass
class Config:
    """Runtime configuration derived from the command line."""

    sources: List[Path]
    recursive: bool
    dry_run: bool
    limit: Optional[int]
    stats_only: bool
    check_only: bool
    log_level: int
    output_dir: Optional[Path] = None
    force_overwrite: bool = False
    max_file_size: int = 10 * 1024 * 1024  # bytes


def parse_args(argv: Iterable[str]) -> Config:
    """Parse CLI options into a :class:`Config` instance."""

    parser = argparse.ArgumentParser(
        description="Cleanup messy Gmail-exported Markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s -r backup_unread/\n"
            "  %(prog)s -n --limit 10 backup_unread/ -o backup_unread_processed/\n"
            "  %(prog)s --stats-only backup_unread/*.md\n"
            "  %(prog)s --check-only backup_unread/\n"
        ),
    )

    parser.add_argument("paths", nargs="+", type=Path, help="Files or directories to process.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Descend into subdirectories.")
    parser.add_argument("-l", "--limit", type=int, help="Process only the first N matched files.")
    parser.add_argument("-o", "--output", type=Path, help="Output directory for processed files (default: add '_processed' suffix to input dir).")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("-n", "--dry-run", action="store_true", help="Preview changes without writing.")
    mode_group.add_argument("--stats-only", action="store_true", help="Report what would change and exit.")
    mode_group.add_argument("--check-only", action="store_true", help="Validate files without reporting stats.")

    parser.add_argument("--force", action="store_true", help="Overwrite existing output files.")
    parser.add_argument("--max-size", type=int, default=10, help="Maximum file size in MB to process (default: 10).")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )

    args = parser.parse_args(list(argv))
    level = getattr(logging, args.log_level.upper(), logging.INFO)

    return Config(
        sources=args.paths,
        recursive=args.recursive,
        dry_run=args.dry_run,
        limit=args.limit,
        stats_only=args.stats_only,
        check_only=args.check_only,
        log_level=level,
        output_dir=args.output,
        force_overwrite=args.force,
        max_file_size=args.max_size * 1024 * 1024,
    )


# ---------------------------------------------------------------------------
#  Normalisation pipeline
# ---------------------------------------------------------------------------


def normalise_line_endings(lines: List[str]) -> List[str]:
    """Ensure every line ends with ``\n`` and strip stray carriage returns."""

    return [line.rstrip("\r\n") + "\n" for line in lines]



def _extract_email_detail_entries(block: List[str]) -> List[tuple[str, str]]:
    """Parse both well-formed tables and collapsed key/value sequences."""

    key_order = ["From", "To", "Date", "Subject", "Gmail ID", "Thread ID", "Labels"]
    entries: List[tuple[str, str]] = []

    for raw in block:
        stripped = raw.strip()
        if not stripped or set(stripped) <= {"|", "-", ":"}:
            continue
        if "|" in stripped:
            cells = [re.sub(r"\s+", " ", cell).strip(" -") for cell in stripped.strip("|").split("|")]
            cells = [c for c in cells if c]
            if len(cells) >= 2:
                key = cells[0].strip().strip(":")
                if key and key.lower() != "field":
                    value = " | ".join(cells[1:]).strip()
                    if value:
                        entries.append((key, value))
            continue
        match = re.match(r"^([^:]+):\s*(.+)$", stripped)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key and key.lower() != "field" and value:
                entries.append((key, value))

    if entries:
        return entries

    joined = " ".join(part.strip() for part in block if part.strip())
    if not joined:
        return []

    cleaned = re.sub(r"Field\s*\|\s*Value", "", joined, flags=re.IGNORECASE)
    cleaned = re.sub(r"-{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    pattern = re.compile(
        r"(From|To|Date|Subject|Gmail ID|Thread ID|Labels)\s*\|\s*"
        r"([^|]+?)(?=\s+(?:From|To|Date|Subject|Gmail ID|Thread ID|Labels)\s*\||$)",
        re.IGNORECASE,
    )

    fallback: List[tuple[str, str]] = []
    seen_keys: set[str] = set()
    for match in pattern.finditer(cleaned):
        key = match.group(1)
        canonical = next((k for k in key_order if k.lower() == key.lower()), key)
        if canonical in seen_keys:
            continue
        value = match.group(2).strip()
        if value:
            fallback.append((canonical, value))
            seen_keys.add(canonical)

    if fallback:
        return fallback

    cleaned_no_pipes = cleaned.strip('| ').strip()
    lower = cleaned_no_pipes.lower()
    keyword_positions: List[tuple[int, str]] = []
    for key in key_order:
        idx = lower.find(key.lower())
        if idx != -1:
            keyword_positions.append((idx, key))
    keyword_positions.sort()

    fallback_keywords: List[tuple[str, str]] = []
    for idx, (pos, key) in enumerate(keyword_positions):
        start = pos + len(key)
        end = keyword_positions[idx + 1][0] if idx + 1 < len(keyword_positions) else len(cleaned_no_pipes)
        value = cleaned_no_pipes[start:end].replace('|', ' ').strip(' :-')
        if value:
            fallback_keywords.append((key, value))

    if fallback_keywords:
        return fallback_keywords

    kv_pairs: List[tuple[str, str]] = []
    for raw in block:
        stripped = raw.strip()
        match = re.match(r"^([^:]+):\s*(.+)$", stripped)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key and key.lower() != "field" and value:
                kv_pairs.append((key, value))
    return kv_pairs


def tidy_front_matter(lines: List[str]) -> List[str]:
    """Collapse the "Email Details" section into a clean two-column table."""

    result: List[str] = []
    seen_email_details = False
    i = 0
    header_pattern = re.compile(r"^#+\s*Email\s+Details\s*$", re.IGNORECASE)

    while i < len(lines):
        line = lines[i]
        if header_pattern.match(line.strip()):
            if seen_email_details:
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("#"):
                    i += 1
                continue

            seen_email_details = True
            result.append(line if line.endswith("\n") else line + "\n")
            block: List[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("#"):
                block.append(lines[i])
                i += 1

            entries = _extract_email_detail_entries(block)
            if entries:
                result.append("| Field | Value |\n")
                result.append("| --- | --- |\n")
                seen_keys = set()
                for key, value in entries:
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    result.append(f"| {key} | {value} |\n")
                result.append("\n")
            else:
                result.extend(block)
            continue

        result.append(line if line.endswith("\n") else line + "\n")
        i += 1

    return result


def normalise_horizontal_rules(lines: List[str]) -> List[str]:
    """Standardise horizontal rule markers and guarantee surrounding spacing."""

    result: List[str] = []
    for line in lines:
        if re.match(r"^\s*-{2,}\s*$", line):
            result.append("---\n")
            result.append("\n")
        else:
            result.append(line)
    return result


def join_wrapped_urls(lines: List[str]) -> List[str]:
    """Join URLs that were wrapped onto subsequent lines during export."""

    result: List[str] = []
    i = 0

    while i < len(lines):
        current = lines[i]
        match = re.search(r"https?://[^\s)]+$", current.rstrip())
        if match:
            url_parts = [current.rstrip()]
            j = i + 1
            while j < len(lines):
                candidate = lines[j].strip()
                if not candidate:
                    break
                if re.match(r"^[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+$", candidate):
                    url_parts.append(candidate)
                    j += 1
                    continue
                break
            result.append("".join(url_parts) + "\n")
            i = j
        else:
            result.append(current)
            i += 1

    return result


def fix_escaped_lists(lines: List[str]) -> List[str]:
    """Convert escaped list markers back to normal Markdown bullets."""

    result: List[str] = []
    for line in lines:
        if re.match(r"^\s*\\[+-]\s", line):
            result.append(re.sub(r"^(\s*)\\[+-]\s", r"\1- ", line))
        elif re.match(r"^\s*\\?\d+\\.\s", line):
            result.append(re.sub(r"^(\s*)\\?(\d+)\\.\s", r"\1\2. ", line))
        else:
            result.append(line)
    return result


def flatten_pipe_blocks(lines: List[str]) -> List[str]:
    """Normalise table-like pipe rows while dropping decorative cruft."""

    result: List[str] = []
    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped.strip():
            result.append("\n")
            continue

        if not stripped.lstrip().startswith("|"):
            result.append(line if line.endswith("\n") else line + "\n")
            continue

        cells = [re.sub(r"\s+", " ", cell).strip() for cell in stripped.strip().strip("|").split("|")]
        meaningful = [c for c in cells if c and not re.fullmatch(r"[-:]+", c)]
        if len(meaningful) <= 1:
            continue

        row = "| " + " | ".join(meaningful) + " |\n"
        result.append(row)

    return result


def split_inline_separators(lines: List[str]) -> List[str]:
    """Ensure images or other inline blocks are not glued to following text."""

    result: List[str] = []
    for line in lines:
        stripped = line.rstrip("\n")
        if stripped.strip().startswith('![') and ')' in stripped:
            before, after = stripped.split(')', 1)
            image_segment = before + ')'
            remainder = after.strip(" -\uFFFD\u2014")
            result.append(image_segment + "\n")
            if remainder:
                if remainder.startswith('--'):
                    result.append("---\n")
                    remainder = remainder.lstrip('- ').strip()
                    if remainder:
                        result.append(remainder + "\n")
                else:
                    result.append("\n")
                    result.append(remainder + "\n")
            continue

        normalised = re.sub(r"\)\s*--+\s*", ")\n\n---\n\n", stripped)
        parts = normalised.split("\n")
        for part in parts:
            result.append(part + "\n")
    return result



def rebuild_lists_and_paragraphs(lines: List[str]) -> List[str]:
    """Reassemble wrapped paragraphs and honour block-level Markdown elements."""

    result: List[str] = []
    i = 0
    last_block: Optional[str] = None

    def push_blank() -> None:
        if result and result[-1] != "\n":
            result.append("\n")

    table_row = re.compile(r"^\|.*\|$")
    list_item = re.compile(r"^(\s*[-*+]|\s*\d+\.)\s")

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        if not stripped:
            push_blank()
            last_block = None
            i += 1
            continue

        if table_row.match(stripped):
            if last_block != "table":
                push_blank()
            result.append(raw if raw.endswith("\n") else raw + "\n")
            last_block = "table"
            i += 1
            continue

        if re.fullmatch(r"-{3,}", stripped):
            push_blank()
            result.append("---\n")
            push_blank()
            last_block = "hr"
            i += 1
            continue

        if stripped.startswith("#"):
            push_blank()
            result.append(stripped + "\n")
            push_blank()
            last_block = "heading"
            i += 1
            continue

        if list_item.match(stripped):
            push_blank()
            result.append(raw if raw.endswith("\n") else raw + "\n")
            last_block = "list"
            i += 1
            continue

        if stripped.startswith("!["):
            push_blank()
            result.append(raw if raw.endswith("\n") else raw + "\n")
            push_blank()
            last_block = "image"
            i += 1
            continue

        paragraph: List[str] = [raw.rstrip("\n")]
        i += 1
        while i < len(lines):
            candidate = lines[i]
            candidate_stripped = candidate.strip()
            if not candidate_stripped:
                break
            if candidate_stripped.startswith("#"):
                break
            if list_item.match(candidate_stripped):
                break
            if candidate_stripped.startswith("!["):
                break
            if table_row.match(candidate_stripped):
                break
            if re.fullmatch(r"-{3,}", candidate_stripped):
                break
            paragraph.append(candidate.rstrip("\n"))
            i += 1

        joined = " ".join(part.strip() for part in paragraph if part).strip()
        if joined:
            push_blank()
            result.append(joined + "\n")
            push_blank()
            last_block = "paragraph"

    cleaned: List[str] = []
    for line in result:
        if line == "\n" and cleaned and cleaned[-1] == "\n":
            continue
        cleaned.append(line)

    if not cleaned or cleaned[-1] != "\n":
        cleaned.append("\n")
    return cleaned


def restore_unicode(lines: List[str]) -> List[str]:
    """Restore common placeholder sequences to their Unicode equivalents."""

    replacements = [
        (re.compile(r"\(c\)", re.IGNORECASE), "©"),
        (re.compile(r"\(r\)", re.IGNORECASE), "®"),
        (re.compile(r"\(tm\)", re.IGNORECASE), "™"),
    ]

    result: List[str] = []
    for line in lines:
        for pattern, replacement in replacements:
            line = pattern.sub(replacement, line)
        line = re.sub(r"(?<=\s)--(?=\s)", "—", line)
        line = line.replace("...", "…")
        line = re.sub(r"(?<=\s)c\s+(\d{4})", r" © \1", line)
        result.append(line)
    return result


PIPELINE: List[Transform] = [
    normalise_line_endings,
    tidy_front_matter,
    normalise_horizontal_rules,
    join_wrapped_urls,
    fix_escaped_lists,
    flatten_pipe_blocks,
    split_inline_separators,
    rebuild_lists_and_paragraphs,
    restore_unicode,
]


# ---------------------------------------------------------------------------
#  Supporting helpers
# ---------------------------------------------------------------------------


def get_output_path(input_path: Path, cfg: Config) -> Path:
    """Determine the output path for a processed file."""
    if cfg.output_dir is not None:
        # Use explicit output directory
        output_dir = cfg.output_dir
    else:
        # Auto-generate output directory by adding '_processed' suffix
        if len(cfg.sources) == 1 and cfg.sources[0].is_dir():
            base_dir = cfg.sources[0]
            output_dir = base_dir.parent / (base_dir.name + "_processed")
        else:
            # If multiple sources or files, use current directory with suffix
            output_dir = Path.cwd() / "processed_markdown"
    
    # Preserve relative path structure
    relative_path = input_path
    for source in cfg.sources:
        try:
            if source.is_dir():
                relative_path = input_path.relative_to(source)
                break
            elif source.is_file() and input_path == source:
                relative_path = input_path.name
                break
        except ValueError:
            continue
    
    return output_dir / relative_path


def discover_files(cfg: Config) -> Iterator[Path]:
    """Yield markdown files respecting recursion, limits and size caps."""

    count = 0
    for src in cfg.sources:
        if not src.exists():
            LOG.warning("Path does not exist: %s", src)
            continue

        if src.is_file():
            candidates = [src] if src.suffix.lower() == ".md" else []
        elif cfg.recursive:
            candidates = sorted(p for p in src.rglob("*.md") if p.is_file())
        else:
            candidates = sorted(p for p in src.glob("*.md") if p.is_file())

        for path in candidates:
            try:
                if not path.exists():
                    LOG.warning("File does not exist: %s", path)
                    continue
                    
                size = path.stat().st_size
            except (OSError, PermissionError) as exc:
                LOG.warning("Cannot access %s: %s", path, exc)
                continue

            if size > cfg.max_file_size:
                LOG.warning("Skipping large file %.1f MB: %s", size / (1024 * 1024), path)
                continue

            yield path
            count += 1
            if cfg.limit is not None and count >= cfg.limit:
                return


def apply_pipeline(lines: List[str]) -> List[str]:
    for transform in PIPELINE:
        lines = transform(lines)
    return lines


def md5_digest(lines: List[str]) -> str:
    blob = "".join(lines).encode("utf-8", errors="surrogatepass")
    return hashlib.md5(blob).hexdigest()


def get_sample_changes(original: List[str], transformed: List[str]) -> dict:
    """Return a lightweight description of the differences for debugging."""

    samples: dict = {"lines_added": 0, "lines_removed": 0, "sample_diffs": []}
    orig_set = set(original)
    trans_set = set(transformed)
    samples["lines_added"] = len(trans_set - orig_set)
    samples["lines_removed"] = len(orig_set - trans_set)

    for line in list(trans_set - orig_set)[:3]:
        samples["sample_diffs"].append({"type": "added", "content": line.strip()})
    for line in list(orig_set - trans_set)[:3]:
        samples["sample_diffs"].append({"type": "removed", "content": line.strip()})
    return samples


# ---------------------------------------------------------------------------
#  File processor & CLI plumbing
# ---------------------------------------------------------------------------


def process_file(path: Path, cfg: Config) -> dict:
    """Run the normalisation pipeline for a single file."""

    try:
        text = path.read_text(encoding="utf-8", errors="surrogateescape")
    except Exception as exc:  # pragma: no cover - IO failure
        LOG.error("Failed to read %s: %s", path, exc)
        return {"path": path, "error": str(exc), "before_lines": 0, "after_lines": 0, "changed": False}

    original_lines = text.splitlines(keepends=True)
    if not original_lines:
        return {"path": path, "before_lines": 0, "after_lines": 0, "changed": False}

    try:
        transformed = apply_pipeline(list(original_lines))
        second_pass = apply_pipeline(list(transformed))
        if md5_digest(transformed) != md5_digest(second_pass):
            LOG.warning("Non-idempotent transforms for %s; stabilising output", path)
            transformed = second_pass
    except Exception as exc:  # pragma: no cover - pipeline failure
        LOG.error("Pipeline failed for %s: %s", path, exc)
        return {
            "path": path,
            "error": str(exc),
            "before_lines": len(original_lines),
            "after_lines": 0,
            "changed": False,
        }

    changed = original_lines != transformed
    stats = {
        "path": path,
        "before_lines": len(original_lines),
        "after_lines": len(transformed),
        "line_diff": len(transformed) - len(original_lines),
        "changed": changed,
        "size_before": len("".join(original_lines)),
        "size_after": len("".join(transformed)),
    }

    if LOG.level <= logging.DEBUG and changed:
        stats["sample_changes"] = get_sample_changes(original_lines, transformed)

    if cfg.stats_only or cfg.check_only or cfg.dry_run:
        return stats

    # Determine output path
    output_path = get_output_path(path, cfg)
    stats["output_path"] = output_path

    if not changed:
        LOG.debug("No changes needed for %s", path)
        # Still create output file even if no changes for consistency
        if not cfg.stats_only and not cfg.check_only and not cfg.dry_run:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if not output_path.exists() or cfg.force_overwrite:
                    output_path.write_text("".join(original_lines), encoding="utf-8")
                    LOG.debug("Copied unchanged file %s → %s", path, output_path)
            except Exception as exc:
                LOG.error("Failed to copy unchanged file %s: %s", path, exc)
                stats["error"] = str(exc)
        return stats

    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if output file already exists
        if output_path.exists() and not cfg.force_overwrite:
            LOG.debug("Output file exists for %s (use --force to overwrite)", output_path)
            stats["skipped"] = True
        else:
            output_path.write_text("".join(transformed), encoding="utf-8")
            LOG.info("Processed %s → %s (lines: %d→%d)", path, output_path, stats["before_lines"], stats["after_lines"])
    except Exception as exc:  # pragma: no cover - IO failure
        LOG.error("Failed to write %s: %s", output_path, exc)
        stats["error"] = str(exc)
    return stats


def main(argv: Iterable[str]) -> int:
    cfg = parse_args(argv)
    logging.basicConfig(level=cfg.log_level, format="%(levelname)s: %(message)s", datefmt="%H:%M:%S")

    # Show output directory info
    if cfg.sources and not cfg.stats_only and not cfg.check_only:
        try:
            # Find a real file to determine output path structure
            sample_path = None
            for source in cfg.sources:
                if source.is_file() and source.suffix.lower() == ".md":
                    sample_path = source
                    break
                elif source.is_dir():
                    # Look for markdown files in directory
                    pattern = "**/*.md" if cfg.recursive else "*.md"
                    sample_file = next(iter(source.glob(pattern)), None)
                    if sample_file:
                        sample_path = sample_file
                        break
            
            if sample_path:
                output_path = get_output_path(sample_path, cfg)
                LOG.info("Output directory: %s", output_path.parent)
            elif cfg.output_dir:
                LOG.info("Output directory: %s", cfg.output_dir)
            else:
                # Default output directory logic
                if len(cfg.sources) == 1 and cfg.sources[0].is_dir():
                    base_dir = cfg.sources[0]
                    output_dir = base_dir.parent / (base_dir.name + "_processed")
                    LOG.info("Output directory: %s", output_dir)
        except Exception:
            # If we can't determine output path, just continue
            pass

    if cfg.dry_run:
        LOG.info("Running in dry-run mode. No files will be modified.")
    elif cfg.stats_only:
        LOG.info("Running in stats-only mode. No files will be modified.")
    elif cfg.check_only:
        LOG.info("Running in check-only mode. Input will be validated only.")

    processed = 0
    changed = 0
    errors = 0
    total_size_before = 0
    total_size_after = 0

    try:
        for filepath in discover_files(cfg):
            LOG.debug("Processing %s", filepath)
            stats = process_file(filepath, cfg)
            processed += 1

            if stats.get("error"):
                errors += 1
            elif stats["changed"]:
                changed += 1

            total_size_before += stats.get("size_before", 0)
            total_size_after += stats.get("size_after", 0)

            if (cfg.stats_only or cfg.check_only) and LOG.level <= logging.INFO:
                if stats.get("error"):
                    LOG.info("ERROR %s: %s", filepath, stats["error"])
                elif cfg.check_only:
                    LOG.info("OK %s: validated successfully", filepath)
                elif stats["changed"]:
                    LOG.info("CHANGES %s: %d→%d lines (%+d)", filepath, stats["before_lines"], stats["after_lines"], stats.get("line_diff", 0))
                else:
                    LOG.info("OK %s: no changes required", filepath)

    except KeyboardInterrupt:  # pragma: no cover - manual interrupt
        LOG.warning("Interrupted by user")
        return 1
    except Exception as exc:  # pragma: no cover - unexpected failure
        LOG.error("Unexpected error: %s", exc)
        return 1

    LOG.info("Summary: processed %d file(s), %d modified, %d errors", processed, changed, errors)
    if total_size_before > 0:
        delta = total_size_after - total_size_before
        pct = (delta / total_size_before) * 100
        LOG.info("Size change: %+d bytes (%+.1f%%)", delta, pct)

    return 1 if errors else 0


def demo_transforms() -> None:
    """Showcase the individual transforms with tiny examples."""

    examples = [
        ("Escaped lists", ["\\+ First item\n", "\\- Second item\n"], fix_escaped_lists),
        ("Pipe flattening", ["|  |\n", "| Image | ![](logo.png) |\n"], flatten_pipe_blocks),
        ("Unicode restore", ["Copyright (C) 2025\n", "Price: $10.00 -- $9.99\n"], restore_unicode),
        ("Wrapped URLs", ["Visit https://example.com/\n", "long/path\n"], join_wrapped_urls),
    ]

    print("\n=== Cleanup Transform Examples ===\n")
    for name, before, transform in examples:
        print(f"Transform: {name}")
        print("  Before:")
        for line in before:
            print(f"    {repr(line)}")
        print("  After:")
        for line in transform(before):
            print(f"    {repr(line)}")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_transforms()
    else:
        sys.exit(main(sys.argv[1:]))
