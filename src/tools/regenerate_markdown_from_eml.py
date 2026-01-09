#!/usr/bin/env python3
"""Regenerate Markdown from source EML files.

This tool rebuilds the message body for each Markdown export by parsing the
original EML, extracting the HTML body, and converting it back to Markdown with
rich structure (paragraphs, lists, tables, etc.).  It preserves the existing
"Email Details" header from the current Markdown file, replacing only the
"Message Content" section so the layout stays consistent.

Typical usage (in-place rewrite):
    python tools/regenerate_markdown_from_eml.py \
        --eml-root backup_unread \
        --md-root backup_unread_processed

Pass --dry-run to preview which files would change.  Use --output-root to write
regenerated files to a separate directory for review before overwriting the
originals.
"""

from __future__ import annotations

import argparse
import logging
import re
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from typing import Iterable, Optional

MISSING_DEPS = []
try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - dependency guard
    MISSING_DEPS.append("beautifulsoup4>=4.12")
try:
    import html5lib  # noqa: F401
except Exception:  # pragma: no cover
    MISSING_DEPS.append("html5lib>=1.1")
try:
    from markdownify import MarkdownConverter
except Exception:  # pragma: no cover
    MISSING_DEPS.append("markdownify>=0.13")

if MISSING_DEPS:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install with: pip install " + " ".join(MISSING_DEPS)
    )

try:  # Optional pretty formatting
    import mdformat
except Exception:  # pragma: no cover
    mdformat = None


class EmailMarkdownConverter(MarkdownConverter):
    """Custom markdownify converter with tweaks suitable for emails."""

    def convert_br(self, el, text, convert_as_inline=False, **kwargs):
        return "\n"


def markdownify(html: str) -> str:
    conv = EmailMarkdownConverter(
        heading_style="ATX",
        bullets="*",
        code_language=None,
    )
    md = conv.convert(html)
    return md


def extract_html_part(msg: EmailMessage) -> tuple[Optional[str], bool]:
    """Return (body, is_html). Prefer HTML parts, fall back to plain text."""
    html_body = None
    text_body = None

    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart():
                continue
            content_type = part.get_content_type()
            if content_type == "text/html" and html_body is None:
                html_body = part.get_content()
            elif content_type == "text/plain" and text_body is None:
                text_body = part.get_content()
    else:
        content_type = msg.get_content_type()
        if content_type == "text/html":
            html_body = msg.get_content()
        elif content_type == "text/plain":
            text_body = msg.get_content()

    if html_body is not None:
        return html_body, True
    if text_body is not None:
        return text_body, False
    return None, False


def remove_tracking_pixels(soup: BeautifulSoup) -> None:
    for img in list(soup.find_all("img")):
        width = (img.get("width") or "").strip()
        height = (img.get("height") or "").strip()
        style = (img.get("style") or "").lower()
        src = (img.get("src") or "").lower()
        if (
            (width in {"1", "0"} and height in {"1", "0"})
            or "display:none" in style
            or "visibility:hidden" in style
            or src.endswith("pixel.gif")
        ):
            img.decompose()


def flatten_simple_tables(soup: BeautifulSoup) -> None:
    for table in list(soup.find_all("table")):
        cells = table.find_all("td")
        if not cells:
            continue
        # Treat small layout tables (hero blocks) as stacked paragraphs.
        if len(cells) <= 4:
            new_wrapper = soup.new_tag("div")
            for cell in cells:
                p = soup.new_tag("p")
                for child in list(cell.contents):
                    p.append(child)
                cell.decompose()
                if p.get_text(strip=True) or p.find("img"):
                    new_wrapper.append(p)
            table.replace_with(new_wrapper)


def clean_html(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html5lib")
    for tag in soup(["script", "style", "meta", "link", "noscript"]):
        tag.decompose()
    remove_tracking_pixels(soup)
    flatten_simple_tables(soup)
    # Normalize <br> handling by ensuring newline placeholders are present
    for br in soup.find_all("br"):
        br.insert_after(soup.new_string("\n"))
    return soup


def html_to_markdown(html: str) -> str:
    soup = clean_html(html)
    md = markdownify(str(soup))
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = md.strip()
    if mdformat is not None:
        try:
            md = mdformat.text(md, options={"wrap": 80})
        except Exception:  # pragma: no cover - formatting is best effort
            pass
    md = re.sub(r"\s+\Z", "\n", md)
    if not md.endswith("\n"):
        md += "\n"
    return md


def plain_to_markdown(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        raw_line = raw_line.rstrip()
        if raw_line.strip():
            lines.append(raw_line)
        else:
            lines.append("")
    md = "\n".join(lines).strip() + "\n"
    return md


def rebuild_markdown(md_path: Path, eml_path: Path) -> Optional[str]:
    msg = BytesParser(policy=policy.default).parse(eml_path.open("rb"))
    body, is_html = extract_html_part(msg)
    if not body:
        logging.warning("No body content in %s", eml_path)
        return None

    if is_html:
        body_md = html_to_markdown(body)
    else:
        body_md = plain_to_markdown(body)

    original_text = md_path.read_text(encoding="utf-8", errors="replace")
    header, separator, _ = original_text.partition("## Message Content")
    if not separator:
        logging.debug("No '## Message Content' section in %s; replacing entire file", md_path)
        new_text = body_md
    else:
        header = header.rstrip()
        if not header.endswith("\n"):
            header += "\n"
        new_text = f"{header}## Message Content\n\n{body_md.strip()}\n"
    return new_text


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if path.is_file():
            yield path


def corresponding_eml(md_path: Path, md_root: Path, eml_root: Path) -> Optional[Path]:
    rel = md_path.relative_to(md_root)
    eml_path = eml_root / rel.with_suffix(".eml")
    if eml_path.exists():
        return eml_path
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate Markdown from EML sources.")
    parser.add_argument("--md-root", default="backup_unread_processed", help="Root directory containing Markdown exports")
    parser.add_argument("--eml-root", default="backup_unread", help="Root directory containing original EML backups")
    parser.add_argument("--output-root", default="", help="Optional output directory. If omitted, files are rewritten in place.")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N files (0 = no limit)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    for noisy in ('markdown_it', "MARKDOWN_IT_DEBUG", "mdformat"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    md_root = Path(args.md_root)
    eml_root = Path(args.eml_root)
    if not md_root.exists():
        raise SystemExit(f"Markdown root not found: {md_root}")
    if not eml_root.exists():
        raise SystemExit(f"EML root not found: {eml_root}")

    if args.output_root:
        output_root = Path(args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
    else:
        output_root = None

    processed = 0
    updated = 0

    for md_path in iter_markdown_files(md_root):
        if args.limit and processed >= args.limit:
            break
        processed += 1

        eml_path = corresponding_eml(md_path, md_root, eml_root)
        if not eml_path:
            logging.warning("EML counterpart not found for %s", md_path)
            continue

        new_md = rebuild_markdown(md_path, eml_path)
        if new_md is None:
            continue

        destination = md_path
        if output_root is not None:
            destination = output_root / md_path.relative_to(md_root)
            destination.parent.mkdir(parents=True, exist_ok=True)

        original_text = md_path.read_text(encoding="utf-8", errors="replace")
        if new_md == original_text:
            logging.debug("No change for %s", md_path)
            continue

        updated += 1
        if args.dry_run:
            logging.info("Would update %s", destination)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(new_md, encoding="utf-8", newline="\n")
        logging.info("Updated %s", destination)

    logging.info("Processed %d Markdown file(s); %d regenerated.", processed, updated)


if __name__ == "__main__":
    main()
