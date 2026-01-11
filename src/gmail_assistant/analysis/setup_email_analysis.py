#!/usr/bin/env python3
"""
Email Analysis System Setup
Sets up the daily email analysis environment and validates the system.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


class EmailAnalysisSetup:
    """Setup and validation for email analysis system"""

    def __init__(self):
        self.base_dir = Path.cwd()
        self.required_dirs = [
            'logs', 'output', 'data', 'config', 'scripts'
        ]
        self.required_files = [
            'daily_email_analysis.py',
            'config.json',
            'requirements.txt'
        ]

    def create_directory_structure(self):
        """Create required directory structure"""
        print("📁 Creating directory structure...")

        for dir_name in self.required_dirs:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"   ✓ {dir_name}/")

        # Create subdirectories
        (self.base_dir / 'output' / 'daily').mkdir(exist_ok=True)
        (self.base_dir / 'output' / 'reports').mkdir(exist_ok=True)
        (self.base_dir / 'data' / 'raw').mkdir(exist_ok=True)
        (self.base_dir / 'data' / 'processed').mkdir(exist_ok=True)

        print("✅ Directory structure created")

    def check_dependencies(self):
        """Check if required Python packages are installed"""
        print("\n🔍 Checking dependencies...")

        required_packages = [
            'pandas', 'numpy', 'pyarrow', 'json', 'argparse',
            'logging', 'datetime', 'pathlib', 're', 'collections'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                if package in ['json', 'argparse', 'logging', 'datetime', 'pathlib', 're', 'collections']:
                    # These are built-in modules
                    continue
                __import__(package)
                print(f"   ✓ {package}")
            except ImportError:
                print(f"   ❌ {package} - MISSING")
                missing_packages.append(package)

        if missing_packages:
            print("\n📦 Install missing packages:")
            print(f"pip install {' '.join(missing_packages)}")
            return False

        print("✅ All dependencies satisfied")
        return True

    def create_requirements_file(self):
        """Create requirements.txt file"""
        requirements = [
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "pyarrow>=13.0.0",
            "tqdm>=4.65.0"
        ]

        req_file = self.base_dir / 'requirements.txt'
        with open(req_file, 'w') as f:
            f.write('\n'.join(requirements))

        print(f"📄 Created {req_file}")

    def validate_config(self):
        """Validate configuration file"""
        print("\n⚙️  Validating configuration...")

        config_file = self.base_dir / 'config.json'
        if not config_file.exists():
            print("   ❌ config.json not found")
            return False

        try:
            with open(config_file) as f:
                config = json.load(f)

            # Validate required sections
            required_sections = [
                'quality_thresholds', 'classification_config',
                'temporal_analysis', 'sender_analysis', 'content_analysis'
            ]

            for section in required_sections:
                if section in config:
                    print(f"   ✓ {section}")
                else:
                    print(f"   ❌ {section} - MISSING")
                    return False

            print("✅ Configuration valid")
            return True

        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON in config.json: {e}")
            return False

    def create_sample_data(self):
        """Create sample data for testing"""
        print("\n📊 Creating sample test data...")

        import pandas as pd

        # Create sample email data
        sample_data = {
            'gmail_id': [f'id_{i:04d}' for i in range(100)],
            'date_received': [
                datetime.now() - timedelta(days=i//10, hours=i%24)
                for i in range(100)
            ],
            'subject': [
                'Payment Receipt', 'Newsletter Update', 'Meeting Reminder',
                'Bill Statement', 'Social Notification', 'Work Assignment'
            ] * 17 + ['Test Email', 'Sample Subject'],
            'sender': [
                'billing@company.com', 'newsletter@news.com', 'calendar@work.com',
                'statements@bank.com', 'notifications@social.com', 'team@workplace.com'
            ] * 17 + ['test@example.com', 'sample@test.com'],
            'plain_text_content': [
                'Your payment has been processed successfully.',
                'Here is your weekly newsletter with the latest updates.',
                'Reminder: You have a meeting scheduled for tomorrow.',
                'Your monthly statement is now available.',
                'You have new notifications on your social account.',
                'New assignment has been added to your project.'
            ] * 17 + ['Test content here.', 'Sample email content.']
        }

        df = pd.DataFrame(sample_data)
        sample_file = self.base_dir / 'data' / 'sample_emails.parquet'
        df.to_parquet(sample_file, index=False)

        print(f"   ✓ Created sample data: {sample_file}")
        print(f"   📧 Sample contains {len(df)} emails")

        return sample_file

    def test_analysis_pipeline(self, sample_file):
        """Test the analysis pipeline with sample data"""
        print("\n🧪 Testing analysis pipeline...")

        try:
            # Import and test the analysis engine
            from gmail_assistant.analysis.daily_email_analysis import EmailAnalysisEngine

            # Load config
            with open(self.base_dir / 'config.json') as f:
                config = json.load(f)

            # Initialize engine
            engine = EmailAnalysisEngine(config)

            # Load sample data
            import pandas as pd
            df = pd.read_parquet(sample_file)

            # Test each component
            print("   🔍 Testing data quality assessment...")
            quality_metrics = engine.analyze_data_quality(df)
            assert quality_metrics['quality_passed'], "Quality assessment failed"

            print("   🏷️  Testing email classification...")
            df_classified = engine.classify_emails(df)
            assert 'category' in df_classified.columns, "Classification failed"

            print("   📅 Testing temporal analysis...")
            temporal_analysis = engine.analyze_temporal_patterns(df_classified)
            assert 'volume_patterns' in temporal_analysis, "Temporal analysis failed"

            print("   👤 Testing sender analysis...")
            sender_analysis = engine.analyze_senders(df_classified)
            assert 'sender_metrics' in sender_analysis, "Sender analysis failed"

            print("   📝 Testing content analysis...")
            content_analysis = engine.analyze_content(df_classified)
            assert 'length_statistics' in content_analysis, "Content analysis failed"

            print("   💡 Testing insights generation...")
            insights = engine.generate_insights({
                'classification_summary': df_classified['category'].value_counts().to_dict(),
                'temporal_analysis': temporal_analysis,
                'sender_analysis': sender_analysis,
                'content_analysis': content_analysis,
                'metadata': {'total_emails': len(df_classified)}
            })
            assert 'recommendations' in insights, "Insights generation failed"

            print("✅ Analysis pipeline test passed")
            return True

        except Exception as e:
            print(f"   ❌ Pipeline test failed: {e}")
            return False

    def create_execution_scripts(self):
        """Create convenient execution scripts"""
        print("\n📜 Creating execution scripts...")

        # Daily analysis script
        daily_script = self.base_dir / 'scripts' / 'run_daily_analysis.py'
        daily_script_content = '''#!/usr/bin/env python3
"""
Convenience script for running daily email analysis
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def main():
    """Run daily analysis with standard parameters"""

    base_dir = Path(__file__).parent.parent

    # Default parameters
    config_file = base_dir / 'config.json'
    analysis_script = base_dir / 'daily_email_analysis.py'

    # Get input file from command line or use default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = base_dir / 'data' / 'raw' / 'latest_emails.parquet'

    # Output file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = base_dir / 'output' / 'daily' / f'analysis_{timestamp}.json'

    # Run analysis
    cmd = [
        sys.executable, str(analysis_script),
        '--config', str(config_file),
        '--input', str(input_file),
        '--output', str(output_file),
        '--yesterday'
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Daily analysis completed successfully")
        print(f"Results saved to: {output_file}")
    else:
        print("❌ Analysis failed:")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

        daily_script.parent.mkdir(exist_ok=True)
        with open(daily_script, 'w') as f:
            f.write(daily_script_content)
        daily_script.chmod(0o755)

        # Batch analysis script
        batch_script = self.base_dir / 'scripts' / 'run_batch_analysis.py'
        batch_script_content = '''#!/usr/bin/env python3
"""
Batch analysis script for processing multiple days
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def main():
    """Run batch analysis for date range"""

    if len(sys.argv) < 3:
        print("Usage: python run_batch_analysis.py <input_file> <days_back>")
        sys.exit(1)

    input_file = sys.argv[1]
    days_back = int(sys.argv[2])

    base_dir = Path(__file__).parent.parent
    config_file = base_dir / 'config.json'
    analysis_script = base_dir / 'daily_email_analysis.py'

    print(f"Running batch analysis for last {days_back} days...")

    for i in range(days_back):
        date = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')
        output_file = base_dir / 'output' / 'daily' / f'analysis_{date}.json'

        cmd = [
            sys.executable, str(analysis_script),
            '--config', str(config_file),
            '--input', str(input_file),
            '--output', str(output_file),
            '--date', date
        ]

        print(f"Processing {date}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"   ✅ {date} completed")
        else:
            print(f"   ❌ {date} failed: {result.stderr}")

if __name__ == "__main__":
    main()
'''

        with open(batch_script, 'w') as f:
            f.write(batch_script_content)
        batch_script.chmod(0o755)

        print(f"   ✓ {daily_script}")
        print(f"   ✓ {batch_script}")

    def create_cron_template(self):
        """Create cron job template"""
        print("\n⏰ Creating cron job template...")

        cron_template = self.base_dir / 'scripts' / 'cron_template.txt'
        cron_content = f"""# Email Analysis Cron Jobs
# Add these lines to your crontab (crontab -e)

# Daily analysis at 6:00 AM
0 6 * * * cd {self.base_dir} && python scripts/run_daily_analysis.py >> logs/cron.log 2>&1

# Weekly cleanup at 2:00 AM Sunday
0 2 * * 0 cd {self.base_dir} && python scripts/cleanup_old_files.py >> logs/cleanup.log 2>&1

# Monthly summary report at 9:00 AM on the 1st
0 9 1 * * cd {self.base_dir} && python scripts/monthly_report.py >> logs/reports.log 2>&1
"""

        with open(cron_template, 'w') as f:
            f.write(cron_content)

        print(f"   ✓ {cron_template}")
        print("   📝 Edit and add to crontab for automated execution")

    def generate_usage_guide(self):
        """Generate comprehensive usage guide"""
        print("\n📚 Creating usage guide...")

        guide_file = self.base_dir / 'USAGE_GUIDE.md'
        guide_content = """# Email Analysis System - Usage Guide

## Quick Start

### 1. Daily Analysis (Most Common)
```bash
# Analyze yesterday's emails
python daily_email_analysis.py --input data/emails.parquet --yesterday

# Analyze specific date
python daily_email_analysis.py --input data/emails.parquet --date 2025-09-18

# Use convenience script
python scripts/run_daily_analysis.py data/emails.parquet
```

### 2. Configuration
Edit `config.json` to customize:
- Quality thresholds
- Classification rules
- Custom categories
- Output formats
- Alert settings

### 3. Output Interpretation
Results are saved as JSON with these sections:
- **metadata**: Analysis info and timing
- **quality_metrics**: Data quality assessment
- **classification_summary**: Category distribution
- **temporal_analysis**: Time patterns and trends
- **sender_analysis**: Sender patterns and automation
- **content_analysis**: Content length and patterns
- **insights**: Actionable recommendations

## Advanced Usage

### Batch Processing
```bash
# Analyze last 7 days
python scripts/run_batch_analysis.py data/emails.parquet 7
```

### Custom Configuration
```bash
# Use custom config
python daily_email_analysis.py --config my_config.json --input data.parquet
```

### Automated Execution
```bash
# Set up cron job (see scripts/cron_template.txt)
crontab -e
# Add: 0 6 * * * cd /path/to/analysis && python scripts/run_daily_analysis.py
```

## Troubleshooting

### Common Issues
1. **Missing dependencies**: Run `pip install -r requirements.txt`
2. **Data quality failures**: Check input data completeness
3. **Memory issues**: Process smaller batches or increase memory limits
4. **Classification errors**: Review and update classification rules

### Log Files
- `logs/email_analysis.log`: Main analysis logs
- `logs/cron.log`: Automated execution logs
- `logs/cleanup.log`: Data cleanup logs

## Customization

### Adding New Categories
Edit `config.json` under `custom_categories`:
```json
"My_Category": {
  "priority": 9,
  "keywords": ["keyword1", "keyword2"],
  "sender_patterns": ["@domain.com", "specific@"]
}
```

### Modifying Thresholds
Adjust quality and alert thresholds in `config.json`:
```json
"quality_thresholds": {
  "min_completeness": 95.0,
  "max_null_rate": 5.0
}
```

## Output Examples

### Classification Summary
```json
"classification_summary": {
  "Financial": {"count": 450, "percentage": 32.5},
  "Notifications": {"count": 280, "percentage": 20.2},
  "Marketing/News": {"count": 310, "percentage": 22.4}
}
```

### Key Insights
```json
"insights": {
  "recommendations": [
    {
      "priority": "High",
      "category": "Financial Processing",
      "recommendation": "Set up dedicated financial email processing",
      "impact": "High automation potential"
    }
  ]
}
```

For detailed methodology, see `EMAIL_ANALYSIS_METHODOLOGY.md`
"""

        with open(guide_file, 'w') as f:
            f.write(guide_content)

        print(f"   ✓ {guide_file}")

    def run_setup(self):
        """Run complete setup process"""
        print("🚀 Email Analysis System Setup")
        print("=" * 50)

        success = True

        # Create directory structure
        self.create_directory_structure()

        # Check dependencies
        if not self.check_dependencies():
            success = False

        # Create requirements file
        self.create_requirements_file()

        # Validate configuration
        if not self.validate_config():
            success = False

        # Create sample data and test
        if success:
            sample_file = self.create_sample_data()
            if not self.test_analysis_pipeline(sample_file):
                success = False

        # Create execution scripts
        self.create_execution_scripts()

        # Create cron template
        self.create_cron_template()

        # Generate usage guide
        self.generate_usage_guide()

        # Final status
        print("\n" + "=" * 50)
        if success:
            print("✅ Setup completed successfully!")
            print("\n🎯 Next Steps:")
            print("1. Install missing dependencies if any")
            print("2. Place your email data in data/raw/")
            print("3. Run: python scripts/run_daily_analysis.py your_data.parquet")
            print("4. Set up cron job for automation (see scripts/cron_template.txt)")
            print("5. Review USAGE_GUIDE.md for detailed instructions")
        else:
            print("❌ Setup completed with issues")
            print("Please resolve the issues above before proceeding")

        return success

def main():
    """Main setup function"""
    setup = EmailAnalysisSetup()
    setup.run_setup()

if __name__ == "__main__":
    main()
