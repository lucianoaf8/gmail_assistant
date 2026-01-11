# Gmail Markdown Cleanup Script Plan

The `tools/cleanup_markdown.py` script is a scaffold for transforming raw Gmail-exported Markdown
into consistent, readable documents. This guide explains what the finished script should do,
how its pipeline is structured, and which behaviours you still need to implement.

## Goals

The fixer should:

- normalise line endings, whitespace, and encoding issues so each file renders cleanly across platforms;
- recognise and repair newsletter-style artefacts (pseudo tables, broken buttons, escaped bullets, etc.);
- keep genuine content intact while reorganising it into idiomatic Markdown (headings, lists, paragraphs);
- preserve idempotency so rerunning the script produces no further diffs;
- emit backups and change summaries so large batches can be audited safely.

## Processing Pipeline Overview

The script processes each file as a list of lines. Extend the following stages with real logic:

1. **`normalise_line_endings`** – standardise to `\n`, strip stray carriage returns, ensure every line ends with a newline.
2. **`tidy_front_matter`** – collapse duplicate "Email Details" blocks, rebuild the header table with consistent columns, and remove empty rows.
3. **`join_wrapped_urls`** – detect URLs that broke across lines and join them; reference-style links are preferred for long tracking URLs.
4. **`fix_escaped_lists`** – convert leading `\+` / `\-` characters into proper bullets; ensure numbered lists are formatted as Markdown lists.
5. **`remove_empty_pipe_rows`** – drop faux tables (`|  |`, repeated `---`) or replace them with paragraphs/lists depending on context.
6. **`rebuild_lists_and_paragraphs`** – merge arbitrarily wrapped sentences, split multi-topic paragraphs, and insert blank lines between logical blocks.
7. **`restore_unicode`** – map placeholder sequences (`??`, `(R)`, etc.) back to real emoji/symbols; warn when ambiguous.

Add additional transforms as you encounter patterns (CTA buttons, boilerplate folding, image alt text fixes, etc.).

## Expected Behaviours

- **Backup creation:** before writing changes, store the original file as `<name>.md.bak` unless a backup already exists.
- **Dry-run mode:** `--dry-run` should log which files *would* change without touching disk.
- **Stats-only mode:** `--stats-only` should report change counts (e.g., line deltas, detected issues) without writing files.
- **Idempotency check:** after running the pipeline once, run it again in memory. If the MD5 hash differs, log a warning and adopt the stabilised result.
- **Logging:** provide INFO-level summaries by default (`Processed N files; M modified.`) and DEBUG-level insights for individual transforms when needed.

## CLI Usage

General pattern:

```bash
python tools/cleanup_markdown.py [options] <files-and-or-directories>
```

Important flags:

- `-r / --recursive` – traverse subdirectories for `*.md` files.
- `-n / --dry-run` – preview changes only.
- `-l / --limit N` – stop after the first N matched files.
- `--stats-only` – inspect without rewriting.
- `--log-level LEVEL` – set verbosity (`DEBUG`, `INFO`, etc.).

## Extending the Script

When you implement a new fix:

1. Add a dedicated transform function (keep them pure: inputs/outputs are lists of strings).
2. Append the function to `PIPELINE` in the correct order.
3. Write unit tests (e.g., `tests/test_cleanup_pipeline.py`) using small fixtures that capture the malformed input and expected output.
4. Update this document or inline docstrings to explain the behaviour.

## Suggested Test Harness

- Create `tests/fixtures/broken/*.md` files representing real failure cases (wrapped URLs, escaped bullets, newsletter CTAs, etc.).
- Write pytest functions that load each fixture, pass it through `apply_pipeline`, and compare the result with companion `expected/*.md` files.
- Include tests for idempotency: run the pipeline twice on an already-clean file and assert no modifications occur.

## Operational Checklist

Before running against the full archive:

1. Implement the highest-value transforms (URL unwrap, faux-table dismantle, escaped list repair, CTA conversion).
2. Dry-run against a 25–50 file sample: `python tools/cleanup_markdown.py -r --limit 50 --dry-run backup_unread`.
3. Review logs and generated backups; adjust transforms as needed.
4. Remove `--dry-run` and process the full set, keeping an eye on the summary stats.
5. Spot-check a handful of cleaned files in a Markdown renderer to verify readability.

## Future Enhancements

- Integrate a Markdown linter (`markdownlint-cli2`) as a post-processing check.
- Produce a JSON or CSV report summarising fixes per file (count of URLs unwrapped, tables rebuilt, etc.).
- Add a `--fold-boilerplate` option to wrap long legal/privacy sections in `<details>` blocks.
- Provide a `--report-only` mode that lists files needing manual review (e.g., non-idempotent, excessive changes).

Keep this document up to date as you implement each transformer so anyone running the script understands its scope and guarantees.
