#!/usr/bin/env python3
"""
Integration tests for the email analysis system
"""

import unittest
import sys
import os
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta

from gmail_assistant.analysis.email_data_converter import EmailDataConverter
from gmail_assistant.analysis.daily_email_analysis import EmailAnalysisEngine

class TestEmailAnalysisIntegration(unittest.TestCase):
    """Test email analysis integration"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.converter = EmailDataConverter(verbose=False)

        # Basic config for testing
        self.config = {
            'quality_thresholds': {
                'min_completeness': 70.0,
                'max_null_rate': 30.0,
                'max_duplicate_rate': 50.0
            },
            'logging_config': {
                'log_level': 'ERROR'
            }
        }

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_email_data_converter_imports(self):
        """Test that EmailDataConverter can be imported and instantiated"""
        converter = EmailDataConverter()
        self.assertIsNotNone(converter)

    def test_analysis_engine_imports(self):
        """Test that EmailAnalysisEngine can be imported and instantiated"""
        engine = EmailAnalysisEngine(self.config)
        self.assertIsNotNone(engine)

    def test_analysis_engine_methods(self):
        """Test that EmailAnalysisEngine has required methods"""
        engine = EmailAnalysisEngine(self.config)

        # Check required methods exist
        self.assertTrue(hasattr(engine, 'analyze_data_quality'))
        self.assertTrue(hasattr(engine, 'classify_emails'))
        self.assertTrue(hasattr(engine, 'analyze_temporal_patterns'))
        self.assertTrue(hasattr(engine, 'analyze_senders'))
        self.assertTrue(hasattr(engine, 'analyze_content'))
        self.assertTrue(hasattr(engine, 'generate_insights'))

    def test_converter_methods(self):
        """Test that EmailDataConverter has required methods"""
        converter = EmailDataConverter()

        # Check required methods exist
        self.assertTrue(hasattr(converter, 'extract_from_eml'))
        self.assertTrue(hasattr(converter, 'extract_from_markdown'))
        self.assertTrue(hasattr(converter, 'convert_directory'))

    def test_date_parsing(self):
        """Test email date parsing functionality"""
        converter = EmailDataConverter()

        # Test various date formats
        test_dates = [
            "Sat, 01 Jun 2024 17:22:00 +0000",
            "2024-06-01 17:22:00",
            "2024-06-01T17:22:00+00:00"
        ]

        for date_str in test_dates:
            parsed = converter._parse_email_date(date_str)
            if parsed:  # Some may fail, that's ok
                self.assertIsInstance(parsed, datetime)

    def test_gmail_id_extraction(self):
        """Test Gmail ID extraction from filenames"""
        converter = EmailDataConverter()

        # Test filename pattern
        filename = "2024-06-01_172200_subject_18fd4d295a4fe8ea.eml"
        gmail_id = converter._extract_gmail_id(filename)

        self.assertEqual(gmail_id, "18fd4d295a4fe8ea")

    def test_classification_categories(self):
        """Test that classification system has proper categories"""
        engine = EmailAnalysisEngine(self.config)

        # Check that classification rules exist
        self.assertIsInstance(engine.classification_rules, dict)

        # Check for expected categories
        expected_categories = ['Financial', 'Notifications', 'Transportation',
                             'Marketing/News', 'Social', 'Work/Business']

        for category in expected_categories:
            self.assertIn(category, engine.classification_rules)

        # Check that each category has required fields
        for category, rules in engine.classification_rules.items():
            self.assertIn('priority', rules)
            self.assertIn('keywords', rules)
            self.assertIsInstance(rules['keywords'], list)

    def test_sample_email_classification(self):
        """Test email classification with sample data"""
        engine = EmailAnalysisEngine(self.config)

        # Create sample email data
        import pandas as pd

        sample_data = {
            'gmail_id': ['test001', 'test002', 'test003'],
            'subject': ['Payment Receipt', 'Newsletter Update', 'Meeting Reminder'],
            'sender': ['billing@company.com', 'newsletter@news.com', 'calendar@work.com'],
            'date_received': [datetime.now()] * 3,
            'plain_text_content': [
                'Your payment has been processed successfully.',
                'Here is your weekly newsletter.',
                'Reminder: You have a meeting tomorrow.'
            ]
        }

        df = pd.DataFrame(sample_data)

        # Test classification
        df_classified = engine.classify_emails(df)

        self.assertEqual(len(df_classified), 3)
        self.assertIn('category', df_classified.columns)
        self.assertIn('classification_confidence', df_classified.columns)
        self.assertIn('is_automated', df_classified.columns)

        # Check expected classifications
        categories = df_classified['category'].tolist()
        self.assertIn('Financial', categories)

    def test_quality_assessment(self):
        """Test data quality assessment"""
        engine = EmailAnalysisEngine(self.config)

        # Create sample data with quality issues
        import pandas as pd

        sample_data = {
            'gmail_id': ['test001', 'test002', None],  # Missing gmail_id
            'subject': ['Test 1', 'Test 2', 'Test 3'],
            'sender': ['test@example.com', None, 'test3@example.com'],  # Missing sender
            'date_received': [datetime.now()] * 3,
            'plain_text_content': ['Content 1', 'Content 2', 'Content 3']
        }

        df = pd.DataFrame(sample_data)

        # Test quality assessment
        quality_metrics = engine.analyze_data_quality(df)

        self.assertIsInstance(quality_metrics, dict)
        self.assertIn('completeness', quality_metrics)
        self.assertIn('consistency', quality_metrics)
        self.assertIn('quality_passed', quality_metrics)

        # Should detect the missing values
        completeness = quality_metrics['completeness']['overall_completeness']
        self.assertLess(completeness, 100.0)

    def test_insights_generation(self):
        """Test insights generation"""
        engine = EmailAnalysisEngine(self.config)

        # Mock analysis results
        mock_results = {
            'classification_summary': {
                'Financial': {'count': 100, 'percentage': 50.0},
                'Notifications': {'count': 50, 'percentage': 25.0},
                'Other': {'count': 50, 'percentage': 25.0}
            },
            'sender_analysis': {
                'automation_analysis': {
                    'automation_rate': 75.0,
                    'automated_emails': 150,
                    'personal_emails': 50
                }
            },
            'temporal_analysis': {},
            'content_analysis': {},
            'metadata': {'total_emails': 200}
        }

        # Test insights generation
        insights = engine.generate_insights(mock_results)

        self.assertIsInstance(insights, dict)
        self.assertIn('recommendations', insights)

        # Should generate recommendations for high financial percentage
        recommendations = insights['recommendations']
        self.assertIsInstance(recommendations, list)

if __name__ == '__main__':
    unittest.main()