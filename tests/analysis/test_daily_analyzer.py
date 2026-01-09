#!/usr/bin/env python3
"""
Test Suite for Daily Email Analysis System
Comprehensive tests for all analysis components with sample data validation.
"""

import unittest
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from analysis.daily_email_analyzer import (
    DailyEmailAnalyzer,
    DataQualityAssessment,
    HierarchicalClassifier,
    TemporalAnalyzer,
    SenderAnalyzer,
    ContentAnalyzer,
    InsightsGenerator
)


class TestDataQualityAssessment(unittest.TestCase):
    """Test cases for data quality assessment"""
    
    def setUp(self):
        self.quality_thresholds = {
            'min_completeness': 95.0,
            'max_null_rate': 5.0
        }
        self.assessor = DataQualityAssessment(self.quality_thresholds)
        
    def test_complete_data_quality(self):
        """Test quality assessment with complete data"""
        df = pd.DataFrame({
            'gmail_id': ['id_001', 'id_002', 'id_003'],
            'date_received': [datetime.now(), datetime.now(), datetime.now()],
            'subject': ['Test 1', 'Test 2', 'Test 3'],
            'sender': ['test1@example.com', 'test2@example.com', 'test3@example.com'],
            'plain_text_content': ['Content 1', 'Content 2', 'Content 3']
        })
        
        quality_metrics = self.assessor.assess_quality(df)
        
        self.assertTrue(quality_metrics['quality_passed'])
        self.assertEqual(quality_metrics['completeness']['overall_completeness'], 100.0)
        self.assertEqual(quality_metrics['consistency']['duplicate_gmail_ids'], 0)
        
    def test_incomplete_data_quality(self):
        """Test quality assessment with missing data"""
        df = pd.DataFrame({
            'gmail_id': ['id_001', 'id_002', None],
            'date_received': [datetime.now(), None, datetime.now()],
            'subject': ['Test 1', 'Test 2', 'Test 3'],
            'sender': [None, 'test2@example.com', 'test3@example.com'],
            'plain_text_content': ['Content 1', 'Content 2', None]
        })
        
        quality_metrics = self.assessor.assess_quality(df)
        
        self.assertFalse(quality_metrics['quality_passed'])
        self.assertLess(quality_metrics['completeness']['overall_completeness'], 95.0)
        self.assertGreater(len(quality_metrics['quality_issues']), 0)
        
    def test_duplicate_detection(self):
        """Test duplicate gmail_id detection"""
        df = pd.DataFrame({
            'gmail_id': ['id_001', 'id_002', 'id_001'],  # Duplicate
            'date_received': [datetime.now(), datetime.now(), datetime.now()],
            'subject': ['Test 1', 'Test 2', 'Test 3'],
            'sender': ['test1@example.com', 'test2@example.com', 'test3@example.com'],
            'plain_text_content': ['Content 1', 'Content 2', 'Content 3']
        })
        
        quality_metrics = self.assessor.assess_quality(df)
        
        self.assertFalse(quality_metrics['quality_passed'])
        self.assertEqual(quality_metrics['consistency']['duplicate_gmail_ids'], 1)


class TestHierarchicalClassifier(unittest.TestCase):
    """Test cases for email classification"""
    
    def setUp(self):
        self.classification_rules = {
            'Financial': {
                'priority': 1,
                'keywords': ['payment', 'invoice', 'bill', 'receipt'],
                'sender_patterns': ['billing@', 'finance@']
            },
            'Notifications': {
                'priority': 2,
                'keywords': ['notification', 'alert', 'backup'],
                'sender_patterns': ['noreply@', 'no-reply@']
            }
        }
        self.classifier = HierarchicalClassifier(self.classification_rules)
        
    def test_financial_classification(self):
        """Test financial email classification"""
        df = pd.DataFrame({
            'gmail_id': ['id_001'],
            'subject': ['Payment Receipt'],
            'sender': ['billing@company.com'],
            'plain_text_content': ['Your payment of $100 has been processed']
        })
        
        df_classified = self.classifier.classify_emails(df)
        
        self.assertEqual(df_classified.iloc[0]['category'], 'Financial')
        self.assertGreater(df_classified.iloc[0]['classification_confidence'], 0.7)
        
    def test_notification_classification(self):
        """Test notification email classification"""
        df = pd.DataFrame({
            'gmail_id': ['id_002'],
            'subject': ['Backup Completed'],
            'sender': ['noreply@backup.com'],
            'plain_text_content': ['Your backup has completed successfully']
        })
        
        df_classified = self.classifier.classify_emails(df)
        
        self.assertEqual(df_classified.iloc[0]['category'], 'Notifications')
        
    def test_automation_detection(self):
        """Test automation detection"""
        df = pd.DataFrame({
            'gmail_id': ['id_003', 'id_004'],
            'subject': ['Backup Alert', 'Personal Message'],
            'sender': ['noreply@service.com', 'friend@personal.com'],
            'plain_text_content': ['Automated backup alert', 'Hey, how are you?']
        })
        
        df_classified = self.classifier.classify_emails(df)
        
        self.assertTrue(df_classified.iloc[0]['is_automated'])
        self.assertFalse(df_classified.iloc[1]['is_automated'])
        
    def test_custom_categories(self):
        """Test adding custom categories"""
        custom_categories = {
            'AI_Newsletters': {
                'priority': 2,
                'keywords': ['AI', 'artificial intelligence'],
                'sender_patterns': ['@ai.com']
            }
        }
        
        self.classifier.add_custom_categories(custom_categories)
        
        df = pd.DataFrame({
            'gmail_id': ['id_005'],
            'subject': ['AI Newsletter'],
            'sender': ['newsletter@ai.com'],
            'plain_text_content': ['Latest AI developments']
        })
        
        df_classified = self.classifier.classify_emails(df)
        
        self.assertEqual(df_classified.iloc[0]['category'], 'AI_Newsletters')


class TestTemporalAnalyzer(unittest.TestCase):
    """Test cases for temporal analysis"""
    
    def setUp(self):
        self.config = {
            'peak_detection_threshold': 2.0,
            'rolling_window_days': 7
        }
        self.analyzer = TemporalAnalyzer(self.config)
        
    def test_volume_patterns(self):
        """Test volume pattern analysis"""
        # Create data with varying volumes
        dates = [datetime.now() - timedelta(days=i) for i in range(10)]
        volumes = [5, 10, 15, 8, 12, 20, 6, 9, 11, 7]  # Spike on day 5
        
        data = []
        for date, volume in zip(dates, volumes):
            for i in range(volume):
                data.append({
                    'gmail_id': f'id_{len(data):03d}',
                    'date_received': date + timedelta(hours=i),
                    'subject': f'Email {i}',
                    'sender': f'sender{i}@example.com',
                    'plain_text_content': f'Content {i}',
                    'category': 'Other'
                })
        
        df = pd.DataFrame(data)
        
        temporal_analysis = self.analyzer.analyze_temporal_patterns(df)
        
        self.assertIn('volume_patterns', temporal_analysis)
        self.assertIn('peak_analysis', temporal_analysis)
        self.assertGreater(temporal_analysis['volume_patterns']['daily_average'], 0)
        
    def test_peak_detection(self):
        """Test peak detection algorithm"""
        # Create daily volume series with clear peak
        daily_volume = pd.Series([5, 6, 4, 5, 20, 6, 5, 4, 6, 5])  # Peak at index 4
        daily_volume.index = pd.date_range('2025-01-01', periods=len(daily_volume))
        
        peaks = self.analyzer._detect_peaks(daily_volume)
        
        self.assertGreater(peaks['peaks_detected'], 0)
        
    def test_hourly_distribution(self):
        """Test hourly distribution analysis"""
        # Create emails at different hours
        df = pd.DataFrame({
            'gmail_id': [f'id_{i:03d}' for i in range(24)],
            'date_received': [datetime.now().replace(hour=h) for h in range(24)],
            'subject': ['Test'] * 24,
            'sender': ['test@example.com'] * 24,
            'plain_text_content': ['Content'] * 24,
            'category': ['Other'] * 24
        })
        
        temporal_analysis = self.analyzer.analyze_temporal_patterns(df)
        
        hourly_dist = temporal_analysis['time_distribution']['hourly_distribution']
        self.assertEqual(len(hourly_dist), 24)
        self.assertEqual(sum(hourly_dist.values()), 24)


class TestSenderAnalyzer(unittest.TestCase):
    """Test cases for sender analysis"""
    
    def setUp(self):
        self.config = {
            'top_senders_count': 10
        }
        self.analyzer = SenderAnalyzer(self.config)
        
    def test_sender_metrics(self):
        """Test basic sender metrics calculation"""
        df = pd.DataFrame({
            'gmail_id': ['id_001', 'id_002', 'id_003'],
            'sender': ['sender1@example.com', 'sender2@example.com', 'sender1@example.com'],
            'date_received': [datetime.now()] * 3,
            'is_automated': [True, False, True]
        })
        
        sender_analysis = self.analyzer.analyze_senders(df)
        
        self.assertEqual(sender_analysis['sender_metrics']['total_unique_senders'], 2)
        self.assertEqual(sender_analysis['sender_metrics']['total_emails'], 3)
        
    def test_automation_analysis(self):
        """Test automation pattern analysis"""
        df = pd.DataFrame({
            'gmail_id': ['id_001', 'id_002', 'id_003', 'id_004'],
            'sender': ['auto@example.com', 'human@example.com', 'auto@example.com', 'human@example.com'],
            'is_automated': [True, False, True, False]
        })
        
        sender_analysis = self.analyzer.analyze_senders(df)
        automation = sender_analysis['automation_analysis']
        
        self.assertEqual(automation['automation_rate'], 50.0)
        self.assertEqual(automation['automated_emails'], 2)
        self.assertEqual(automation['personal_emails'], 2)
        
    def test_domain_analysis(self):
        """Test domain classification"""
        df = pd.DataFrame({
            'gmail_id': ['id_001', 'id_002', 'id_003'],
            'sender': ['user@gmail.com', 'noreply@service.com', 'admin@company.com']
        })
        
        sender_analysis = self.analyzer.analyze_senders(df)
        domain_analysis = sender_analysis['domain_analysis']
        
        self.assertEqual(domain_analysis['total_unique_domains'], 3)
        self.assertIn('gmail.com', domain_analysis['top_domains'])


class TestContentAnalyzer(unittest.TestCase):
    """Test cases for content analysis"""
    
    def setUp(self):
        self.config = {
            'length_buckets': [0, 500, 2000, 5000, 10000, 20000],
            'bucket_labels': ['Very Short', 'Short', 'Medium', 'Long', 'Very Long', 'Extremely Long']
        }
        self.analyzer = ContentAnalyzer(self.config)
        
    def test_content_length_analysis(self):
        """Test content length statistics"""
        df = pd.DataFrame({
            'content_length': [100, 1000, 3000, 8000, 15000],
            'plain_text_content': ['Short'] * 5,
            'subject': ['Test'] * 5
        })
        
        content_analysis = self.analyzer.analyze_content(df)
        length_stats = content_analysis['length_statistics']
        
        self.assertIn('basic_stats', length_stats)
        self.assertIn('length_distribution', length_stats)
        self.assertEqual(length_stats['basic_stats']['min'], 100)
        self.assertEqual(length_stats['basic_stats']['max'], 15000)
        
    def test_url_analysis(self):
        """Test URL pattern detection"""
        df = pd.DataFrame({
            'plain_text_content': [
                'Check out https://example.com for more info',
                'Visit http://test.org and https://another.com',
                'No URLs in this email'
            ],
            'subject': ['Test'] * 3,
            'word_count': [10, 15, 5]
        })
        
        content_analysis = self.analyzer.analyze_content(df)
        url_analysis = content_analysis['content_patterns']['url_analysis']
        
        self.assertEqual(url_analysis['emails_with_urls'], 2)
        self.assertGreater(url_analysis['average_urls_per_email'], 0)
        
    def test_subject_analysis(self):
        """Test subject line analysis"""
        df = pd.DataFrame({
            'subject': ['Re: Meeting', 'Fwd: Important', 'Regular subject', 'Another regular subject']
        })
        
        content_analysis = self.analyzer.analyze_content(df)
        subject_analysis = content_analysis['subject_analysis']
        
        self.assertEqual(subject_analysis['prefix_analysis']['emails_with_prefixes'], 2)
        self.assertEqual(subject_analysis['prefix_analysis']['prefix_rate'], 50.0)


class TestInsightsGenerator(unittest.TestCase):
    """Test cases for insights generation"""
    
    def setUp(self):
        self.config = {
            'alert_thresholds': {
                'volume_spike_multiplier': 3.0,
                'new_sender_threshold': 50
            }
        }
        self.generator = InsightsGenerator(self.config)
        
    def test_volume_insights(self):
        """Test volume-based insights generation"""
        analysis_results = {
            'temporal_analysis': {
                'volume_patterns': {
                    'daily_average': 100.0,
                    'volatility': 1.5
                },
                'peak_analysis': {
                    'peaks_detected': 3,
                    'peak_frequency_percent': 15.0
                }
            }
        }
        
        insights = self.generator.generate_insights(analysis_results)
        volume_insights = insights['volume_insights']
        
        self.assertGreater(len(volume_insights), 0)
        
    def test_recommendations_generation(self):
        """Test actionable recommendations generation"""
        analysis_results = {
            'classification_summary': {
                'Financial': {'percentage': 35.0, 'count': 350},
                'Notifications': {'percentage': 25.0, 'count': 250}
            },
            'sender_analysis': {
                'automation_analysis': {'automation_rate': 65.0},
                'sender_diversity': {'top_10_concentration': 0.7}
            },
            'content_analysis': {
                'length_statistics': {
                    'basic_stats': {'mean': 6000}
                }
            },
            'temporal_analysis': {
                'volume_patterns': {'daily_average': 120.0}
            },
            'metadata': {'total_emails': 1000}
        }
        
        insights = self.generator.generate_insights(analysis_results)
        recommendations = insights['recommendations']
        
        self.assertGreater(len(recommendations), 0)
        
        # Check for high-priority financial recommendation
        financial_rec = next((r for r in recommendations if 'Financial' in r.get('category', '')), None)
        self.assertIsNotNone(financial_rec)
        self.assertEqual(financial_rec['priority'], 'High')


class TestDailyEmailAnalyzer(unittest.TestCase):
    """Integration tests for the complete analysis system"""
    
    def setUp(self):
        # Create a temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        config = {
            'quality_thresholds': {'min_completeness': 90.0},
            'classification_rules': {
                'Financial': {
                    'priority': 1,
                    'keywords': ['payment', 'bill'],
                    'sender_patterns': ['billing@']
                }
            },
            'temporal_analysis': {'peak_detection_threshold': 2.0},
            'sender_analysis': {'top_senders_count': 10},
            'content_analysis': {'length_buckets': [0, 1000, 5000, 10000]},
            'logging_config': {'log_level': 'WARNING'}  # Reduce log noise during tests
        }
        json.dump(config, self.temp_config)
        self.temp_config.close()
        
        self.analyzer = DailyEmailAnalyzer(self.temp_config.name)
        
    def tearDown(self):
        # Clean up temporary config file
        os.unlink(self.temp_config.name)
        
    def test_complete_analysis_pipeline(self):
        """Test the complete analysis pipeline end-to-end"""
        # Create comprehensive test data
        df = pd.DataFrame({
            'gmail_id': [f'id_{i:03d}' for i in range(20)],
            'date_received': [
                datetime.now() - timedelta(days=i//5, hours=i%24) 
                for i in range(20)
            ],
            'subject': [
                'Payment Receipt', 'Newsletter', 'Meeting Reminder', 'Bill Statement'
            ] * 5,
            'sender': [
                'billing@company.com', 'newsletter@news.com', 
                'calendar@work.com', 'statements@bank.com'
            ] * 5,
            'plain_text_content': [
                'Your payment of $100 has been processed.',
                'Weekly newsletter with updates.',
                'Meeting scheduled for tomorrow.',
                'Monthly statement available.'
            ] * 5
        })
        
        results = self.analyzer.analyze_emails(df)
        
        # Verify all major sections are present
        self.assertIn('metadata', results)
        self.assertIn('quality_metrics', results)
        self.assertIn('classification_summary', results)
        self.assertIn('temporal_analysis', results)
        self.assertIn('sender_analysis', results)
        self.assertIn('content_analysis', results)
        self.assertIn('insights', results)
        
        # Verify no errors
        self.assertNotIn('error', results)
        
        # Verify quality passed
        self.assertTrue(results['quality_metrics']['quality_passed'])
        
        # Verify classification worked
        self.assertGreater(len(results['classification_summary']), 0)
        
        # Verify insights generated
        self.assertIn('recommendations', results['insights'])
        
    def test_summary_report_generation(self):
        """Test summary report generation"""
        # Simple test data
        df = pd.DataFrame({
            'gmail_id': ['id_001', 'id_002'],
            'date_received': [datetime.now(), datetime.now()],
            'subject': ['Payment Receipt', 'Newsletter'],
            'sender': ['billing@company.com', 'newsletter@news.com'],
            'plain_text_content': ['Payment processed', 'Weekly updates']
        })
        
        results = self.analyzer.analyze_emails(df)
        summary = self.analyzer.generate_summary_report(results)
        
        self.assertIn('EMAIL ANALYSIS SUMMARY', summary)
        self.assertIn('CATEGORY DISTRIBUTION', summary)
        self.assertIn('Total Emails: 2', summary)
        
    def test_date_range_analysis(self):
        """Test date range filtering"""
        # Create data spanning multiple days
        df = pd.DataFrame({
            'gmail_id': [f'id_{i:03d}' for i in range(10)],
            'date_received': [
                datetime(2025, 9, 20) + timedelta(days=i) 
                for i in range(10)
            ],
            'subject': ['Test'] * 10,
            'sender': ['test@example.com'] * 10,
            'plain_text_content': ['Content'] * 10
        })
        
        results = self.analyzer.analyze_date_range(df, '2025-09-22', '2025-09-24')
        
        # Should contain 3 emails (days 22, 23, 24)
        self.assertEqual(results['metadata']['emails_in_range'], 3)
        self.assertIn('date_range', results['metadata'])


def create_test_suite():
    """Create and return the complete test suite"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDataQualityAssessment,
        TestHierarchicalClassifier,
        TestTemporalAnalyzer,
        TestSenderAnalyzer,
        TestContentAnalyzer,
        TestInsightsGenerator,
        TestDailyEmailAnalyzer
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_tests():
    """Run all tests and return results"""
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running Daily Email Analysis Test Suite")
    print("=" * 60)

    success = run_tests()

    if success:
        print("\nAll tests passed! The analysis system is working correctly.")
    else:
        print("\nSome tests failed. Please check the output above.")
        sys.exit(1)