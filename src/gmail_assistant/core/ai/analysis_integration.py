#!/usr/bin/env python3
"""
Gmail Fetcher Analysis Integration
Seamless integration between Gmail Fetcher and Daily Email Analysis systems.

This module provides integration points for:
- Automated analysis after Gmail fetching
- Configuration sharing and management
- Output format standardization
- Workflow orchestration
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class GmailAnalysisIntegration:
    """
    Integration orchestrator for Gmail Fetcher and Email Analysis
    
    Provides seamless workflow integration including:
    - Automated analysis pipeline
    - Configuration management
    - Output coordination
    - Performance monitoring
    """

    def __init__(self, base_dir: str | None = None):
        """
        Initialize the integration system
        
        Args:
            base_dir: Base directory for the Gmail Fetcher project
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.logger = self._setup_logging()

        # Integration paths
        self.gmail_assistant_script = self.base_dir / 'gmail_assistant.py'
        self.analysis_script = self.base_dir / 'scripts' / 'analysis' / 'daily_email_analysis.py'
        self.analysis_config = self.base_dir / 'config' / 'analysis' / '0922-1430_daily_analysis_config.json'

        # Output directories
        self.gmail_backup_dir = self.base_dir / 'gmail_backup'
        self.analysis_output_dir = self.base_dir / 'output' / 'daily'

        # Ensure directories exist
        self.analysis_output_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for integration operations"""
        logger = logging.getLogger('GmailAnalysisIntegration')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # Create logs directory
            log_dir = self.base_dir / 'logs'
            log_dir.mkdir(exist_ok=True)

            # File handler
            file_handler = logging.FileHandler(log_dir / 'integration.log')
            console_handler = logging.StreamHandler()

            # Formatter
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def run_integrated_workflow(self,
                               gmail_query: str,
                               max_emails: int = 1000,
                               analysis_date: str | None = None,
                               gmail_format: str = "both",
                               gmail_organize: str = "date") -> dict[str, Any]:
        """
        Run integrated Gmail fetch + analysis workflow
        
        Args:
            gmail_query: Gmail search query
            max_emails: Maximum emails to fetch
            analysis_date: Date for analysis ('yesterday', 'YYYY-MM-DD', or None for all)
            gmail_format: Gmail fetcher output format
            gmail_organize: Gmail fetcher organization method
            
        Returns:
            Dict with workflow results including Gmail fetch and analysis results
        """
        workflow_start = datetime.now()
        self.logger.info("🚀 Starting integrated Gmail fetch + analysis workflow")

        try:
            # Step 1: Run Gmail Fetcher
            self.logger.info("Step 1: Fetching emails from Gmail...")
            gmail_result = self._run_gmail_assistant(
                query=gmail_query,
                max_emails=max_emails,
                format_type=gmail_format,
                organize=gmail_organize
            )

            if not gmail_result['success']:
                return {
                    'success': False,
                    'error': f"Gmail fetch failed: {gmail_result['error']}",
                    'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                }

            # Step 2: Locate and validate output data
            self.logger.info("Step 2: Locating Gmail fetcher output...")
            data_file = self._find_latest_gmail_output()

            if not data_file:
                return {
                    'success': False,
                    'error': "Could not find Gmail fetcher output file",
                    'gmail_result': gmail_result,
                    'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                }

            # Step 3: Run email analysis
            self.logger.info("Step 3: Running email analysis...")
            analysis_result = self._run_email_analysis(
                input_file=data_file,
                analysis_date=analysis_date
            )

            if not analysis_result['success']:
                return {
                    'success': False,
                    'error': f"Email analysis failed: {analysis_result['error']}",
                    'gmail_result': gmail_result,
                    'workflow_duration': (datetime.now() - workflow_start).total_seconds()
                }

            # Step 4: Generate integrated summary
            self.logger.info("Step 4: Generating integrated summary...")
            summary = self._generate_integrated_summary(gmail_result, analysis_result)

            workflow_duration = (datetime.now() - workflow_start).total_seconds()

            result = {
                'success': True,
                'workflow_duration': workflow_duration,
                'gmail_result': gmail_result,
                'analysis_result': analysis_result,
                'summary': summary,
                'data_file': str(data_file),
                'analysis_file': analysis_result.get('output_file'),
                'timestamp': datetime.now().isoformat()
            }

            self.logger.info(f"✅ Integrated workflow completed successfully in {workflow_duration:.2f} seconds")
            return result

        except Exception as e:
            self.logger.error(f"❌ Integrated workflow failed: {e!s}")
            return {
                'success': False,
                'error': str(e),
                'workflow_duration': (datetime.now() - workflow_start).total_seconds()
            }

    def _run_gmail_assistant(self,
                          query: str,
                          max_emails: int,
                          format_type: str,
                          organize: str) -> dict[str, Any]:
        """
        Run Gmail Fetcher with specified parameters
        
        Args:
            query: Gmail search query
            max_emails: Maximum emails to fetch
            format_type: Output format ('eml', 'markdown', 'both')
            organize: Organization method ('date', 'sender', 'none')
            
        Returns:
            Dict with Gmail fetcher execution results
        """
        try:
            # Construct Gmail fetcher command
            cmd = [
                sys.executable, str(self.gmail_assistant_script),
                '--query', query,
                '--max', str(max_emails),
                '--format', format_type,
                '--organize', organize
            ]

            self.logger.info(f"Running Gmail fetcher: {' '.join(cmd)}")

            # Execute Gmail fetcher
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'command': ' '.join(cmd),
                    'stdout': result.stdout,
                    'emails_fetched': self._extract_email_count(result.stdout),
                    'duration': None  # Gmail fetcher doesn't report duration
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Unknown Gmail fetcher error',
                    'command': ' '.join(cmd),
                    'returncode': result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Gmail fetcher timed out after 30 minutes'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to run Gmail fetcher: {e!s}'
            }

    def _find_latest_gmail_output(self) -> Path | None:
        """
        Find the most recent Gmail fetcher output file
        
        Returns:
            Path to the latest parquet file or None if not found
        """
        try:
            # Look for parquet files in gmail_backup directory
            parquet_files = list(self.gmail_backup_dir.rglob('*.parquet'))

            if not parquet_files:
                # Also check for alternative locations
                backup_dirs = [
                    self.base_dir / 'backup',
                    self.base_dir / 'data' / 'raw',
                    self.base_dir
                ]

                for backup_dir in backup_dirs:
                    if backup_dir.exists():
                        parquet_files.extend(backup_dir.rglob('*.parquet'))

            if not parquet_files:
                self.logger.warning("No parquet files found in any backup directory")
                return None

            # Return the most recently modified file
            latest_file = max(parquet_files, key=lambda f: f.stat().st_mtime)
            self.logger.info(f"Found latest Gmail output: {latest_file}")

            return latest_file

        except Exception as e:
            self.logger.error(f"Error finding Gmail output: {e!s}")
            return None

    def _run_email_analysis(self,
                           input_file: Path,
                           analysis_date: str | None = None) -> dict[str, Any]:
        """
        Run email analysis on the specified input file
        
        Args:
            input_file: Path to input parquet file
            analysis_date: Date filter for analysis
            
        Returns:
            Dict with analysis execution results
        """
        try:
            # Generate output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if analysis_date:
                if analysis_date == 'yesterday':
                    date_suffix = 'yesterday'
                else:
                    date_suffix = analysis_date.replace('-', '')
            else:
                date_suffix = 'all'

            output_file = self.analysis_output_dir / f'analysis_{date_suffix}_{timestamp}.json'

            # Construct analysis command
            cmd = [
                sys.executable, str(self.analysis_script),
                '--input', str(input_file),
                '--output', str(output_file),
                '--config', str(self.analysis_config)
            ]

            # Add date filter if specified
            if analysis_date:
                if analysis_date == 'yesterday':
                    cmd.extend(['--yesterday'])
                else:
                    cmd.extend(['--date', analysis_date])

            self.logger.info(f"Running email analysis: {' '.join(cmd)}")

            # Execute analysis
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 60 minute timeout
            )

            if result.returncode == 0:
                # Load and validate analysis results
                if output_file.exists():
                    with open(output_file) as f:
                        analysis_data = json.load(f)

                    return {
                        'success': True,
                        'command': ' '.join(cmd),
                        'output_file': str(output_file),
                        'analysis_data': analysis_data,
                        'emails_analyzed': analysis_data.get('metadata', {}).get('total_emails', 0),
                        'duration': analysis_data.get('metadata', {}).get('analysis_duration_seconds', 0)
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Analysis completed but output file not found'
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Unknown analysis error',
                    'command': ' '.join(cmd),
                    'returncode': result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Email analysis timed out after 60 minutes'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to run email analysis: {e!s}'
            }

    def _extract_email_count(self, gmail_output: str) -> int:
        """
        Extract number of emails fetched from Gmail fetcher output
        
        Args:
            gmail_output: Standard output from Gmail fetcher
            
        Returns:
            Number of emails fetched (0 if not found)
        """
        try:
            # Look for patterns like "Downloaded X emails" or "Fetched X emails"
            import re
            patterns = [
                r'Downloaded (\d+) emails',
                r'Fetched (\d+) emails',
                r'Processing (\d+) emails',
                r'Found (\d+) emails'
            ]

            for pattern in patterns:
                match = re.search(pattern, gmail_output, re.IGNORECASE)
                if match:
                    return int(match.group(1))

            return 0

        except Exception:
            return 0

    def _generate_integrated_summary(self,
                                   gmail_result: dict[str, Any],
                                   analysis_result: dict[str, Any]) -> dict[str, Any]:
        """
        Generate integrated summary combining Gmail fetch and analysis results
        
        Args:
            gmail_result: Gmail fetcher execution results
            analysis_result: Email analysis execution results
            
        Returns:
            Dict with integrated summary
        """
        try:
            analysis_data = analysis_result.get('analysis_data', {})

            return {
                'workflow_summary': {
                    'emails_fetched': gmail_result.get('emails_fetched', 0),
                    'emails_analyzed': analysis_result.get('emails_analyzed', 0),
                    'gmail_duration': 'Not reported',
                    'analysis_duration': f"{analysis_result.get('duration', 0):.2f} seconds"
                },
                'data_quality': {
                    'quality_passed': analysis_data.get('quality_metrics', {}).get('quality_passed', False),
                    'completeness': analysis_data.get('quality_metrics', {}).get('completeness', {}).get('overall_completeness', 0)
                },
                'top_categories': self._extract_top_categories(analysis_data),
                'automation_insights': self._extract_automation_insights(analysis_data),
                'key_recommendations': self._extract_key_recommendations(analysis_data),
                'volume_patterns': self._extract_volume_patterns(analysis_data)
            }

        except Exception as e:
            self.logger.error(f"Error generating integrated summary: {e!s}")
            return {'error': f'Failed to generate summary: {e!s}'}

    def _extract_top_categories(self, analysis_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract top email categories from analysis data"""
        try:
            classification = analysis_data.get('classification_summary', {})
            return [
                {
                    'category': category,
                    'count': stats.get('count', 0),
                    'percentage': stats.get('percentage', 0)
                }
                for category, stats in sorted(
                    classification.items(),
                    key=lambda x: x[1].get('percentage', 0),
                    reverse=True
                )[:5]
            ]
        except Exception:
            return []

    def _extract_automation_insights(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Extract automation insights from analysis data"""
        try:
            automation = analysis_data.get('sender_analysis', {}).get('automation_analysis', {})
            return {
                'automation_rate': automation.get('automation_rate', 0),
                'automated_emails': automation.get('automated_emails', 0),
                'personal_emails': automation.get('personal_emails', 0)
            }
        except Exception:
            return {}

    def _extract_key_recommendations(self, analysis_data: dict[str, Any]) -> list[str]:
        """Extract key recommendations from analysis data"""
        try:
            recommendations = analysis_data.get('insights', {}).get('recommendations', [])
            return [
                rec.get('recommendation', '')
                for rec in recommendations[:3]
                if rec.get('priority') in ['High', 'Medium']
            ]
        except Exception:
            return []

    def _extract_volume_patterns(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Extract volume pattern insights from analysis data"""
        try:
            volume_patterns = analysis_data.get('temporal_analysis', {}).get('volume_patterns', {})
            return {
                'daily_average': volume_patterns.get('daily_average', 0),
                'peak_volume': volume_patterns.get('peak_day', {}).get('volume', 0),
                'peak_date': volume_patterns.get('peak_day', {}).get('date', 'Unknown')
            }
        except Exception:
            return {}

    def run_daily_automation(self,
                           gmail_query: str = "newer_than:1d",
                           max_emails: int = 500) -> dict[str, Any]:
        """
        Run automated daily workflow optimized for cron execution
        
        Args:
            gmail_query: Gmail search query (default: last 24 hours)
            max_emails: Maximum emails to fetch
            
        Returns:
            Dict with automation results
        """
        self.logger.info("🤖 Starting daily automation workflow")

        return self.run_integrated_workflow(
            gmail_query=gmail_query,
            max_emails=max_emails,
            analysis_date='yesterday',
            gmail_format='both',
            gmail_organize='date'
        )

    def create_automation_script(self, output_path: str | None = None) -> Path:
        """
        Create automation script for cron job execution
        
        Args:
            output_path: Where to save the automation script
            
        Returns:
            Path to created automation script
        """
        if not output_path:
            output_path = self.base_dir / 'scripts' / 'daily_automation.py'

        script_content = f'''#!/usr/bin/env python3
"""
Daily Gmail Fetch + Analysis Automation
Automated script for daily email processing workflow
"""

from gmail_assistant.core.ai.analysis_integration import GmailAnalysisIntegration

def main():
    """Run daily automation workflow"""
    integration = GmailAnalysisIntegration("{self.base_dir}")
    
    # Run daily workflow
    result = integration.run_daily_automation()
    
    if result['success']:
        print("✅ Daily automation completed successfully")
        
        # Print summary
        summary = result.get('summary', {{}})
        workflow_summary = summary.get('workflow_summary', {{}})
        
        print(f"📧 Emails fetched: {{workflow_summary.get('emails_fetched', 0)}}")
        print(f"📊 Emails analyzed: {{workflow_summary.get('emails_analyzed', 0)}}")
        print(f"⏱️  Analysis time: {{workflow_summary.get('analysis_duration', 'Unknown')}}")
        
        # Print key insights
        recommendations = summary.get('key_recommendations', [])
        if recommendations:
            print("\\n🎯 Key recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {{i}}. {{rec}}")
        
        sys.exit(0)
    else:
        print(f"❌ Daily automation failed: {{result.get('error', 'Unknown error')}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(script_content)

        output_file.chmod(0o755)  # Make executable

        self.logger.info(f"Created automation script: {output_file}")
        return output_file

    def generate_cron_template(self) -> str:
        """
        Generate cron job template for daily automation
        
        Returns:
            Cron job configuration string
        """
        automation_script = self.base_dir / 'scripts' / 'daily_automation.py'
        log_file = self.base_dir / 'logs' / 'daily_automation.log'

        cron_template = f"""# Gmail Fetcher + Analysis Daily Automation
# Add this line to your crontab (crontab -e)

# Daily automation at 6:00 AM
0 6 * * * cd {self.base_dir} && python {automation_script} >> {log_file} 2>&1

# Alternative: Daily automation at 8:00 PM  
# 0 20 * * * cd {self.base_dir} && python {automation_script} >> {log_file} 2>&1

# Weekly summary report on Sundays at 9:00 AM
# 0 9 * * 0 cd {self.base_dir} && python scripts/analysis/weekly_summary.py >> {log_file} 2>&1
"""

        return cron_template


# Convenience functions for easy integration
def run_daily_workflow(gmail_query: str = "newer_than:1d",
                      max_emails: int = 500,
                      base_dir: str | None = None) -> dict[str, Any]:
    """
    Convenience function to run daily Gmail + analysis workflow
    
    Args:
        gmail_query: Gmail search query
        max_emails: Maximum emails to fetch
        base_dir: Base directory (uses current directory if None)
        
    Returns:
        Dict with workflow results
    """
    integration = GmailAnalysisIntegration(base_dir)
    return integration.run_daily_automation(gmail_query, max_emails)


def setup_daily_automation(base_dir: str | None = None) -> tuple[Path, str]:
    """
    Setup daily automation for Gmail + analysis workflow
    
    Args:
        base_dir: Base directory (uses current directory if None)
        
    Returns:
        Tuple of (automation_script_path, cron_template)
    """
    integration = GmailAnalysisIntegration(base_dir)

    # Create automation script
    script_path = integration.create_automation_script()

    # Generate cron template
    cron_template = integration.generate_cron_template()

    return script_path, cron_template


if __name__ == "__main__":
    # Example usage
    print("Gmail Fetcher + Analysis Integration")
    print("=" * 40)

    # Test integration
    integration = GmailAnalysisIntegration()

    print("Setting up daily automation...")
    script_path, cron_template = setup_daily_automation()

    print(f"✅ Automation script created: {script_path}")
    print("\n📅 Cron template:")
    print(cron_template)

    print("\n🚀 To test the integration, run:")
    print(f"python {script_path}")
