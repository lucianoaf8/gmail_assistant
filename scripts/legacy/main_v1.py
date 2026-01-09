#!/usr/bin/env python3
"""
Gmail Fetcher Suite - Main Orchestrator
=====================================================

Single entry point for all Gmail Fetcher operations.
This script coordinates between core modules, parsers, and tools.

Usage:
    python main.py --help                    # Show all available commands
    python main.py fetch --help              # Show fetch-specific options
    python main.py parse --help              # Show parsing options
    python main.py tools --help              # Show tools and utilities
    python main.py analyze --help            # Show analysis options

Examples:
    python main.py fetch --query "is:unread" --max 1000
    python main.py parse --input backup_folder --format markdown
    python main.py tools cleanup --target backup_folder
    python main.py samples unread            # Run predefined samples
    python main.py analyze --yesterday       # Analyze yesterday's emails
"""

import sys
import argparse
import os
import time
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_argument_parser():
    """Setup the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Gmail Fetcher Suite - Professional email backup and management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Fetch command - Gmail API operations
    fetch_parser = subparsers.add_parser('fetch', help='Download emails from Gmail')
    fetch_parser.add_argument('--query', required=True, help='Gmail search query')
    fetch_parser.add_argument('--max', type=int, default=1000, help='Maximum emails to fetch')
    fetch_parser.add_argument('--output', default='gmail_backup', help='Output directory')
    fetch_parser.add_argument('--format', choices=['eml', 'markdown', 'both'], default='both')
    fetch_parser.add_argument('--organize', choices=['date', 'sender', 'none'], default='date')
    fetch_parser.add_argument('--auth-only', action='store_true', help='Test authentication only')
    
    # Parse command - Email processing and conversion
    parse_parser = subparsers.add_parser('parse', help='Parse and convert email formats')
    parse_parser.add_argument('--input', required=True, help='Input directory or file')
    parse_parser.add_argument('--format', choices=['markdown', 'eml'], default='markdown')
    parse_parser.add_argument('--strategy', choices=['auto', 'readability', 'trafilatura', 'html2text'], default='auto')
    parse_parser.add_argument('--clean', action='store_true', help='Apply cleaning rules')
    
    # Tools command - Utilities and maintenance
    tools_parser = subparsers.add_parser('tools', help='Utilities and maintenance tools')
    tools_subparsers = tools_parser.add_subparsers(dest='tool', help='Available tools')
    
    # Tools subcommands
    cleanup_parser = tools_subparsers.add_parser('cleanup', help='Cleanup and maintenance')
    cleanup_parser.add_argument('--target', required=True, help='Target directory')
    cleanup_parser.add_argument('--type', choices=['markdown', 'duplicates', 'all'], default='all')
    
    ai_parser = tools_subparsers.add_parser('ai-cleanup', help='AI newsletter detection and cleanup')
    ai_parser.add_argument('--input', required=True, help='Email data file (JSON/CSV)')
    ai_parser.add_argument('--delete', action='store_true', help='Actually delete (default: dry run)')
    ai_parser.add_argument('--threshold', type=float, default=0.7, help='Confidence threshold')
    
    # Samples command - Predefined scenarios
    samples_parser = subparsers.add_parser('samples', help='Run predefined sample scenarios')
    samples_parser.add_argument('scenario', choices=['unread', 'newsletters', 'services', 'important', 'list'])
    samples_parser.add_argument('--max', type=int, default=1000, help='Maximum emails for scenario')

    # Analysis command - Daily email analysis
    analysis_parser = subparsers.add_parser('analyze', help='Analyze email patterns and generate insights')
    analysis_parser.add_argument('--input', help='Email backup directory (defaults to gmail_backup)')
    analysis_parser.add_argument('--output', help='Analysis output file (defaults to analysis_results.json)')
    analysis_parser.add_argument('--date', help='Specific date to analyze (YYYY-MM-DD)')
    analysis_parser.add_argument('--yesterday', action='store_true', help='Analyze yesterday\'s emails')
    analysis_parser.add_argument('--days', type=int, default=1, help='Number of days to analyze')
    analysis_parser.add_argument('--config', help='Analysis configuration file')
    analysis_parser.add_argument('--format', choices=['parquet', 'auto'], default='auto',
                                help='Input format (auto-detect or force parquet)')

    # Delete command - Gmail email deletion
    delete_parser = subparsers.add_parser('delete', help='Delete emails from Gmail')
    delete_subparsers = delete_parser.add_subparsers(dest='delete_action', help='Deletion actions')

    # Delete unread command
    unread_parser = delete_subparsers.add_parser('unread', help='Clean unread emails')
    unread_parser.add_argument('--dry-run', action='store_true', default=True, help='Show what would be deleted (default)')
    unread_parser.add_argument('--execute', action='store_true', help='Actually perform deletion')
    unread_parser.add_argument('--keep-recent', type=int, default=0, help='Keep emails from last N days')
    unread_parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')

    # Delete by query command
    query_parser = delete_subparsers.add_parser('query', help='Delete emails by custom query')
    query_parser.add_argument('--query', required=True, help='Gmail search query')
    query_parser.add_argument('--dry-run', action='store_true', default=True, help='Show what would be deleted (default)')
    query_parser.add_argument('--execute', action='store_true', help='Actually perform deletion')
    query_parser.add_argument('--max-delete', type=int, help='Maximum number of emails to delete')
    query_parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')

    # Delete preset command
    preset_parser = delete_subparsers.add_parser('preset', help='Use predefined deletion presets')
    preset_parser.add_argument('preset', choices=['old', 'large', 'newsletters', 'notifications'],
                              help='Preset deletion pattern')
    preset_parser.add_argument('--dry-run', action='store_true', default=True, help='Show what would be deleted (default)')
    preset_parser.add_argument('--execute', action='store_true', help='Actually perform deletion')
    preset_parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')

    # Config command - Configuration management
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('--setup', action='store_true', help='Setup initial configuration')

    return parser

def handle_fetch_command(args):
    """Handle email fetching operations."""
    from src.handlers.fetcher_handler import handle_fetch_command as handler
    handler(args)

def handle_parse_command(args):
    """Handle email parsing and conversion operations."""
    try:
        from parsers.advanced_email_parser import AdvancedEmailParser
        from parsers.gmail_eml_to_markdown_cleaner import EMLToMarkdownConverter
        
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input path does not exist: {input_path}")
            sys.exit(1)
        
        if args.format == 'markdown':
            if input_path.is_file() and input_path.suffix == '.eml':
                # Single EML file conversion
                converter = EMLToMarkdownConverter()
                output_file = input_path.with_suffix('.md')
                converter.convert_eml_file(str(input_path), str(output_file))
                print(f"Success: Converted {input_path} to {output_file}")
            else:
                # Directory conversion
                converter = EMLToMarkdownConverter()
                converter.convert_directory(str(input_path))
                print(f"Success: Converted all EML files in {input_path}")
        
    except ImportError as e:
        print(f"Error: Error importing parser modules: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Error during parse operation: {e}")
        sys.exit(1)

def handle_tools_command(args):
    """Handle tools and utility operations."""
    from src.handlers.tools_handler import handle_tools_command as handler
    handler(args)

def handle_samples_command(args):
    """Handle predefined sample scenarios."""
    from src.handlers.samples_handler import handle_samples_command as handler
    handler(args)

def handle_analysis_command(args):
    """Handle email analysis operations."""
    try:
        from analysis.email_data_converter import EmailDataConverter
        from analysis.daily_email_analysis import EmailAnalysisEngine
        from datetime import datetime, timedelta
        import json

        # Set defaults
        input_dir = Path(args.input) if args.input else Path("gmail_backup")
        output_file = Path(args.output) if args.output else Path("analysis_results.json")
        config_file = Path(args.config) if args.config else Path("src/analysis/daily_analysis_config.json")

        if not input_dir.exists():
            print(f"Input directory not found: {input_dir}")
            print("Use 'python main.py fetch' to download emails first")
            sys.exit(1)

        print(f"Analyzing emails from {input_dir}")

        # Step 1: Convert to Parquet format if needed
        converter = EmailDataConverter(verbose=True)

        if args.format == 'parquet':
            # Input is already Parquet
            parquet_file = input_dir if input_dir.is_file() else input_dir / "emails.parquet"
        else:
            # Convert from EML/Markdown to Parquet
            temp_parquet = Path("temp_analysis_data.parquet")

            if args.date:
                print(f"Converting emails for date: {args.date}")
                count = converter.convert_directory(input_dir, temp_parquet, date_filter=args.date)
            elif args.yesterday:
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"Converting emails for yesterday: {yesterday}")
                count = converter.convert_directory(input_dir, temp_parquet, date_filter=yesterday)
            else:
                print(f"Converting emails for last {args.days} days")
                count = converter.convert_latest_emails(input_dir, temp_parquet, days_back=args.days)

            if count == 0:
                print("No emails found for analysis")
                if temp_parquet.exists():
                    temp_parquet.unlink()
                sys.exit(1)

            parquet_file = temp_parquet

        # Step 2: Load configuration
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            print(f"Warning:  Config file not found: {config_file}, using defaults")
            config = {
                'quality_thresholds': {'min_completeness': 95},
                'log_file': 'logs/email_analysis.log'
            }

        # Step 3: Run analysis
        print("Running email analysis...")
        engine = EmailAnalysisEngine(config)

        # Execute analysis pipeline similar to daily_email_analysis.py main()
        import pandas as pd

        df = pd.read_parquet(parquet_file)
        print(f"   Loaded {len(df)} emails for analysis")

        # Quality assessment
        quality_metrics = engine.analyze_data_quality(df)

        if not quality_metrics['quality_passed']:
            print(f"Error: Quality issues detected: {quality_metrics['quality_issues']}")
            sys.exit(1)

        # Classification and analysis
        start_time = datetime.now()
        df_classified = engine.classify_emails(df)
        temporal_analysis = engine.analyze_temporal_patterns(df_classified)
        sender_analysis = engine.analyze_senders(df_classified)
        content_analysis = engine.analyze_content(df_classified)

        # Generate classification summary
        classification_summary = df_classified['category'].value_counts().to_dict()
        classification_percentages = (df_classified['category'].value_counts() / len(df_classified) * 100).to_dict()

        # Combine results
        analysis_results = {
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_emails': len(df_classified),
                'analysis_duration_seconds': (datetime.now() - start_time).total_seconds(),
                'data_source': str(input_dir),
                'configuration': config
            },
            'quality_metrics': quality_metrics,
            'classification_summary': {
                category: {
                    'count': count,
                    'percentage': round(classification_percentages[category], 2)
                }
                for category, count in classification_summary.items()
            },
            'temporal_analysis': temporal_analysis,
            'sender_analysis': sender_analysis,
            'content_analysis': content_analysis
        }

        # Generate insights
        insights = engine.generate_insights(analysis_results)
        analysis_results['insights'] = insights

        # Save results
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)

        # Clean up temp file if created
        if args.format != 'parquet' and parquet_file.name.startswith('temp_'):
            parquet_file.unlink()

        # Print summary
        duration = analysis_results['metadata']['analysis_duration_seconds']
        print(f"\nEmail Analysis Complete!")
        print(f"   Analyzed: {len(df_classified):,} emails")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Quality: {quality_metrics['completeness']['overall_completeness']:.1f}%")
        print(f"   Results: {output_file}")

        print(f"\nCategory Distribution:")
        for category, stats in analysis_results['classification_summary'].items():
            print(f"   • {category}: {stats['count']} ({stats['percentage']}%)")

        print(f"\nTop Recommendations:")
        for i, rec in enumerate(insights.get('recommendations', [])[:3], 1):
            print(f"   {i}. {rec['recommendation']}")

        print(f"\nAnalysis saved to: {output_file}")

    except ImportError as e:
        print(f"Error importing analysis modules: {e}")
        print("Make sure analysis dependencies are installed: pip install pandas pyarrow")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

def handle_config_command(args):
    """Handle configuration management."""
    config_dir = Path(__file__).parent / "config"
    
    if args.show:
        print("Current configuration:")
        print(f"  Config directory: {config_dir}")
        print(f"  App configs: {list((config_dir / 'app').glob('*.json'))}")
        print(f"  Security files: {list((config_dir / 'security').glob('*.json'))}")
    
    if args.setup:
        print("Setting up initial configuration...")
        # Create config structure if needed
        config_dir.mkdir(exist_ok=True)
        (config_dir / "app").mkdir(exist_ok=True)
        (config_dir / "security").mkdir(exist_ok=True)
        print("Success: Configuration directories created")
        print("Place your credentials.json file in config/security/")

def handle_delete_command(args):
    """Handle email deletion operations with comprehensive safety checks."""
    try:
        from deletion.deleter import GmailDeleter
        from deletion.ui import clean_unread_inbox
        import logging
        from pathlib import Path

        # Setup logging for deletion operations
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"deletion_{args.delete_action}_{time.strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info(f"Starting deletion operation: {args.delete_action}")

        # Initialize deleter with credentials
        credentials_path = Path(__file__).parent / "config" / "security" / "credentials.json"
        if not credentials_path.exists():
            print("Error: Gmail API credentials not found!")
            print(f"Please place credentials.json in: {credentials_path}")
            sys.exit(1)

        deleter = GmailDeleter(credentials_file=str(credentials_path))

        # Determine dry-run mode (default is True for safety)
        dry_run = not args.execute if hasattr(args, 'execute') else True

        if args.delete_action == 'unread':
            logger.info("Processing unread inbox cleanup")
            result = clean_unread_inbox(
                deleter=deleter,
                dry_run=dry_run,
                keep_recent_days=getattr(args, 'keep_recent', 0)
            )

        elif args.delete_action == 'query':
            logger.info(f"Processing custom query: {args.query}")
            if dry_run:
                print(f"🧪 DRY RUN: Would delete emails matching: {args.query}")
                count = deleter.get_email_count(args.query)
                print(f"Running Found {count:,} emails matching query")
                result = {'deleted': 0, 'failed': 0}
            else:
                result = deleter.delete_by_query(
                    query=args.query,
                    dry_run=False,
                    max_delete=getattr(args, 'max_delete', None)
                )

        elif args.delete_action == 'preset':
            preset_queries = {
                'old': 'older_than:1y',
                'large': 'larger:10M',
                'newsletters': 'is:unread (newsletter OR unsubscribe)',
                'notifications': 'is:unread (notification OR alert OR backup)'
            }

            query = preset_queries[args.preset]
            logger.info(f"Processing preset '{args.preset}' with query: {query}")

            if dry_run:
                print(f"🧪 DRY RUN: Would delete emails using preset '{args.preset}'")
                print(f"📝 Query: {query}")
                count = deleter.get_email_count(query)
                print(f"Running Found {count:,} emails matching preset")
                result = {'deleted': 0, 'failed': 0}
            else:
                result = deleter.delete_by_query(query=query, dry_run=False)

        # Log results
        logger.info(f"Deletion completed - Deleted: {result.get('deleted', 0)}, Failed: {result.get('failed', 0)}")
        print(f"Running Results logged to: {log_file}")

    except ImportError as e:
        print(f"Error: Error importing deletion modules: {e}")
        print("Make sure the deletion module is properly installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Error during deletion operation: {e}")
        if 'logger' in locals():
            logger.error(f"Deletion failed: {e}")
        sys.exit(1)

def main():
    """Main entry point for the Gmail Fetcher Suite."""
    parser = setup_argument_parser()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Route to appropriate handler
    if args.command == 'fetch':
        handle_fetch_command(args)
    elif args.command == 'parse':
        handle_parse_command(args)
    elif args.command == 'tools':
        handle_tools_command(args)
    elif args.command == 'samples':
        handle_samples_command(args)
    elif args.command == 'analyze':
        handle_analysis_command(args)
    elif args.command == 'delete':
        handle_delete_command(args)
    elif args.command == 'config':
        handle_config_command(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()