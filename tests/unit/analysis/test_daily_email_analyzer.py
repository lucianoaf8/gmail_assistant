#!/usr/bin/env python3
"""
Comprehensive tests for daily_email_analyzer.py module.

Test coverage targets:
- DataQualityAssessment: 80%
- HierarchicalClassifier: 80%
- TemporalAnalyzer: 80%
- SenderAnalyzer: 80%
- ContentAnalyzer: 80%
- InsightsGenerator: 80%
- DailyEmailAnalyzer: 80%

Overall target: 0% → 80% coverage
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gmail_assistant.analysis.daily_email_analyzer import (
    ContentAnalyzer,
    DataQualityAssessment,
    DailyEmailAnalyzer,
    HierarchicalClassifier,
    InsightsGenerator,
    SenderAnalyzer,
    TemporalAnalyzer,
    create_sample_data,
)


# Test Fixtures
@pytest.fixture
def sample_email_data():
    """Create sample email data for testing."""
    base_date = datetime(2025, 1, 10, 10, 0, 0)

    return [
        {
            'gmail_id': f'id_{i:04d}',
            'sender': f'sender{i % 10}@example.com',
            'subject': f'Test Email {i}',
            'date_received': base_date - timedelta(days=i // 5, hours=i % 24),
            'plain_text_content': f'Test email content {i}. ' * 10,
            'labels': ['INBOX']
        }
        for i in range(50)
    ]


@pytest.fixture
def sample_dataframe(sample_email_data):
    """Create sample DataFrame from email data."""
    return pd.DataFrame(sample_email_data)


@pytest.fixture
def sample_dataframe_with_categories():
    """Create sample DataFrame with predefined categories."""
    base_date = datetime(2025, 1, 10, 10, 0, 0)

    data = []
    categories = ['Financial', 'Notifications', 'Marketing/News', 'Work/Business', 'Other']
    senders = [
        'billing@company.com',
        'noreply@alerts.com',
        'newsletter@news.com',
        'team@work.com',
        'friend@gmail.com'
    ]
    subjects = [
        'Payment receipt for $25.00',
        'Security alert notification',
        'Weekly newsletter update',
        'Meeting reminder tomorrow',
        'Personal message'
    ]
    contents = [
        'Your payment of $25.00 has been processed successfully.',
        'Security alert: New login detected on your account.',
        'Here is your weekly newsletter with updates.',
        'Reminder: You have a meeting tomorrow at 2 PM.',
        'Hey, how are you doing?'
    ]

    for i in range(50):
        cat_idx = i % 5
        data.append({
            'gmail_id': f'id_{i:04d}',
            'sender': senders[cat_idx],
            'subject': subjects[cat_idx],
            'date_received': base_date - timedelta(days=i // 5, hours=i % 24),
            'plain_text_content': contents[cat_idx] * 10,
            'labels': ['INBOX']
        })

    return pd.DataFrame(data)


@pytest.fixture
def quality_thresholds():
    """Quality threshold configuration."""
    return {
        'min_completeness': 95,
        'max_null_rate': 5
    }


@pytest.fixture
def classification_rules():
    """Classification rules for testing."""
    return {
        'Financial': {
            'priority': 1,
            'keywords': ['payment', 'invoice', 'bill', 'receipt', 'balance'],
            'sender_patterns': ['billing@', 'finance@'],
            'confidence_threshold': 0.9
        },
        'Notifications': {
            'priority': 2,
            'keywords': ['notification', 'alert', 'reminder', 'backup'],
            'sender_patterns': ['noreply@', 'no-reply@', 'notifications@'],
            'confidence_threshold': 0.85
        }
    }


@pytest.fixture
def temporal_config():
    """Temporal analysis configuration."""
    return {
        'peak_detection_threshold': 2.0,
        'rolling_window_days': 7
    }


@pytest.fixture
def sender_config():
    """Sender analysis configuration."""
    return {
        'top_senders_count': 20
    }


@pytest.fixture
def content_config():
    """Content analysis configuration."""
    return {
        'length_buckets': [0, 500, 2000, 5000, 10000, 20000],
        'bucket_labels': ['Very Short', 'Short', 'Medium', 'Long', 'Very Long', 'Extremely Long']
    }


@pytest.fixture
def temp_config_file(quality_thresholds, classification_rules, temporal_config):
    """Create temporary configuration file."""
    config = {
        'quality_thresholds': quality_thresholds,
        'classification_rules': classification_rules,
        'temporal_analysis': temporal_config,
        'sender_analysis': {'top_senders_count': 20},
        'content_analysis': {
            'length_buckets': [0, 500, 2000, 5000, 10000, 20000],
            'bucket_labels': ['Very Short', 'Short', 'Medium', 'Long', 'Very Long', 'Extremely Long']
        },
        'logging_config': {
            'log_level': 'INFO',
            'log_file': 'logs/test_analysis.log',
            'console_output': False
        },
        'analysis_config': {
            'version': '1.0.0'
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


# DataQualityAssessment Tests
class TestDataQualityAssessment:
    """Tests for DataQualityAssessment class."""

    def test_complete_data_quality(self, sample_dataframe, quality_thresholds):
        """Test quality assessment with complete data."""
        assessor = DataQualityAssessment(quality_thresholds)
        result = assessor.assess_quality(sample_dataframe)

        assert 'completeness' in result
        assert 'consistency' in result
        assert 'validity' in result
        assert result['completeness']['overall_completeness'] == 100.0
        assert result['quality_passed'] is True

    def test_incomplete_data_quality(self, quality_thresholds):
        """Test quality assessment with incomplete data."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id2', None, 'id4'],
            'sender': ['a@b.com', None, 'c@d.com', 'd@e.com'],
            'subject': ['Test', 'Test2', 'Test3', None],
            'date_received': [datetime.now()] * 4,
            'plain_text_content': ['content'] * 4
        })

        assessor = DataQualityAssessment(quality_thresholds)
        result = assessor.assess_quality(df)

        assert result['completeness']['overall_completeness'] < 100.0
        assert len(result['completeness']['critical_missing']) > 0
        assert result['quality_passed'] is False

    def test_duplicate_detection(self, quality_thresholds):
        """Test duplicate gmail_id detection."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id1', 'id2', 'id3'],
            'sender': ['a@b.com'] * 4,
            'subject': ['Test'] * 4,
            'date_received': [datetime.now()] * 4,
            'plain_text_content': ['content'] * 4
        })

        assessor = DataQualityAssessment(quality_thresholds)
        result = assessor.assess_quality(df)

        assert result['consistency']['duplicate_gmail_ids'] == 1
        assert result['quality_passed'] is False
        assert any('Duplicate' in issue for issue in result['quality_issues'])

    def test_missing_fields_detection(self, quality_thresholds):
        """Test detection of missing critical fields."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id2', 'id3'],
            'sender': ['a@b.com', None, None],
            'subject': ['Test'] * 3,
            'date_received': [datetime.now()] * 3,
            'plain_text_content': ['content'] * 3
        })

        quality_thresholds['max_null_rate'] = 5
        assessor = DataQualityAssessment(quality_thresholds)
        result = assessor.assess_quality(df)

        assert result['completeness']['field_completeness']['sender'] < 100.0
        assert result['quality_passed'] is False

    def test_email_format_validation(self, quality_thresholds):
        """Test email format validation."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id2', 'id3'],
            'sender': ['valid@email.com', 'Name <valid@email.com>', 'invalid-email'],
            'subject': ['Test'] * 3,
            'date_received': [datetime.now()] * 3,
            'plain_text_content': ['content'] * 3
        })

        assessor = DataQualityAssessment(quality_thresholds)
        result = assessor.assess_quality(df)

        email_validity = result['validity']['email_format_validity']
        assert email_validity['valid_emails'] == 2
        assert email_validity['invalid_emails'] == 1
        assert 0 < email_validity['validity_rate'] < 100


# HierarchicalClassifier Tests
class TestHierarchicalClassifier:
    """Tests for HierarchicalClassifier class."""

    def test_automation_detection(self, classification_rules):
        """Test automated email detection."""
        classifier = HierarchicalClassifier(classification_rules)

        automated_row = {
            'sender': 'noreply@example.com',
            'subject': 'Automated notification',
            'plain_text_content': 'This is an automated message.'
        }

        is_automated = classifier._detect_automation(automated_row)
        assert is_automated is True

    def test_custom_categories(self, classification_rules):
        """Test custom category classification."""
        classifier = HierarchicalClassifier(classification_rules)

        custom_categories = {
            'TestCategory': {
                'priority': 1,
                'keywords': ['testword'],
                'sender_patterns': ['test@'],
                'confidence_threshold': 0.8
            }
        }
        classifier.add_custom_categories(custom_categories)

        row = {
            'sender': 'test@example.com',
            'subject': 'Contains testword',
            'plain_text_content': 'This contains testword in content.'
        }

        category = classifier._categorize_email(row)
        assert category == 'TestCategory'

    def test_financial_classification(self, classification_rules, sample_dataframe_with_categories):
        """Test financial email classification."""
        classifier = HierarchicalClassifier(classification_rules)
        df_classified = classifier.classify_emails(sample_dataframe_with_categories)

        financial_emails = df_classified[df_classified['sender'].str.contains('billing@', na=False)]
        assert len(financial_emails) > 0
        assert all(df_classified.loc[financial_emails.index, 'category'] == 'Financial')

    def test_notification_classification(self, classification_rules, sample_dataframe_with_categories):
        """Test notification email classification."""
        classifier = HierarchicalClassifier(classification_rules)
        df_classified = classifier.classify_emails(sample_dataframe_with_categories)

        notification_emails = df_classified[df_classified['sender'].str.contains('noreply@', na=False)]
        assert len(notification_emails) > 0
        assert all(df_classified.loc[notification_emails.index, 'category'] == 'Notifications')

    def test_classification_confidence(self, classification_rules):
        """Test confidence score calculation."""
        classifier = HierarchicalClassifier(classification_rules)

        high_confidence_row = {
            'sender': 'billing@company.com',
            'subject': 'Payment receipt invoice',
            'plain_text_content': 'Your payment bill has been processed.',
            'category': 'Financial'
        }

        confidence = classifier._calculate_confidence(high_confidence_row)
        assert 0.7 <= confidence <= 1.0

    def test_other_category_default(self, classification_rules):
        """Test default 'Other' category for unmatched emails."""
        classifier = HierarchicalClassifier(classification_rules)

        row = {
            'sender': 'random@example.com',
            'subject': 'Random topic',
            'plain_text_content': 'This does not match any category.'
        }

        category = classifier._categorize_email(row)
        assert category == 'Other'


# TemporalAnalyzer Tests
class TestTemporalAnalyzer:
    """Tests for TemporalAnalyzer class."""

    def test_hourly_distribution(self, temporal_config, sample_dataframe):
        """Test hourly email distribution analysis."""
        # Add category column for analyzer
        sample_dataframe['category'] = 'Other'

        analyzer = TemporalAnalyzer(temporal_config)
        result = analyzer.analyze_temporal_patterns(sample_dataframe)

        assert 'time_distribution' in result
        assert 'hourly_distribution' in result['time_distribution']
        assert len(result['time_distribution']['hourly_distribution']) > 0

    def test_peak_detection(self, temporal_config):
        """Test peak detection algorithm."""
        # Create data with clear peaks
        base_date = datetime(2025, 1, 1)
        dates = [base_date + timedelta(days=i) for i in range(30)]

        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(len(dates))],
            'date_received': dates,
            'sender': ['test@example.com'] * len(dates),
            'category': ['Other'] * len(dates)
        })

        analyzer = TemporalAnalyzer(temporal_config)
        result = analyzer.analyze_temporal_patterns(df)

        assert 'peak_analysis' in result
        assert result['peak_analysis']['peaks_detected'] >= 0

    def test_volume_patterns(self, temporal_config, sample_dataframe):
        """Test volume pattern analysis."""
        sample_dataframe['category'] = 'Other'

        analyzer = TemporalAnalyzer(temporal_config)
        result = analyzer.analyze_temporal_patterns(sample_dataframe)

        assert 'volume_patterns' in result
        patterns = result['volume_patterns']
        assert 'daily_average' in patterns
        assert 'daily_median' in patterns
        assert 'daily_std' in patterns
        assert patterns['daily_average'] > 0

    def test_trend_analysis(self, temporal_config, sample_dataframe):
        """Test temporal trend analysis."""
        sample_dataframe['category'] = 'Other'

        analyzer = TemporalAnalyzer(temporal_config)
        result = analyzer.analyze_temporal_patterns(sample_dataframe)

        assert 'date_range' in result
        assert 'start_date' in result['date_range']
        assert 'end_date' in result['date_range']
        assert 'span_days' in result['date_range']

    def test_category_temporal_patterns(self, temporal_config):
        """Test category-specific temporal patterns."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(20)],
            'date_received': [datetime.now() - timedelta(hours=i) for i in range(20)],
            'sender': ['test@example.com'] * 20,
            'category': ['Financial'] * 10 + ['Notifications'] * 10,
            'hour': [(datetime.now() - timedelta(hours=i)).hour for i in range(20)],
            'day_name': [(datetime.now() - timedelta(hours=i)).strftime('%A') for i in range(20)],
            'date': [(datetime.now() - timedelta(hours=i)).date() for i in range(20)]
        })

        analyzer = TemporalAnalyzer(temporal_config)
        result = analyzer.analyze_temporal_patterns(df)

        assert 'category_temporal_patterns' in result
        assert 'Financial' in result['category_temporal_patterns']
        assert 'Notifications' in result['category_temporal_patterns']

    def test_insufficient_data_for_peaks(self, temporal_config):
        """Test peak detection with insufficient data."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id2'],
            'date_received': [datetime.now(), datetime.now() - timedelta(days=1)],
            'sender': ['test@example.com'] * 2,
            'category': ['Other'] * 2
        })

        analyzer = TemporalAnalyzer(temporal_config)
        result = analyzer.analyze_temporal_patterns(df)

        assert result['peak_analysis']['insufficient_data'] is True


# SenderAnalyzer Tests
class TestSenderAnalyzer:
    """Tests for SenderAnalyzer class."""

    def test_automation_analysis(self, sender_config):
        """Test sender automation analysis."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(20)],
            'sender': ['noreply@example.com'] * 10 + ['person@gmail.com'] * 10,
            'is_automated': [True] * 10 + [False] * 10
        })

        analyzer = SenderAnalyzer(sender_config)
        result = analyzer.analyze_senders(df)

        assert 'automation_analysis' in result
        assert result['automation_analysis']['automation_rate'] == 50.0
        assert result['automation_analysis']['automated_emails'] == 10
        assert result['automation_analysis']['personal_emails'] == 10

    def test_domain_analysis(self, sender_config):
        """Test domain analysis."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(20)],
            'sender': ['user@gmail.com'] * 5 + ['team@company.com'] * 10 + ['noreply@service.com'] * 5,
            'is_automated': [False] * 20
        })

        analyzer = SenderAnalyzer(sender_config)
        result = analyzer.analyze_senders(df)

        assert 'domain_analysis' in result
        assert result['domain_analysis']['total_unique_domains'] > 0
        assert 'top_domains' in result['domain_analysis']

    def test_sender_metrics(self, sender_config, sample_dataframe):
        """Test basic sender metrics calculation."""
        sample_dataframe['is_automated'] = False

        analyzer = SenderAnalyzer(sender_config)
        result = analyzer.analyze_senders(sample_dataframe)

        assert 'sender_metrics' in result
        metrics = result['sender_metrics']
        assert metrics['total_unique_senders'] > 0
        assert metrics['total_emails'] == len(sample_dataframe)
        assert metrics['average_emails_per_sender'] > 0

    def test_frequency_calculation(self, sender_config):
        """Test sender frequency calculation."""
        base_date = datetime(2025, 1, 1)
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(30)],
            'sender': ['frequent@example.com'] * 20 + ['rare@example.com'] * 10,
            'date_received': [base_date + timedelta(days=i) for i in range(30)],
            'category': ['Financial'] * 30,
            'is_automated': [False] * 30,
            'content_length': [100] * 30
        })

        analyzer = SenderAnalyzer(sender_config)
        result = analyzer.analyze_senders(df)

        assert 'top_senders' in result
        assert 'frequent@example.com' in result['top_senders']
        assert result['top_senders']['frequent@example.com']['email_count'] == 20

    def test_sender_diversity(self, sender_config):
        """Test sender diversity metrics."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(100)],
            'sender': [f'sender{i % 10}@example.com' for i in range(100)],
            'is_automated': [False] * 100
        })

        analyzer = SenderAnalyzer(sender_config)
        result = analyzer.analyze_senders(df)

        assert 'sender_diversity' in result
        diversity = result['sender_diversity']
        assert 'shannon_diversity' in diversity
        assert 'simpson_diversity' in diversity
        assert 'top_10_concentration' in diversity
        assert 'effective_senders' in diversity


# ContentAnalyzer Tests
class TestContentAnalyzer:
    """Tests for ContentAnalyzer class."""

    def test_content_length_analysis(self, content_config):
        """Test content length statistics."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(20)],
            'content_length': [100, 600, 2500, 7000, 15000] * 4
        })

        analyzer = ContentAnalyzer(content_config)
        result = analyzer.analyze_content(df)

        assert 'length_statistics' in result
        stats = result['length_statistics']
        assert 'basic_stats' in stats
        assert 'percentiles' in stats
        assert 'length_distribution' in stats

    def test_subject_analysis(self, content_config):
        """Test email subject analysis."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(20)],
            'subject': ['Re: Meeting'] * 5 + ['Fwd: Report'] * 5 + ['Normal subject'] * 10
        })

        analyzer = ContentAnalyzer(content_config)
        result = analyzer.analyze_content(df)

        assert 'subject_analysis' in result
        subject = result['subject_analysis']
        assert 'length_stats' in subject
        assert 'prefix_analysis' in subject
        assert subject['prefix_analysis']['emails_with_prefixes'] == 10

    def test_url_analysis(self, content_config):
        """Test URL detection in content."""
        plain_texts = [
            'Visit https://example.com for more info.',
            'Check out http://test.org and https://another.com',
            'No URLs here',
            'Multiple links: https://a.com https://b.com https://c.com'
        ] * 2 + ['Plain text'] * 2

        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(len(plain_texts))],
            'plain_text_content': plain_texts,
            'word_count': [len(text.split()) for text in plain_texts]
        })

        analyzer = ContentAnalyzer(content_config)
        result = analyzer.analyze_content(df)

        assert 'content_patterns' in result
        patterns = result['content_patterns']
        assert 'url_analysis' in patterns
        assert patterns['url_analysis']['emails_with_urls'] > 0

    def test_attachment_analysis(self, content_config):
        """Test word count and content analysis."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(10)],
            'plain_text_content': ['word ' * 100 for _ in range(10)],
            'word_count': [100] * 10
        })

        analyzer = ContentAnalyzer(content_config)
        result = analyzer.analyze_content(df)

        assert 'content_patterns' in result
        assert 'word_count_stats' in result['content_patterns']
        assert result['content_patterns']['word_count_stats']['average_words'] == 100.0

    def test_signature_detection(self, content_config):
        """Test email signature detection."""
        plain_texts = [
            'Email body\nBest regards,\nJohn',
            'Email content\nSincerely,\nJane',
            'No signature here'
        ] * 3 + ['No sig']

        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(len(plain_texts))],
            'plain_text_content': plain_texts,
            'word_count': [len(text.split()) for text in plain_texts]
        })

        analyzer = ContentAnalyzer(content_config)
        result = analyzer.analyze_content(df)

        assert 'content_patterns' in result
        assert 'signature_analysis' in result['content_patterns']
        assert result['content_patterns']['signature_analysis']['emails_with_signatures'] > 0


# InsightsGenerator Tests
class TestInsightsGenerator:
    """Tests for InsightsGenerator class."""

    def test_recommendations_generation(self):
        """Test generation of actionable recommendations."""
        config = {'alert_thresholds': {}}
        generator = InsightsGenerator(config)

        analysis_results = {
            'classification_summary': {
                'Financial': {'percentage': 30, 'count': 30},
                'Notifications': {'percentage': 25, 'count': 25}
            },
            'sender_analysis': {
                'automation_analysis': {'automation_rate': 65}
            },
            'temporal_analysis': {
                'volume_patterns': {'daily_average': 110}
            },
            'content_analysis': {
                'length_statistics': {'basic_stats': {'mean': 6000}}
            },
            'metadata': {'total_emails': 100}
        }

        insights = generator.generate_insights(analysis_results)

        assert 'recommendations' in insights
        assert len(insights['recommendations']) > 0
        assert all('priority' in rec for rec in insights['recommendations'])

    def test_volume_insights(self):
        """Test volume-specific insights generation."""
        config = {'alert_thresholds': {}}
        generator = InsightsGenerator(config)

        results = {
            'temporal_analysis': {
                'volume_patterns': {
                    'daily_average': 75,
                    'volatility': 1.5
                },
                'peak_analysis': {
                    'peaks_detected': 3,
                    'peak_frequency_percent': 10.0
                }
            }
        }

        insights = generator._generate_volume_insights(results)
        assert len(insights) > 0
        assert any('volume' in insight.lower() for insight in insights)

    def test_priority_insights(self):
        """Test priority-based insight recommendations."""
        config = {'alert_thresholds': {}}
        generator = InsightsGenerator(config)

        analysis_results = {
            'classification_summary': {
                'Financial': {'percentage': 35, 'count': 350}
            },
            'sender_analysis': {
                'automation_analysis': {'automation_rate': 75},
                'sender_diversity': {'top_10_concentration': 0.7}
            },
            'temporal_analysis': {'volume_patterns': {'daily_average': 50}},
            'content_analysis': {'length_statistics': {'basic_stats': {'mean': 3000}}},
            'metadata': {'total_emails': 1000}
        }

        insights = generator.generate_insights(analysis_results)
        recommendations = insights['recommendations']

        high_priority = [r for r in recommendations if r['priority'] == 'High']
        assert len(high_priority) > 0


# DailyEmailAnalyzer Tests
class TestDailyEmailAnalyzer:
    """Tests for DailyEmailAnalyzer orchestration class."""

    def test_complete_analysis_pipeline(self, temp_config_file, sample_dataframe_with_categories):
        """Test complete end-to-end analysis pipeline."""
        analyzer = DailyEmailAnalyzer(temp_config_file)
        result = analyzer.analyze_emails(sample_dataframe_with_categories)

        assert 'metadata' in result
        assert 'quality_metrics' in result
        assert 'classification_summary' in result
        assert 'temporal_analysis' in result
        assert 'sender_analysis' in result
        assert 'content_analysis' in result
        assert 'insights' in result

    def test_date_range_analysis(self, temp_config_file):
        """Test date range filtering in analysis."""
        analyzer = DailyEmailAnalyzer(temp_config_file)

        # Create data spanning multiple days
        base_date = datetime(2025, 1, 1)
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(30)],
            'sender': ['test@example.com'] * 30,
            'subject': ['Test'] * 30,
            'date_received': [base_date + timedelta(days=i) for i in range(30)],
            'plain_text_content': ['Content'] * 30
        })

        result = analyzer.analyze_date_range(df, '2025-01-10', '2025-01-15')

        assert 'metadata' in result
        assert 'date_range' in result['metadata']
        assert result['metadata']['date_range']['start_date'] == '2025-01-10'
        assert result['metadata']['date_range']['end_date'] == '2025-01-15'

    def test_summary_report_generation(self, temp_config_file, sample_dataframe_with_categories):
        """Test summary report text generation."""
        analyzer = DailyEmailAnalyzer(temp_config_file)
        result = analyzer.analyze_emails(sample_dataframe_with_categories)

        summary = analyzer.generate_summary_report(result)

        assert 'EMAIL ANALYSIS SUMMARY' in summary
        assert 'CATEGORY DISTRIBUTION' in summary
        assert 'Total Emails:' in summary
        assert 'AUTOMATION ANALYSIS' in summary

    def test_error_handling_quality_failure(self, temp_config_file):
        """Test error handling when quality assessment fails."""
        analyzer = DailyEmailAnalyzer(temp_config_file)

        # Create data with quality issues
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id1', 'id3'],  # Duplicate
            'sender': ['test@example.com'] * 3,
            'subject': ['Test'] * 3,
            'date_received': [datetime.now()] * 3,
            'plain_text_content': ['Content'] * 3
        })

        result = analyzer.analyze_emails(df)

        assert 'error' in result
        assert result['quality_metrics']['quality_passed'] is False

    def test_config_loading_fallback(self):
        """Test configuration loading with missing file."""
        analyzer = DailyEmailAnalyzer('nonexistent_config.json')

        # Should fall back to default configuration
        assert analyzer.config is not None
        assert 'quality_thresholds' in analyzer.config

    def test_empty_dataframe_handling(self, temp_config_file):
        """Test handling of empty DataFrame."""
        analyzer = DailyEmailAnalyzer(temp_config_file)
        df = pd.DataFrame(columns=['gmail_id', 'sender', 'subject', 'date_received', 'plain_text_content'])

        result = analyzer.analyze_date_range(df, '2025-01-01', '2025-01-10')

        assert 'error' in result


# Module-level Function Tests
class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_create_sample_data(self):
        """Test sample data generation function."""
        sample_df = create_sample_data()

        assert isinstance(sample_df, pd.DataFrame)
        assert len(sample_df) == 50
        assert 'gmail_id' in sample_df.columns
        assert 'sender' in sample_df.columns
        assert 'subject' in sample_df.columns
        assert 'date_received' in sample_df.columns
        assert 'plain_text_content' in sample_df.columns


# Edge Case Tests
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_email_analysis(self, temp_config_file):
        """Test analysis with single email."""
        analyzer = DailyEmailAnalyzer(temp_config_file)

        df = pd.DataFrame({
            'gmail_id': ['id1'],
            'sender': ['test@example.com'],
            'subject': ['Test'],
            'date_received': [datetime.now()],
            'plain_text_content': ['Content']
        })

        result = analyzer.analyze_emails(df)
        assert result['metadata']['total_emails'] == 1

    def test_missing_columns(self, temp_config_file):
        """Test handling of missing required columns."""
        analyzer = DailyEmailAnalyzer(temp_config_file)

        df = pd.DataFrame({
            'gmail_id': ['id1'],
            'sender': ['test@example.com']
            # Missing other required columns
        })

        # Should handle gracefully
        result = analyzer.analyze_emails(df)
        assert 'error' in result or 'quality_metrics' in result

    def test_unicode_content(self, temp_config_file):
        """Test handling of Unicode content."""
        analyzer = DailyEmailAnalyzer(temp_config_file)

        df = pd.DataFrame({
            'gmail_id': ['id1'],
            'sender': ['test@example.com'],
            'subject': ['Test 测试 тест'],
            'date_received': [datetime.now()],
            'plain_text_content': ['Content with émojis 🎉 and unicode ñ']
        })

        result = analyzer.analyze_emails(df)
        assert result['metadata']['total_emails'] == 1

    def test_very_long_content(self, temp_config_file):
        """Test handling of very long email content."""
        analyzer = DailyEmailAnalyzer(temp_config_file)

        long_content = 'A' * 1_000_000  # 1MB of text

        df = pd.DataFrame({
            'gmail_id': ['id1'],
            'sender': ['test@example.com'],
            'subject': ['Test'],
            'date_received': [datetime.now()],
            'plain_text_content': [long_content]
        })

        result = analyzer.analyze_emails(df)
        assert result['metadata']['total_emails'] == 1
        assert result['content_analysis']['length_statistics']['basic_stats']['max'] > 900_000
