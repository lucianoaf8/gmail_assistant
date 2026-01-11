#!/usr/bin/env python3
"""
gmail_eml_to_markdown_cleaner.py

Purpose
- Walk C:\\Projects\\gmail_assistant\backup_unread\2025\\**\\* for .eml and .md
- Rebuild clean, consistent, professional Markdown with front matter
- Normalize quotes, lists, spacing, and line-wrapping
- Preserve links, detect encoding, extract inline CID images, and save attachments
- Reformat any existing .md files with mdformat to a consistent style
- Write outputs under a mirrored tree: <base>\\_clean\\<year>\\<month>\\*.md
- Read-only on sources. No admin needed. Windows-friendly paths.

Requirements
pip install markdownify mdformat beautifulsoup4 html5lib chardet python-frontmatter
"""

import argparse
import datetime as dt
import email
import logging
import re
import sys
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

# Local imports
from gmail_assistant.utils.input_validator import InputValidator, ValidationError

# Dependency checks (fail fast with actionable hints)
MISSING = []
try:
    import chardet  # encoding detection
except Exception:
    MISSING.append("chardet>=5.2")
try:
    import frontmatter  # YAML front matter
except Exception:
    MISSING.append("python-frontmatter>=1.0")
try:
    from bs4 import BeautifulSoup  # HTML cleanup
except Exception:
    MISSING.append("beautifulsoup4>=4.12")
try:
    import html5lib  # noqa: F401  # parser backend for bs4
except Exception:
    MISSING.append("html5lib>=1.1")
try:
    from markdownify import markdownify as md_convert  # HTML -> MD
except Exception:
    MISSING.append("markdownify>=0.13")
# mdformat is used via subprocess safest on Windows; but try import to detect availability
try:
    import importlib.util as _il
    _mdformat_available = _il.find_spec("mdformat") is not None
except Exception:
    _mdformat_available = False

if MISSING:
    sys.stderr.write(
        "\n[ERROR] Missing required packages:\n  pip install "
        + " ".join(f'"{p}"' for p in MISSING)
        + "\n"
    )
    sys.exit(1)

# ---------- Config ----------
DEFAULT_BASE = r"C:\Projects\gmail_assistant\backup_unread\2025"
OUTPUT_ROOT_SUFFIX = "_clean"
ATTACH_DIR_NAME = "_attachments"
MAX_LINE = 100  # wrap target for paragraphs
# ----------------------------

def detect_encoding(p: Path) -> str:
    raw = p.read_bytes()
    det = chardet.detect(raw)
    enc = det.get("encoding") or "utf-8"
    try:
        raw.decode(enc, errors="strict")
    except Exception:
        enc = "utf-8"
    return enc

def load_bytes(p: Path) -> bytes:
    return p.read_bytes()

def sanitize_filename(name: str) -> str:
    """Sanitize filename. Delegates to InputValidator for consistency."""
    try:
        return InputValidator.sanitize_filename(name, max_length=180)
    except ValidationError:
        return "untitled"

def html_cleanup(html: str) -> str:
    # Remove tracking pixels, scripts, styles. Simplify tables.
    soup = BeautifulSoup(html, "html5lib")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    # tracking pixels: 1x1 or zero-sized images
    for img in soup.find_all("img"):
        w = (img.get("width") or "").strip()
        h = (img.get("height") or "").strip()
        style = (img.get("style") or "").lower()
        if (
            (w == "1" and h == "1")
            or ("display:none" in style)
            or ("visibility:hidden" in style)
        ):
            img.decompose()
    # collapse extra whitespace
    html = re.sub(r"\n{3,}", "\n\n", soup.body.get_text("\n") if soup.body else soup.get_text("\n"))
    # Recreate minimal HTML wrapper for markdownify to keep paragraphs
    html = "<html><body>" + "\n".join(line.strip() for line in html.splitlines()) + "</body></html>"
    return html

def convert_html_to_markdown(html: str) -> str:
    """Convert HTML to markdown with input validation."""
    try:
        # Validate HTML input
        validator = InputValidator()
        html = validator.validate_string(html, max_length=5000000)  # 5MB limit

        # Configure markdownify for email-friendly output
        md = md_convert(
            html,
            heading_style="ATX",
            bullets="*",
            strip=["a"],  # keep links but avoid extra attrs; markdownify preserves href
            convert=["b", "strong", "em", "i", "u", "br", "p", "ul", "ol", "li", "blockquote", "img", "table"],
        )
    except ValidationError as e:
        logging.error(f"HTML validation failed: {e}")
        return f"[Error: Invalid HTML content - {e}]"
    except Exception as e:
        logging.error(f"HTML conversion failed: {e}")
        return f"[Error: HTML conversion failed - {e}]"
    # Normalize blockquotes and spacing
    md = re.sub(r"\n{3,}", "\n\n", md)
    # Fix lines that start with multiple '>' and stray spaces
    md = re.sub(r"^(\s*>+)\s*", r"\1 ", md, flags=re.MULTILINE)
    return md

def wrap_paragraphs(md: str, width: int = MAX_LINE) -> str:
    # Soft wrap paragraphs only. Do not wrap inside code fences, tables, or list markers.
    out = []
    in_code = False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code or re.match(r"^\s*([*+-] |\d+\. |>|\|)|^#{1,6}\s", line):
            out.append(line)
            continue
        # wrap long paragraphs
        if len(line) > width and " " in line:
            words = line.split()
            cur = []
            cur_len = 0
            for w in words:
                if cur_len + 1 + len(w) > width:
                    out.append(" ".join(cur))
                    cur = [w]
                    cur_len = len(w)
                else:
                    cur.append(w)
                    cur_len = len(" ".join(cur))
            if cur:
                out.append(" ".join(cur))
        else:
            out.append(line)
    return "\n".join(out)

def extract_best_part(msg: email.message.Message) -> tuple[str | None, str | None]:
    """
    Return (text_plain, html) as strings if present.
    """
    text_plain = None
    text_html = None
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disp:
                continue
            try:
                payload = part.get_content()
            except Exception:
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8", errors="replace")
            if ctype == "text/plain" and text_plain is None:
                text_plain = str(payload)
            elif ctype == "text/html" and text_html is None:
                text_html = str(payload)
    else:
        ctype = msg.get_content_type()
        payload = msg.get_content()
        if ctype == "text/plain":
            text_plain = str(payload)
        elif ctype == "text/html":
            text_html = str(payload)
    return text_plain, text_html

def save_attachments(msg: email.message.Message, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for part in msg.walk():
        disp = (part.get("Content-Disposition") or "").lower()
        if "attachment" in disp or part.get_content_maintype() != "text":
            filename = part.get_filename()
            if not filename:
                continue
            data = part.get_payload(decode=True)
            if not isinstance(data, (bytes, bytearray)):
                continue
            fname = sanitize_filename(filename)
            (out_dir / fname).write_bytes(data)

def cid_image_map(msg: email.message.Message, attach_dir: Path) -> dict:
    """Map cid:... to saved attachment filenames for markdown image linking."""
    mapping = {}
    for part in msg.walk():
        if part.get_content_maintype() == "image":
            cid = part.get("Content-ID")
            if not cid:
                continue
            cid_clean = cid.strip("<>")
            filename = part.get_filename() or f"{cid_clean}.bin"
            filename = sanitize_filename(filename)
            data = part.get_payload(decode=True)
            if not isinstance(data, (bytes, bytearray)):
                continue
            attach_dir.mkdir(parents=True, exist_ok=True)
            (attach_dir / filename).write_bytes(data)
            mapping[f"cid:{cid_clean}"] = f"{ATTACH_DIR_NAME}/{filename}"
    return mapping

def apply_cid_rewrites(md: str, cid_map: dict) -> str:
    # Replace ![](cid:xyz) or links to cid:... with saved file paths
    for cid, rel in cid_map.items():
        md = md.replace(f"]({cid})", f"]({rel})").replace(f"![]({cid})", f"![]({rel})")
    return md

def build_front_matter(msg: email.message.Message, source_rel: str) -> dict:
    # Parse headers robustly
    subj = (msg.get("Subject") or "").strip()
    from_list = getaddresses(msg.get_all("From", []))
    to_list = getaddresses(msg.get_all("To", []))
    date_hdr = msg.get("Date")
    try:
        date_iso = parsedate_to_datetime(date_hdr).astimezone(dt.timezone.utc).isoformat()
    except Exception:
        date_iso = None
    fm = {
        "source_file": source_rel,
        "subject": subj,
        "from": [f"{n} <{a}>" if n else a for n, a in from_list],
        "to": [f"{n} <{a}>" if n else a for n, a in to_list],
        "date": date_iso,
        "message_id": (msg.get("Message-Id") or msg.get("Message-ID") or "").strip(),
        "labels": list(msg.get_all("X-Gmail-Labels", []) or []),
    }
    return fm

def compose_markdown(fm: dict, body_md: str) -> str:
    post = frontmatter.Post(body_md, **fm)
    return frontmatter.dumps(post)

def process_eml(eml_path: Path, base_dir: Path, out_root: Path) -> Path | None:
    raw = load_bytes(eml_path)
    msg = BytesParser(policy=policy.default).parsebytes(raw)

    text_plain, text_html = extract_best_part(msg)

    attach_dir = (out_root / eml_path.parent.relative_to(base_dir) / ATTACH_DIR_NAME)
    cid_map = cid_image_map(msg, attach_dir)

    if text_plain and (not text_html or len(text_plain) >= len(re.sub(r"\s+", "", text_html)) * 0.4):
        body_md = text_plain.strip()
    else:
        html = html_cleanup(text_html or "")
        body_md = convert_html_to_markdown(html)
        body_md = apply_cid_rewrites(body_md, cid_map)

    body_md = wrap_paragraphs(body_md, MAX_LINE)

    fm = build_front_matter(msg, str(eml_path.relative_to(base_dir)))
    final_md = compose_markdown(fm, body_md)

    # Output path mirrors input name, with .md
    rel = eml_path.parent.relative_to(base_dir)
    out_dir = out_root / rel
    out_dir.mkdir(parents=True, exist_ok=True)

    # Name from date + subject if possible, else from filename
    subj = fm.get("subject") or eml_path.stem
    date_part = ""
    if fm.get("date"):
        try:
            dt_utc = dt.datetime.fromisoformat(fm["date"].replace("Z", "+00:00"))
            date_part = dt_utc.astimezone().strftime("%Y-%m-%d_%H%M%S_")
        except Exception:
            pass
    out_name = sanitize_filename(f"{date_part}{subj}.md")
    out_path = out_dir / out_name
    out_path.write_text(final_md, encoding="utf-8", newline="\n")
    return out_path

def reformat_md(md_path: Path, base_dir: Path, out_root: Path, use_mdformat: bool = True) -> Path | None:
    enc = detect_encoding(md_path)
    text = md_path.read_text(encoding=enc, errors="replace")

    # If file already has front matter, keep. Else minimal FM with source.
    has_fm = text.lstrip().startswith("---\n")
    if not has_fm:
        fm = {
            "source_file": str(md_path.relative_to(base_dir)),
            "reformatted": True,
        }
        text = compose_markdown(fm, text)

    # Normalize blank lines and quotes before mdformat
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^(\s*>+)\s*", r"\1 ", text, flags=re.MULTILINE)

    # Write temp and run mdformat if available
    rel = md_path.parent.relative_to(base_dir)
    out_dir = out_root / rel
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / sanitize_filename(md_path.stem + ".md")
    out_path.write_text(text, encoding="utf-8", newline="\n")

    if _mdformat_available and use_mdformat:
        # Use API to avoid spawning subshells
        try:
            import mdformat
            formatted = mdformat.text(out_path.read_text(encoding="utf-8"), options={"wrap": "no"})
            # We keep our own wrapping via wrap_paragraphs for paragraphs only
            formatted = wrap_paragraphs(formatted, MAX_LINE)
            out_path.write_text(formatted, encoding="utf-8", newline="\n")
        except Exception as e:
            logging.warning("mdformat failed on %s: %s", out_path, e)
    else:
        logging.warning("mdformat not installed. Skipping Markdown reformatter for %s", out_path)

    return out_path

def main():
    ap = argparse.ArgumentParser(description="Rebuild and clean Gmail EML/MD to professional Markdown.")
    ap.add_argument("--base", default=DEFAULT_BASE, help="Base directory containing year/month subfolders")
    ap.add_argument("--year", default="", help="Optional restrict to a year subfolder, e.g., 2025")
    ap.add_argument("--dry-run", action="store_true", help="Scan only, no writes")
    ap.add_argument("--verbose", action="store_true", help="Verbose logging")
    ap.add_argument("--limit", type=int, default=0, help="Alias of --limit-eml (process at most N EML files)")
    ap.add_argument("--limit-eml", type=int, default=0, help="Process at most this many EML files (0 = no limit)")
    ap.add_argument("--process-md", action="store_true", help="Also reformat existing .md files (off by default)")
    ap.add_argument("--no-mdformat", action="store_true", help="Disable mdformat step even if installed")
    ap.add_argument("--output", default="", help="Optional output root; defaults to <base_parent>/<base_name>_clean")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    # Silence very noisy parsers when verbose
    for noisy in ("markdown_it", "mdformat", "MARKDOWN_IT_DEBUG"):
        try:
            import logging as _logging
            _logging.getLogger(noisy).setLevel(_logging.WARNING)
        except Exception:
            pass

    base_dir = Path(args.base)
    if args.year:
        base_dir = base_dir / args.year

    if not base_dir.exists():
        logging.error("Base directory not found: %s", base_dir)
        sys.exit(2)

    if args.output:
        out_root = Path(args.output)
    else:
        out_root = Path(str(base_dir).rstrip("\\/"))  # inside same tree
        out_root = out_root.parent / (out_root.name + OUTPUT_ROOT_SUFFIX)

    logging.info("Input base: %s", base_dir)
    logging.info("Output root: %s", out_root)

    eml_paths = []
    md_paths = []
    for p in base_dir.rglob("*"):
        if p.is_file():
            if p.suffix.lower() == ".eml":
                eml_paths.append(p)
            elif p.suffix.lower() == ".md":
                md_paths.append(p)

    # Deterministic order for testing
    eml_paths = sorted(eml_paths, key=lambda x: str(x).lower())
    md_paths = sorted(md_paths, key=lambda x: str(x).lower())

    total_eml = len(eml_paths)
    limit = args.limit_eml or args.limit or 0
    if limit and limit > 0:
        eml_paths = eml_paths[: limit]
        logging.info("Found %d EML (limiting to %d) and %d MD files", total_eml, len(eml_paths), len(md_paths))
    else:
        logging.info("Found %d EML and %d MD files", total_eml, len(md_paths))

    # Unless explicitly requested, do not reformat existing Markdown files
    if not args.process_md:
        md_paths = []
        logging.info("Existing Markdown reformat is disabled (enable with --process-md)")
    if args.dry_run:
        return

    processed = 0
    for eml in eml_paths:
        try:
            outp = process_eml(eml, base_dir, out_root)
            processed += 1
            logging.debug("Processed EML -> %s", outp)
        except Exception as e:
            logging.error("Failed EML %s: %s", eml, e)

    for md in md_paths:
        try:
            outp = reformat_md(md, base_dir, out_root, use_mdformat=not args.no_mdformat)
            logging.debug("Reformatted MD -> %s", outp)
        except Exception as e:
            logging.error("Failed MD %s: %s", md, e)

    logging.info("Done. Processed %d EML files. Reformatted %d MD files.", processed, len(md_paths))
    logging.info("Outputs under: %s", out_root)

if __name__ == "__main__":
    main()
