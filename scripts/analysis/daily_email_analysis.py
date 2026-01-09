#!/usr/bin/env python3
"""
Daily Email Analysis - CLI Script
Command-line interface for running comprehensive email analysis with the Gmail Fetcher data.

Usage:
    python daily_email_analysis.py --input data.parquet --yesterday
    python daily_email_analysis.py --input data.parquet --date 2025-09-18
    python daily_email_analysis.py --input data.parquet --date-range 2025-09-01 2025-09-18
"""

import sys
import argparse
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Add the src directory to the path so we can import our analysis modules
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from analysis.daily_email_analyzer import DailyEmailAnalyzer


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging for the CLI script"""
    logger = logging.getLogger('daily_email_analysis_cli')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def load_email_data(input_path: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Load email data from various file formats
    
    Args:
        input_path: Path to input data file
        logger: Logger instance
        
    Returns:
        DataFrame with email data
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from: {input_path}")
    
    # Determine file format and load accordingly
    if input_file.suffix.lower() == '.parquet':
        df = pd.read_parquet(input_path)
    elif input_file.suffix.lower() == '.csv':
        df = pd.read_csv(input_path)
    elif input_file.suffix.lower() == '.json':
        df = pd.read_json(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_file.suffix}")
    
    logger.info(f"Loaded {len(df)} records")
    
    # Validate required columns
    required_columns = ['gmail_id', 'date_received', 'subject', 'sender', 'plain_text_content']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}")
        # Create empty columns for missing ones
        for col in missing_columns:
            if col == 'gmail_id':
                df[col] = df.index.astype(str)
            else:
                df[col] = ''
    
    return df


def filter_by_date(df: pd.DataFrame, date_filter: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Filter DataFrame by date criteria
    
    Args:
        df: DataFrame with email data
        date_filter: Date filter type ('yesterday', specific date, etc.)
        logger: Logger instance
        
    Returns:
        Filtered DataFrame
    """
    if 'date_received' not in df.columns:
        logger.warning("No date_received column found, skipping date filtering")
        return df
    
    # Ensure date column is datetime
    df['date_received'] = pd.to_datetime(df['date_received'])
    
    if date_filter == 'yesterday':
        target_date = (datetime.now() - timedelta(days=1)).date()
        logger.info(f"Filtering for yesterday: {target_date}")
        df_filtered = df[df['date_received'].dt.date == target_date]
    else:
        # Assume it's a specific date in YYYY-MM-DD format
        try:
            target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            logger.info(f"Filtering for date: {target_date}")
            df_filtered = df[df['date_received'].dt.date == target_date]
        except ValueError:
            logger.error(f"Invalid date format: {date_filter}. Use YYYY-MM-DD format.")
            return df
    
    logger.info(f"Filtered to {len(df_filtered)} emails for {target_date}")
    return df_filtered


def filter_by_date_range(df: pd.DataFrame, start_date: str, end_date: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Filter DataFrame by date range
    
    Args:
        df: DataFrame with email data
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        logger: Logger instance
        
    Returns:
        Filtered DataFrame
    """
    if 'date_received' not in df.columns:
        logger.warning("No date_received column found, skipping date filtering")
        return df
    
    # Ensure date column is datetime
    df['date_received'] = pd.to_datetime(df['date_received'])
    
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        logger.info(f"Filtering for date range: {start_date} to {end_date}")
        
        mask = (df['date_received'] >= start_dt) & (df['date_received'] <= end_dt)
        df_filtered = df[mask]
        
        logger.info(f"Filtered to {len(df_filtered)} emails in date range")
        return df_filtered
        
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return df


def save_results(results: dict, output_path: str, format_type: str, logger: logging.Logger):
    """
    Save analysis results to file
    
    Args:
        results: Analysis results dictionary
        output_path: Output file path
        format_type: Output format ('json', 'csv')
        logger: Logger instance
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if format_type.lower() == 'json':
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to: {output_file}")
        
    elif format_type.lower() == 'csv':
        # Save summary data to CSV
        summary_data = []
        
        if 'classification_summary' in results:
            for category, stats in results['classification_summary'].items():
                summary_data.append({
                    'category': category,
                    'count': stats.get('count', 0),
                    'percentage': stats.get('percentage', 0),
                    'confidence': stats.get('average_confidence', 0)
                })
        
        if summary_data:
            df_summary = pd.DataFrame(summary_data)
            csv_file = output_file.with_suffix('.csv')
            df_summary.to_csv(csv_file, index=False)
            logger.info(f"Summary CSV saved to: {csv_file}")
        
        # Also save full JSON
        json_file = output_file.with_suffix('.json')
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Full results saved to: {json_file}")
    
    else:
        logger.error(f"Unsupported output format: {format_type}")


def print_summary(results: dict, logger: logging.Logger):
    """Print a summary of analysis results to console"""
    if 'error' in results:
        logger.error(f"Analysis failed: {results['error']}")
        return
    
    metadata = results.get('metadata', {})
    classification = results.get('classification_summary', {})
    insights = results.get('insights', {})
    
    print("\n" + "=" * 60)
    print("📊 DAILY EMAIL ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Analysis Date: {metadata.get('analysis_timestamp', 'Unknown')[:19]}")
    print(f"Total Emails: {metadata.get('total_emails', 0):,}")
    print(f"Processing Time: {metadata.get('analysis_duration_seconds', 0):.2f} seconds")
    
    # Quality metrics
    quality = results.get('quality_metrics', {})
    if quality:
        completeness = quality.get('completeness', {}).get('overall_completeness', 0)
        quality_passed = quality.get('quality_passed', False)
        status = "✅ PASSED" if quality_passed else "❌ FAILED"
        print(f"Data Quality: {completeness:.1f}% complete - {status}")
    
    print("\n📈 CATEGORY DISTRIBUTION:")
    for category, stats in sorted(classification.items(), 
                                key=lambda x: x[1].get('percentage', 0), reverse=True):
        count = stats.get('count', 0)
        percentage = stats.get('percentage', 0)
        confidence = stats.get('average_confidence', 0)
        print(f"  {category:20s}: {count:4,} emails ({percentage:5.1f}%) [conf: {confidence:.2f}]")
    
    # Automation analysis
    sender_analysis = results.get('sender_analysis', {})
    automation = sender_analysis.get('automation_analysis', {})
    if automation:
        automation_rate = automation.get('automation_rate', 0)
        automated_count = automation.get('automated_emails', 0)
        personal_count = automation.get('personal_emails', 0)
        
        print(f"\n🤖 AUTOMATION ANALYSIS:")
        print(f"  Automated emails: {automated_count:,} ({automation_rate:.1f}%)")
        print(f"  Personal emails:  {personal_count:,} ({100-automation_rate:.1f}%)")
    
    # Top recommendations
    recommendations = insights.get('recommendations', [])
    if recommendations:
        print(f"\n🎯 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:3], 1):
            priority = rec.get('priority', 'Medium')
            category = rec.get('category', 'General')
            recommendation = rec.get('recommendation', '')
            print(f"  {i}. [{priority}] {category}: {recommendation}")
    
    # Volume insights
    temporal = results.get('temporal_analysis', {})
    volume_patterns = temporal.get('volume_patterns', {})
    if volume_patterns:
        daily_avg = volume_patterns.get('daily_average', 0)
        peak_day = volume_patterns.get('peak_day', {})
        
        print(f"\n📅 VOLUME PATTERNS:")
        print(f"  Daily average: {daily_avg:.1f} emails")
        if peak_day:
            print(f"  Peak day: {peak_day.get('date', 'Unknown')} ({peak_day.get('volume', 0)} emails)")
    
    print("=" * 60)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Daily Email Analysis - Comprehensive email analytics for Gmail data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze yesterday's emails
  python daily_email_analysis.py --input data/emails.parquet --yesterday
  
  # Analyze specific date
  python daily_email_analysis.py --input data/emails.parquet --date 2025-09-18
  
  # Analyze date range
  python daily_email_analysis.py --input data/emails.parquet --date-range 2025-09-01 2025-09-18
  
  # Use custom config and output
  python daily_email_analysis.py --input data/emails.parquet --yesterday \\
    --config config/my_config.json --output results/analysis.json
        """
    )
    
    # Required arguments
    parser.add_argument('--input', required=True, help='Input email data file (parquet, csv, or json)')
    
    # Date filtering (mutually exclusive)
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument('--yesterday', action='store_true', help='Analyze yesterday\'s emails')
    date_group.add_argument('--date', help='Analyze specific date (YYYY-MM-DD)')
    date_group.add_argument('--date-range', nargs=2, metavar=('START', 'END'), 
                           help='Analyze date range (YYYY-MM-DD YYYY-MM-DD)')
    
    # Optional arguments
    parser.add_argument('--config', default='config/analysis/0922-1430_daily_analysis_config.json',
                       help='Configuration file path')
    parser.add_argument('--output', help='Output file path (auto-generated if not specified)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    try:
        # Load data
        df = load_email_data(args.input, logger)
        
        if len(df) == 0:
            logger.error("No data found in input file")
            sys.exit(1)
        
        # Apply date filtering if specified
        if args.yesterday:
            df = filter_by_date(df, 'yesterday', logger)
        elif args.date:
            df = filter_by_date(df, args.date, logger)
        elif args.date_range:
            df = filter_by_date_range(df, args.date_range[0], args.date_range[1], logger)
        
        if len(df) == 0:
            logger.error("No emails found matching date criteria")
            sys.exit(1)
        
        # Initialize analyzer
        logger.info(f"Initializing analyzer with config: {args.config}")
        analyzer = DailyEmailAnalyzer(args.config)
        
        # Run analysis
        logger.info("Starting comprehensive email analysis...")
        results = analyzer.analyze_emails(df)
        
        # Generate output filename if not specified
        if not args.output:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if args.yesterday:
                date_suffix = 'yesterday'
            elif args.date:
                date_suffix = args.date.replace('-', '')
            elif args.date_range:
                date_suffix = f"{args.date_range[0].replace('-', '')}_to_{args.date_range[1].replace('-', '')}"
            else:
                date_suffix = 'all'
            
            output_dir = Path('output/daily')
            output_dir.mkdir(parents=True, exist_ok=True)
            args.output = output_dir / f"analysis_{date_suffix}_{timestamp}.{args.format}"
        
        # Save results
        save_results(results, args.output, args.format, logger)
        
        # Print summary to console (unless quiet mode)
        if not args.quiet:
            print_summary(results, logger)
        
        # Check for critical issues
        if 'error' in results:
            logger.error("Analysis completed with errors")
            sys.exit(1)
        
        quality_passed = results.get('quality_metrics', {}).get('quality_passed', True)
        if not quality_passed:
            logger.warning("Analysis completed but quality issues detected")
            sys.exit(2)
        
        logger.info("Analysis completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        if args.log_level == 'DEBUG':
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()