"""
Analysis handler for Gmail Fetcher main interface.
Handles email analysis operations with proper validation and error handling.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def handle_analysis_command(args: Any) -> None:
    """
    Handle email analysis operations.

    Args:
        args: Parsed command line arguments
    """
    try:
        # Import analysis modules
        from gmail_assistant.analysis.email_data_converter import EmailDataConverter
        from gmail_assistant.analysis.daily_email_analysis import EmailAnalysisEngine

        # Validate and set defaults
        input_dir = _validate_input_directory(args)
        output_file = _validate_output_file(args)
        config_file = _validate_config_file(args)

        print(f"Analyzing emails from {input_dir}")

        # Convert emails to analysis format
        parquet_file = _convert_emails_to_parquet(args, input_dir)

        if not parquet_file:
            print("No emails found for analysis")
            sys.exit(1)

        # Perform analysis
        _perform_analysis(parquet_file, config_file, output_file)

    except Exception as e:
        error_msg = f"Error during analysis: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        sys.exit(1)


def _validate_input_directory(args: Any) -> Path:
    """
    Validate input directory for analysis.

    Args:
        args: Command line arguments

    Returns:
        Validated input directory path

    Raises:
        SystemExit: If input directory is invalid
    """
    input_dir = Path(args.input) if args.input else Path("gmail_backup")

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        print("Use 'python main.py fetch' to download emails first")
        sys.exit(1)

    return input_dir


def _validate_output_file(args: Any) -> Path:
    """
    Validate output file for analysis results.

    Args:
        args: Command line arguments

    Returns:
        Validated output file path
    """
    return Path(args.output) if args.output else Path("analysis_results.json")


def _validate_config_file(args: Any) -> Path:
    """
    Validate configuration file for analysis.

    Args:
        args: Command line arguments

    Returns:
        Validated config file path
    """
    return Path(args.config) if args.config else Path("src/analysis/daily_analysis_config.json")


def _convert_emails_to_parquet(args: Any, input_dir: Path) -> Path:
    """
    Convert emails to Parquet format for analysis.

    Args:
        args: Command line arguments
        input_dir: Input directory path

    Returns:
        Path to Parquet file, or None if no emails found
    """
    converter = EmailDataConverter(verbose=True)

    if args.format == 'parquet':
        # Input is already Parquet
        return input_dir if input_dir.is_file() else input_dir / "emails.parquet"

    # Convert from EML/Markdown to Parquet
    temp_parquet = Path("temp_analysis_data.parquet")

    try:
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
            if temp_parquet.exists():
                temp_parquet.unlink()
            return None

        return temp_parquet

    except Exception as e:
        logger.error(f"Error converting emails to Parquet: {e}")
        if temp_parquet.exists():
            temp_parquet.unlink()
        raise


def _perform_analysis(parquet_file: Path, config_file: Path, output_file: Path) -> None:
    """
    Perform email analysis.

    Args:
        parquet_file: Path to Parquet data file
        config_file: Path to analysis configuration
        output_file: Path for analysis results
    """
    # Load configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_file}, using defaults")
        config = {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        config = {}

    # Run analysis
    engine = EmailAnalysisEngine(config)
    results = engine.analyze_parquet(str(parquet_file))

    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Analysis completed: {output_file}")

    # Clean up temporary files
    if parquet_file.name.startswith("temp_"):
        parquet_file.unlink()
        logger.info("Cleaned up temporary Parquet file")