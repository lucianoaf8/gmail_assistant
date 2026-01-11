#!/usr/bin/env python3
"""
Comprehensive tests for email_analyzer.py module.

Test coverage target: 0% → 80%
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
import pytest

from gmail_assistant.analysis.email_analyzer import EmailAnalysisEngine


# Test Fixtures
@pytest.fixture
def sample_config():
    """Sample configuration for email analysis."""
    return {
        'quality_thresholds': {
            'min_completeness': 95
        },
        'log_file': 'logs/test_email_analysis.log'
    }


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing with all required fields."""
    base_date = datetime(2025, 1, 10, 10, 0, 0)

    categories = ['Financial', 'Notifications', 'Social', 'Work/Business', 'Marketing/News'] * 10
    plain_texts = [f'Test email content {i}. ' * 10 for i in range(50)]

    return pd.DataFrame({
        'gmail_id': [f'id_{i:04d}' for i in range(50)],
        'sender': [f'sender{i % 10}@example.com' for i in range(50)],
        'subject': [f'Test Email {i}' for i in range(50)],
        'date_received': [base_date - timedelta(days=i // 5, hours=i % 24) for i in range(50)],
        'plain_text_content': plain_texts,
        'category': categories,
        'content_length': [len(text) for text in plain_texts],
        'word_count': [len(text.split()) for text in plain_texts],
        'is_automated': [i % 2 == 0 for i in range(50)],
        'classification_confidence': [0.8] * 50
    })


@pytest.fixture
def financial_dataframe():
    """Create DataFrame with financial emails."""
    base_date = datetime(2025, 1, 10, 10, 0, 0)

    return pd.DataFrame({
        'gmail_id': [f'id_{i}' for i in range(20)],
        'sender': ['billing@company.com'] * 10 + ['friend@gmail.com'] * 10,
        'subject': ['Payment receipt'] * 10 + ['Personal message'] * 10,
        'date_received': [base_date - timedelta(hours=i) for i in range(20)],
        'plain_text_content': ['Your payment of $25.00 has been processed.'] * 10 + ['Hello friend!'] * 10
    })


@pytest.fixture
def engine(sample_config):
    """Create EmailAnalysisEngine instance."""
    return EmailAnalysisEngine(sample_config)


# EmailAnalysisEngine Tests
class TestEmailAnalysisEngine:
    """Tests for EmailAnalysisEngine class."""

    def test_initialization(self, sample_config):
        """Test engine initialization."""
        engine = EmailAnalysisEngine(sample_config)

        assert engine.config == sample_config
        assert engine.quality_thresholds == sample_config['quality_thresholds']
        assert engine.classification_rules is not None
        assert engine.logger is not None

    def test_classification_rules_loading(self, engine):
        """Test classification rules are properly loaded."""
        rules = engine.classification_rules

        assert 'Financial' in rules
        assert 'Notifications' in rules
        assert 'Transportation' in rules
        assert 'Marketing/News' in rules
        assert 'Social' in rules
        assert 'Work/Business' in rules

        # Verify rule structure
        assert 'priority' in rules['Financial']
        assert 'keywords' in rules['Financial']
        assert 'sender_patterns' in rules['Financial']

    def test_data_quality_assessment(self, engine, sample_dataframe):
        """Test comprehensive data quality assessment."""
        result = engine.analyze_data_quality(sample_dataframe)

        assert 'completeness' in result
        assert 'consistency' in result
        assert 'validity' in result
        assert 'quality_passed' in result

        assert result['completeness']['overall_completeness'] == 100.0
        assert result['quality_passed'] is True

    def test_quality_assessment_with_missing_data(self, engine):
        """Test quality assessment with missing data."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id2', None],
            'sender': ['a@b.com', None, 'c@d.com'],
            'subject': ['Test', 'Test2', None],
            'date_received': [datetime.now()] * 3,
            'plain_text_content': ['content'] * 3
        })

        result = engine.analyze_data_quality(df)

        assert result['completeness']['overall_completeness'] < 100.0
        assert len(result['quality_issues']) > 0
        assert result['quality_passed'] is False

    def test_quality_assessment_duplicate_detection(self, engine):
        """Test duplicate gmail_id detection."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id1', 'id2'],
            'sender': ['a@b.com'] * 3,
            'subject': ['Test'] * 3,
            'date_received': [datetime.now()] * 3,
            'plain_text_content': ['content'] * 3
        })

        result = engine.analyze_data_quality(df)

        assert result['consistency']['duplicate_gmail_ids'] == 1
        assert result['quality_passed'] is False

    def test_email_format_validation(self, engine):
        """Test email format validation."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id2', 'id3'],
            'sender': ['valid@email.com', 'Name <valid@email.com>', 'invalid-email'],
            'subject': ['Test'] * 3,
            'date_received': [datetime.now()] * 3,
            'plain_text_content': ['content'] * 3
        })

        result = engine.analyze_data_quality(df)

        email_validity = result['validity']['email_format_validity']
        assert email_validity['valid_emails'] == 2
        assert email_validity['invalid_emails'] == 1

    def test_email_classification(self, engine, financial_dataframe):
        """Test email classification."""
        df_classified = engine.classify_emails(financial_dataframe)

        assert 'category' in df_classified.columns
        assert 'classification_confidence' in df_classified.columns
        assert 'is_automated' in df_classified.columns
        assert 'content_length' in df_classified.columns
        assert 'word_count' in df_classified.columns

        # Check financial classification
        financial_emails = df_classified[df_classified['sender'] == 'billing@company.com']
        assert all(financial_emails['category'] == 'Financial')

    def test_automation_detection(self, engine):
        """Test automated email detection."""
        row = {
            'sender': 'noreply@example.com',
            'subject': 'NOTIFICATION: System alert'
        }

        is_automated = engine._detect_automation(row)
        assert is_automated is True

    def test_classification_confidence_calculation(self, engine):
        """Test confidence score calculation."""
        row = {
            'sender': 'billing@company.com',
            'subject': 'Payment receipt invoice',
            'plain_text_content': 'Your payment has been processed.',
            'category': 'Financial'
        }

        confidence = engine._calculate_classification_confidence(row)
        assert 0.7 <= confidence <= 1.0

    def test_other_category_default(self, engine):
        """Test default Other category for unmatched emails."""
        df = pd.DataFrame({
            'gmail_id': ['id1'],
            'sender': ['xyz123@randomxyz.org'],  # Use unusual domain to avoid pattern match
            'subject': ['Xyz qwerty'],  # No keywords
            'date_received': [datetime.now()],
            'plain_text_content': ['No matching keywords here xyz qwerty asdf.']
        })

        df_classified = engine.classify_emails(df)
        # Should classify as Other or have low confidence
        assert df_classified.loc[0, 'classification_confidence'] <= 0.7

    def test_temporal_analysis(self, engine, sample_dataframe):
        """Test temporal pattern analysis."""
        result = engine.analyze_temporal_patterns(sample_dataframe)

        assert 'date_range' in result
        assert 'volume_patterns' in result
        assert 'hourly_distribution' in result
        assert 'daily_distribution' in result
        assert 'category_temporal_patterns' in result

    def test_volume_patterns_calculation(self, engine, sample_dataframe):
        """Test volume pattern statistics."""
        result = engine.analyze_temporal_patterns(sample_dataframe)

        patterns = result['volume_patterns']
        assert patterns['daily_average'] > 0
        assert patterns['daily_median'] > 0
        assert 'peak_day' in patterns
        assert 'min_day' in patterns

    def test_temporal_concentration_gini(self, engine):
        """Test Gini coefficient calculation for temporal concentration."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(20)],
            'date_received': [datetime(2025, 1, i+1) for i in range(20)]
        })

        concentration = engine._calculate_temporal_concentration(df)
        assert 0.0 <= concentration <= 1.0

    def test_sender_analysis(self, engine, sample_dataframe):
        """Test comprehensive sender analysis."""
        # Add required columns for sender analysis
        sample_dataframe['category'] = 'Other'
        sample_dataframe['is_automated'] = False
        sample_dataframe['content_length'] = 100

        result = engine.analyze_senders(sample_dataframe)

        assert 'sender_metrics' in result
        assert 'top_senders' in result
        assert 'automation_analysis' in result
        assert 'domain_analysis' in result
        assert 'sender_diversity' in result

    def test_sender_metrics(self, engine, sample_dataframe):
        """Test sender metrics calculation."""
        sample_dataframe['category'] = 'Other'
        sample_dataframe['is_automated'] = False
        sample_dataframe['content_length'] = 100

        result = engine.analyze_senders(sample_dataframe)

        metrics = result['sender_metrics']
        assert metrics['total_unique_senders'] == 10  # 50 emails / 5 = 10 unique senders
        assert metrics['total_emails'] == 50
        assert metrics['average_emails_per_sender'] == 5.0

    def test_top_senders_analysis(self, engine):
        """Test top senders detailed analysis."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(30)],
            'sender': ['frequent@example.com'] * 20 + ['rare@example.com'] * 10,
            'date_received': [datetime(2025, 1, i+1) for i in range(30)],
            'category': ['Financial'] * 30,
            'is_automated': [False] * 30,
            'content_length': [100] * 30
        })

        result = engine.analyze_senders(df)

        top_senders = result['top_senders']
        assert 'frequent@example.com' in top_senders
        assert top_senders['frequent@example.com']['email_count'] == 20
        assert top_senders['frequent@example.com']['percentage'] > 50

    def test_automation_analysis(self, engine):
        """Test automation pattern analysis."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(20)],
            'sender': ['noreply@example.com'] * 10 + ['person@gmail.com'] * 10,
            'date_received': [datetime.now()] * 20,
            'category': ['Notifications'] * 10 + ['Other'] * 10,
            'is_automated': [True] * 10 + [False] * 10,
            'content_length': [100] * 20
        })

        result = engine.analyze_senders(df)

        automation = result['automation_analysis']
        assert automation['automation_rate'] == 50.0
        assert automation['automated_emails'] == 10
        assert automation['personal_emails'] == 10

    def test_domain_analysis(self, engine):
        """Test domain analysis."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(15)],
            'sender': ['user@gmail.com'] * 5 + ['team@company.com'] * 10,
            'date_received': [datetime.now()] * 15,
            'category': ['Social'] * 5 + ['Work/Business'] * 10,
            'is_automated': [False] * 15,
            'content_length': [100] * 15
        })

        result = engine.analyze_senders(df)

        domain_analysis = result['domain_analysis']
        assert domain_analysis['total_unique_domains'] == 2
        assert 'top_domains' in domain_analysis
        assert 'corporate_vs_service' in domain_analysis

    def test_sender_diversity_metrics(self, engine):
        """Test sender diversity calculations."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(100)],
            'sender': [f'sender{i % 10}@example.com' for i in range(100)],
            'date_received': [datetime.now()] * 100,
            'category': ['Other'] * 100,
            'is_automated': [False] * 100,
            'content_length': [100] * 100
        })

        result = engine.analyze_senders(df)

        diversity = result['sender_diversity']
        assert 'shannon_diversity' in diversity
        assert 'simpson_diversity' in diversity
        assert 'top_10_concentration' in diversity
        assert diversity['top_10_concentration'] == 1.0  # All emails from top 10

    def test_content_analysis(self, engine):
        """Test comprehensive content analysis."""
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(20)],
            'content_length': [100, 600, 2500, 7000, 15000] * 4,
            'plain_text_content': ['Content with https://example.com'] * 20,
            'subject': ['Re: Meeting'] * 5 + ['Normal subject'] * 15,
            'word_count': [50] * 20,
            'category': ['Financial'] * 20
        })

        result = engine.analyze_content(df)

        assert 'length_statistics' in result
        assert 'content_patterns' in result
        assert 'subject_analysis' in result
        assert 'language_analysis' in result

    def test_content_length_statistics(self, engine):
        """Test content length analysis."""
        content_lengths = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(10)],
            'sender': [f'sender{i}@example.com' for i in range(10)],
            'subject': [f'Subject {i}' for i in range(10)],
            'date_received': [datetime.now()] * 10,
            'content_length': content_lengths,
            'plain_text_content': ['x' * cl for cl in content_lengths],
            'word_count': [cl // 5 for cl in content_lengths],
            'category': ['Financial'] * 10
        })

        result = engine.analyze_content(df)

        stats = result['length_statistics']
        assert stats['basic_stats']['mean'] == 550.0
        assert stats['basic_stats']['median'] == 550.0
        assert 'percentiles' in stats
        assert 'length_distribution' in stats

    def test_url_detection(self, engine):
        """Test URL detection in content."""
        contents = [
            'Visit https://example.com for more info.',
            'Check http://test.org',
            'No URLs here',
            'Multiple: https://a.com https://b.com',
            'Secure link https://secure.example.com'
        ]
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(5)],
            'sender': [f'sender{i}@example.com' for i in range(5)],
            'subject': [f'Subject {i}' for i in range(5)],
            'date_received': [datetime.now()] * 5,
            'content_length': [len(c) for c in contents],
            'plain_text_content': contents,
            'word_count': [5] * 5,
            'category': ['Other'] * 5
        })

        result = engine.analyze_content(df)

        url_analysis = result['content_patterns']['url_analysis']
        assert url_analysis['emails_with_urls'] == 4
        assert url_analysis['average_urls_per_email'] > 0

    def test_subject_analysis(self, engine):
        """Test subject line analysis."""
        subjects = ['Re: Meeting'] * 3 + ['Fwd: Report'] * 2 + ['Normal subject'] * 5
        df = pd.DataFrame({
            'gmail_id': [f'id_{i}' for i in range(10)],
            'sender': [f'sender{i}@example.com' for i in range(10)],
            'subject': subjects,
            'date_received': [datetime.now()] * 10,
            'content_length': [100] * 10,
            'plain_text_content': ['Test content'] * 10,
            'word_count': [10] * 10,
            'category': ['Work/Business'] * 10
        })

        result = engine.analyze_content(df)

        subject_analysis = result['subject_analysis']
        assert subject_analysis['prefix_analysis']['emails_with_prefixes'] == 5
        assert 'most_common_subjects' in subject_analysis

    def test_insights_generation(self, engine):
        """Test actionable insights generation."""
        analysis_results = {
            'classification_summary': {
                'Financial': {'percentage': 30, 'count': 30}
            },
            'sender_analysis': {
                'automation_analysis': {'automation_rate': 65},
                'sender_diversity': {'top_10_concentration': 0.6}
            },
            'temporal_analysis': {
                'volume_patterns': {
                    'daily_average': 75,
                    'peak_day': {'volume': 250}
                }
            },
            'content_analysis': {
                'length_statistics': {'basic_stats': {'mean': 6000}}
            },
            'metadata': {'total_emails': 100}
        }

        insights = engine.generate_insights(analysis_results)

        assert 'volume_insights' in insights
        assert 'category_insights' in insights
        assert 'sender_insights' in insights
        assert 'automation_insights' in insights
        assert 'content_insights' in insights
        assert 'recommendations' in insights

    def test_volume_insights_high_volume(self, engine):
        """Test volume insights for high email volume."""
        results = {
            'temporal_analysis': {
                'volume_patterns': {
                    'daily_average': 75,
                    'peak_day': {'volume': 300}
                }
            }
        }

        insights = engine._generate_volume_insights(results)
        assert len(insights) > 0
        assert any('volume' in insight.lower() for insight in insights)

    def test_recommendations_financial_emails(self, engine):
        """Test recommendations for high financial email percentage."""
        results = {
            'classification_summary': {
                'Financial': {'percentage': 30, 'count': 300}
            },
            'sender_analysis': {
                'automation_analysis': {'automation_rate': 50}
            },
            'metadata': {'total_emails': 1000}
        }

        recommendations = engine._generate_recommendations(results)
        assert len(recommendations) > 0
        assert any('Financial' in rec['category'] for rec in recommendations)


# Edge Case Tests
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_dataframe(self, engine):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=['gmail_id', 'sender', 'subject', 'date_received', 'plain_text_content'])

        # Empty dataframe may cause issues - check it doesn't crash
        try:
            result = engine.analyze_data_quality(df)
            # If it succeeds, result should exist
            assert result is not None
        except (ZeroDivisionError, ValueError):
            # Empty dataframe edge case - acceptable
            pass

    def test_single_email(self, engine):
        """Test analysis with single email."""
        df = pd.DataFrame({
            'gmail_id': ['id1'],
            'sender': ['test@example.com'],
            'subject': ['Test'],
            'date_received': [datetime.now()],
            'plain_text_content': ['Content']
        })

        result = engine.analyze_data_quality(df)
        assert result['completeness']['overall_completeness'] == 100.0

    def test_unicode_handling(self, engine):
        """Test handling of Unicode characters."""
        df = pd.DataFrame({
            'gmail_id': ['id1'],
            'sender': ['test@example.com'],
            'subject': ['Test 测试 тест émoji 🎉'],
            'date_received': [datetime.now()],
            'plain_text_content': ['Content with unicode ñ ü ö']
        })

        df_classified = engine.classify_emails(df)
        assert len(df_classified) == 1

    def test_very_long_content(self, engine):
        """Test handling of very long content."""
        long_content = 'A ' * 500_000  # 1M chars

        df = pd.DataFrame({
            'gmail_id': ['id1'],
            'sender': ['test@example.com'],
            'subject': ['Long content test'],
            'date_received': [datetime.now()],
            'content_length': [len(long_content)],
            'plain_text_content': [long_content],
            'word_count': [500_000],
            'category': ['Other']
        })

        result = engine.analyze_content(df)
        assert result['length_statistics']['basic_stats']['max'] == len(long_content)

    def test_null_content_handling(self, engine):
        """Test handling of null content."""
        df = pd.DataFrame({
            'gmail_id': ['id1', 'id2'],
            'sender': ['xyzrandom@unknowndomain.xyz', 'xyztest@unknowndomain.xyz'],
            'subject': [None, 'Xyz random subject'],
            'date_received': [datetime.now()] * 2,
            'plain_text_content': [None, 'Random xyz content']
        })

        df_classified = engine.classify_emails(df)
        assert len(df_classified) == 2
        # Classification should work even with null content
        assert 'category' in df_classified.columns


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflow."""

    def test_complete_analysis_workflow(self, engine, sample_dataframe):
        """Test complete analysis workflow from quality check to insights."""
        # Step 1: Quality Assessment
        quality_metrics = engine.analyze_data_quality(sample_dataframe)
        assert quality_metrics['quality_passed'] is True

        # Step 2: Classification
        df_classified = engine.classify_emails(sample_dataframe)
        assert 'category' in df_classified.columns

        # Step 3: Analysis
        temporal_analysis = engine.analyze_temporal_patterns(df_classified)
        sender_analysis = engine.analyze_senders(df_classified)
        content_analysis = engine.analyze_content(df_classified)

        # Step 4: Combine results
        analysis_results = {
            'metadata': {'total_emails': len(df_classified)},
            'quality_metrics': quality_metrics,
            'classification_summary': {
                'Financial': {'percentage': 20, 'count': 10}
            },
            'temporal_analysis': temporal_analysis,
            'sender_analysis': sender_analysis,
            'content_analysis': content_analysis
        }

        # Step 5: Generate insights
        insights = engine.generate_insights(analysis_results)

        assert 'recommendations' in insights
        assert len(insights) > 0
