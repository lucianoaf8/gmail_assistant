#!/usr/bin/env python3
"""
Simple system test for email analysis
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from analysis.daily_email_analyzer import DailyEmailAnalyzer

def create_test_data():
    """Create test data for validation"""
    return pd.DataFrame({
        'gmail_id': ['id_001', 'id_002', 'id_003', 'id_004', 'id_005'],
        'date_received': [
            datetime.now() - timedelta(days=1),
            datetime.now() - timedelta(days=1), 
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1)
        ],
        'subject': [
            'Payment Receipt - Your order',
            'Newsletter Update',
            'Backup completed successfully', 
            'Meeting Reminder',
            'Bird ride receipt'
        ],
        'sender': [
            'billing@company.com',
            'newsletter@ai.com',
            'noreply@backup.com',
            'calendar@work.com',
            'noreply@bird.co'
        ],
        'plain_text_content': [
            'Your payment of $25.50 has been processed successfully.',
            'Here are the latest AI updates and news.',
            'Your backup completed successfully. All files backed up.',
            'Reminder: Meeting at 2 PM tomorrow.',
            'Thanks for riding with Bird! Trip cost $3.50.'
        ]
    })

def main():
    """Run simple system test"""
    print("Email Analysis System Test")
    print("=" * 40)
    
    try:
        # Create test data
        print("Creating test data...")
        df = create_test_data()
        print(f"+ Created {len(df)} test emails")
        
        # Initialize analyzer
        print("Initializing analyzer...")
        config_path = Path(__file__).parent.parent.parent / 'config' / 'analysis' / '0922-1430_daily_analysis_config.json'
        analyzer = DailyEmailAnalyzer(str(config_path))
        print("+ Analyzer initialized")
        
        # Run analysis
        print("Running analysis...")
        results = analyzer.analyze_emails(df)
        
        if 'error' in results:
            print(f"- Analysis failed: {results['error']}")
            return False
        
        print("+ Analysis completed successfully")
        
        # Generate summary
        print("\nGenerating summary...")
        summary = analyzer.generate_summary_report(results)
        print(summary)
        
        # Validate key components
        print("\nValidating results...")
        
        required_sections = [
            'metadata', 'quality_metrics', 'classification_summary',
            'temporal_analysis', 'sender_analysis', 'content_analysis', 'insights'
        ]
        
        for section in required_sections:
            if section in results:
                print(f"+ {section}")
            else:
                print(f"- Missing: {section}")
                return False
        
        # Check classifications
        categories = results.get('classification_summary', {})
        print(f"\nCategories found: {list(categories.keys())}")
        
        # Check insights
        recommendations = results.get('insights', {}).get('recommendations', [])
        print(f"Recommendations generated: {len(recommendations)}")
        
        print("\n+ System test passed!")
        return True
        
    except Exception as e:
        print(f"\n- System test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)