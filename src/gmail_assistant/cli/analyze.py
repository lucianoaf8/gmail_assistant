"""
Analyze command for Gmail Fetcher CLI.

Analyzes email patterns and generates insights.
"""

import logging
from argparse import ArgumentParser, _SubParsersAction
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def setup_parser(subparsers: _SubParsersAction) -> ArgumentParser:
    """
    Setup the analyze command parser.

    Args:
        subparsers: Parent subparsers object

    Returns:
        Configured ArgumentParser for analyze command
    """
    parser = subparsers.add_parser(
        'analyze',
        help='Analyze email patterns and generate insights',
        description='Analyze email patterns from backup data'
    )

    # Input/output arguments
    parser.add_argument(
        '--input', '-i',
        default='gmail_backup',
        help='Email backup directory (default: gmail_backup)'
    )

    parser.add_argument(
        '--output', '-o',
        default='analysis_results.json',
        help='Analysis output file (default: analysis_results.json)'
    )

    # Date filtering
    parser.add_argument(
        '--date',
        help='Specific date to analyze (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--yesterday',
        action='store_true',
        help="Analyze yesterday's emails"
    )

    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of days to analyze (default: 1)'
    )

    # Configuration
    parser.add_argument(
        '--config',
        help='Analysis configuration file'
    )

    parser.add_argument(
        '--format',
        choices=['parquet', 'auto'],
        default='auto',
        help='Input format (default: auto-detect)'
    )

    # Output options
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Only show summary, do not save full results'
    )

    return parser


def handle(args: Any) -> int:
    """
    Handle the analyze command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        import json

        # Validate input directory
        input_dir = Path(args.input)
        if not input_dir.exists():
            print(f"Error: Input directory not found: {input_dir}")
            print("Use 'gmail-fetcher fetch' to download emails first")
            return 1

        # Determine date filter
        date_filter = None
        if args.date:
            date_filter = args.date
        elif args.yesterday:
            date_filter = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        print(f"Analyzing emails from: {input_dir}")
        if date_filter:
            print(f"Date filter: {date_filter}")

        # Try to import analysis modules
        try:
            from gmail_assistant.analysis.daily_email_analyzer import DailyEmailAnalyzer

            analyzer = DailyEmailAnalyzer()

            # Run analysis
            results = analyzer.analyze(
                input_dir=str(input_dir),
                date_filter=date_filter,
                days=args.days
            )

            # Display summary
            _display_summary(results)

            # Save results unless summary-only
            if not args.summary_only:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, default=str)

                print(f"\nResults saved to: {output_path}")

            return 0

        except ImportError:
            # Fall back to simple analysis
            return _simple_analysis(input_dir, args)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


def _display_summary(results: dict) -> None:
    """Display analysis summary."""
    print("\n" + "=" * 50)
    print("EMAIL ANALYSIS SUMMARY")
    print("=" * 50)

    metadata = results.get('metadata', {})
    print(f"\nTotal emails analyzed: {metadata.get('total_emails', 'unknown'):,}")
    print(f"Analysis duration: {metadata.get('analysis_duration_seconds', 0):.2f}s")

    # Category distribution
    categories = results.get('classification_summary', {})
    if categories:
        print("\nCategory Distribution:")
        for category, stats in categories.items():
            if isinstance(stats, dict):
                count = stats.get('count', 0)
                pct = stats.get('percentage', 0)
            else:
                count = stats
                pct = 0
            print(f"  - {category}: {count:,} ({pct:.1f}%)")

    # Top senders
    sender_analysis = results.get('sender_analysis', {})
    top_senders = sender_analysis.get('top_senders', [])[:5]
    if top_senders:
        print("\nTop Senders:")
        for sender in top_senders:
            name = sender.get('sender', 'unknown')
            count = sender.get('count', 0)
            print(f"  - {name}: {count:,} emails")

    # Insights
    insights = results.get('insights', {})
    recommendations = insights.get('recommendations', [])[:3]
    if recommendations:
        print("\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            text = rec.get('recommendation', rec) if isinstance(rec, dict) else rec
            print(f"  {i}. {text}")


def _simple_analysis(input_dir: Path, args: Any) -> int:
    """Perform simple file-based analysis when modules are not available."""
    print("Performing simple file analysis...")

    # Count files by type
    eml_files = list(input_dir.rglob("*.eml"))
    md_files = list(input_dir.rglob("*.md"))

    print(f"\nFile counts:")
    print(f"  - EML files: {len(eml_files):,}")
    print(f"  - Markdown files: {len(md_files):,}")

    # Count by directory (organization)
    if eml_files:
        dirs = set(f.parent for f in eml_files)
        print(f"  - Directories: {len(dirs):,}")

    # Get date range from filenames
    dates = []
    for f in eml_files[:1000]:  # Sample first 1000
        if f.name[:10].replace('-', '').isdigit():
            try:
                date_str = f.name[:10]
                dates.append(date_str)
            except Exception:
                pass

    if dates:
        dates.sort()
        print(f"\nDate range:")
        print(f"  - Oldest: {dates[0]}")
        print(f"  - Newest: {dates[-1]}")

    return 0
