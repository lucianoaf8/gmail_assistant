"""Analyze command implementation (C-2 fix)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from gmail_assistant.core.exceptions import ConfigError
from gmail_assistant.utils.secure_logger import SecureLogger

logger = SecureLogger(__name__)


def analyze_emails(
    input_dir: Path,
    report_type: str = "summary",
    output_file: Path | None = None,
    date_filter: str | None = None
) -> dict[str, Any]:
    """
    Analyze fetched emails (C-2 implementation).

    Args:
        input_dir: Directory containing fetched emails
        report_type: Type of report (summary, detailed, json)
        output_file: Optional output file for report
        date_filter: Optional date filter (YYYY-MM-DD)

    Returns:
        Dict with analysis results

    Raises:
        ConfigError: If input directory is invalid
    """
    if not input_dir.exists():
        raise ConfigError(f"Input directory not found: {input_dir}")

    # Collect email files
    email_files = list(input_dir.glob("**/*.json")) + list(input_dir.glob("**/*.eml"))

    if not email_files:
        click.echo("No email files found in directory")
        return {'total': 0, 'analyzed': 0}

    click.echo(f"Found {len(email_files)} email files")

    # Basic analysis without pandas dependency
    analysis = {
        'metadata': {
            'analysis_timestamp': datetime.now().isoformat(),
            'source_directory': str(input_dir),
            'total_files': len(email_files),
            'report_type': report_type
        },
        'file_statistics': _analyze_file_statistics(email_files),
        'temporal_distribution': _analyze_temporal_distribution(email_files),
        'category_summary': {},
        'sender_summary': {}
    }

    # Parse JSON files for detailed analysis
    json_files = [f for f in email_files if f.suffix == '.json']
    if json_files:
        emails_data = []
        for jf in json_files[:1000]:  # Limit for performance
            try:
                with open(jf, encoding='utf-8') as f:
                    emails_data.append(json.load(f))
            except (OSError, json.JSONDecodeError):
                continue

        if emails_data:
            analysis['sender_summary'] = _analyze_senders(emails_data)
            analysis['category_summary'] = _classify_emails(emails_data)

    # Generate report
    if report_type == "json":
        _output_json_report(analysis, output_file)
    elif report_type == "detailed":
        _output_detailed_report(analysis, output_file)
    else:
        _output_summary_report(analysis)

    return analysis


def _analyze_file_statistics(files: list) -> dict[str, Any]:
    """Analyze file statistics."""
    extensions = {}
    total_size = 0

    for f in files:
        ext = f.suffix.lower()
        extensions[ext] = extensions.get(ext, 0) + 1
        try:
            total_size += f.stat().st_size
        except OSError:
            continue

    return {
        'by_extension': extensions,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2)
    }


def _analyze_temporal_distribution(files: list) -> dict[str, Any]:
    """Analyze temporal distribution based on file organization."""
    years = {}
    months = {}

    for f in files:
        parts = f.parts
        for part in parts:
            if part.isdigit():
                if len(part) == 4:  # Year
                    years[part] = years.get(part, 0) + 1
                elif len(part) == 2:  # Month
                    months[part] = months.get(part, 0) + 1

    return {
        'by_year': dict(sorted(years.items())),
        'by_month': dict(sorted(months.items()))
    }


def _analyze_senders(emails: list) -> dict[str, Any]:
    """Analyze sender patterns."""
    senders = {}

    for email in emails:
        sender = email.get('sender', email.get('from', 'unknown'))
        # Extract domain
        sender.split('@')[-1].rstrip('>') if '@' in sender else sender

        senders[sender] = senders.get(sender, 0) + 1

    # Sort by count
    sorted_senders = dict(sorted(senders.items(), key=lambda x: x[1], reverse=True)[:20])

    return {
        'unique_senders': len(senders),
        'top_senders': sorted_senders
    }


def _classify_emails(emails: list) -> dict[str, Any]:
    """Simple email classification."""
    categories = {
        'Financial': 0,
        'Notifications': 0,
        'Marketing': 0,
        'Social': 0,
        'Other': 0
    }

    financial_kw = ['payment', 'invoice', 'bill', 'receipt', 'bank', 'card']
    notification_kw = ['notification', 'alert', 'reminder', 'update']
    marketing_kw = ['newsletter', 'unsubscribe', 'offer', 'deal', 'sale']
    social_kw = ['friend', 'follow', 'like', 'comment', 'share']

    for email in emails:
        subject = (email.get('subject', '') or '').lower()
        sender = (email.get('sender', '') or '').lower()
        combined = subject + ' ' + sender

        if any(kw in combined for kw in financial_kw):
            categories['Financial'] += 1
        elif any(kw in combined for kw in notification_kw):
            categories['Notifications'] += 1
        elif any(kw in combined for kw in marketing_kw):
            categories['Marketing'] += 1
        elif any(kw in combined for kw in social_kw):
            categories['Social'] += 1
        else:
            categories['Other'] += 1

    total = sum(categories.values())
    return {
        'counts': categories,
        'percentages': {k: round(v / total * 100, 1) if total > 0 else 0
                       for k, v in categories.items()}
    }


def _output_summary_report(analysis: dict[str, Any]) -> None:
    """Output summary report to console."""
    click.echo("\n" + "=" * 50)
    click.echo("EMAIL ANALYSIS SUMMARY")
    click.echo("=" * 50)

    meta = analysis['metadata']
    click.echo(f"\nAnalyzed: {meta['total_files']} files")
    click.echo(f"Timestamp: {meta['analysis_timestamp']}")

    stats = analysis['file_statistics']
    click.echo(f"\nTotal size: {stats['total_size_mb']} MB")
    click.echo("File types:")
    for ext, count in stats['by_extension'].items():
        click.echo(f"  {ext}: {count} files")

    if analysis['category_summary']:
        click.echo("\nCategory distribution:")
        for cat, pct in analysis['category_summary'].get('percentages', {}).items():
            click.echo(f"  {cat}: {pct}%")

    if analysis['sender_summary']:
        click.echo(f"\nUnique senders: {analysis['sender_summary']['unique_senders']}")
        click.echo("Top senders:")
        for sender, count in list(analysis['sender_summary']['top_senders'].items())[:5]:
            click.echo(f"  {sender[:50]}: {count}")


def _output_detailed_report(analysis: dict[str, Any], output_file: Path | None) -> None:
    """Output detailed report."""
    _output_summary_report(analysis)

    click.echo("\n" + "-" * 50)
    click.echo("DETAILED ANALYSIS")
    click.echo("-" * 50)

    # Temporal distribution
    temporal = analysis['temporal_distribution']
    if temporal['by_year']:
        click.echo("\nEmails by year:")
        for year, count in temporal['by_year'].items():
            click.echo(f"  {year}: {count}")

    # Full sender list
    if analysis['sender_summary']:
        click.echo("\nAll top senders:")
        for sender, count in analysis['sender_summary']['top_senders'].items():
            click.echo(f"  {sender}: {count}")

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str)
        click.echo(f"\nDetailed report saved to: {output_file}")


def _output_json_report(analysis: dict[str, Any], output_file: Path | None) -> None:
    """Output JSON report."""
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str)
        click.echo(f"JSON report saved to: {output_file}")
    else:
        click.echo(json.dumps(analysis, indent=2, default=str))


__all__ = ['analyze_emails']
