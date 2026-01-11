#!/usr/bin/env python3
"""
Daily Email Analysis - Production Implementation
Comprehensive email analysis following the documented methodology.

Usage:
    python daily_email_analysis.py --date 2025-09-18 --config config.json
    python daily_email_analysis.py --yesterday  # Analyze yesterday's emails
    python daily_email_analysis.py --incremental --days 7  # Last 7 days
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


class EmailAnalysisEngine:
    """Core email analysis engine implementing the comprehensive methodology"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.classification_rules = self._load_classification_rules()
        self.quality_thresholds = config.get('quality_thresholds', {})
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for analysis pipeline"""
        logger = logging.getLogger('EmailAnalysis')
        logger.setLevel(logging.INFO)

        # Create handlers
        log_file = Path(self.config.get('log_file', 'logs/email_analysis.log'))
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _load_classification_rules(self) -> dict[str, dict]:
        """Load classification rules from configuration"""
        return {
            'Financial': {
                'priority': 1,
                'keywords': [
                    'payment', 'invoice', 'bill', 'receipt', 'balance', 'card', 'bank',
                    'transaction', 'charge', 'refund', 'statement', 'due', 'overdue',
                    'account', 'credit', 'debit', 'finance', 'money', 'cost', 'price',
                    'subscription', 'renewal', 'billing', 'paypal', 'stripe'
                ],
                'sender_patterns': ['billing@', 'finance@', 'payments@', 'noreply@.*bank']
            },
            'Notifications': {
                'priority': 2,
                'keywords': [
                    'notification', 'alert', 'reminder', 'backup', 'report', 'status',
                    'update', 'confirm', 'verification', 'security', 'warning', 'error',
                    'maintenance', 'system', 'server', 'service', 'monitoring'
                ],
                'sender_patterns': ['noreply@', 'no-reply@', 'notifications@', 'alerts@']
            },
            'Transportation': {
                'priority': 3,
                'keywords': [
                    'ride', 'trip', 'uber', 'lyft', 'bird', 'scooter', 'taxi', 'journey',
                    'pickup', 'dropoff', 'driver', 'vehicle', 'transportation', 'travel'
                ],
                'sender_patterns': ['@uber.com', '@lyft.com', '@bird.co']
            },
            'Marketing/News': {
                'priority': 4,
                'keywords': [
                    'newsletter', 'unsubscribe', 'marketing', 'offer', 'deal', 'promotion',
                    'sale', 'discount', 'coupon', 'news', 'update', 'announcement',
                    'campaign', 'launch', 'featured', 'exclusive', 'limited'
                ],
                'sender_patterns': ['marketing@', 'newsletter@', 'promotions@', 'news@']
            },
            'Social': {
                'priority': 5,
                'keywords': [
                    'social', 'friend', 'follow', 'like', 'comment', 'mention', 'tag',
                    'share', 'post', 'message', 'connection', 'network', 'community'
                ],
                'sender_patterns': ['@facebook.com', '@twitter.com', '@linkedin.com', '@instagram.com']
            },
            'Work/Business': {
                'priority': 6,
                'keywords': [
                    'meeting', 'project', 'work', 'team', 'deadline', 'task', 'calendar',
                    'conference', 'presentation', 'document', 'report', 'business',
                    'corporate', 'office', 'colleague', 'manager', 'client'
                ],
                'sender_patterns': ['@.*\\.com$', 'calendar@', 'teams@']
            }
        }

    def analyze_data_quality(self, df: pd.DataFrame) -> dict[str, Any]:
        """Comprehensive data quality assessment"""
        self.logger.info("Starting data quality assessment")

        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()

        quality_metrics = {
            'completeness': {
                'overall_completeness': (1 - null_cells / total_cells) * 100,
                'field_completeness': {
                    col: (1 - df[col].isnull().sum() / len(df)) * 100
                    for col in df.columns
                },
                'critical_missing': {
                    col: df[col].isnull().sum()
                    for col in df.columns if df[col].isnull().sum() > 0
                }
            },
            'consistency': {
                'duplicate_gmail_ids': df['gmail_id'].duplicated().sum(),
                'unique_gmail_ids': len(df['gmail_id'].unique()),
                'total_records': len(df),
                'id_uniqueness_rate': len(df['gmail_id'].unique()) / len(df) * 100
            },
            'validity': {
                'valid_dates': df['date_received'].notna().sum(),
                'date_range': {
                    'min_date': df['date_received'].min().isoformat() if df['date_received'].notna().any() else None,
                    'max_date': df['date_received'].max().isoformat() if df['date_received'].notna().any() else None,
                    'span_days': (df['date_received'].max() - df['date_received'].min()).days if df['date_received'].notna().any() else 0
                },
                'email_format_validity': self._validate_email_formats(df['sender'])
            }
        }

        # Quality gate validation
        quality_issues = []
        if quality_metrics['completeness']['overall_completeness'] < self.quality_thresholds.get('min_completeness', 95):
            quality_issues.append('Low data completeness')

        if quality_metrics['consistency']['duplicate_gmail_ids'] > 0:
            quality_issues.append('Duplicate gmail_ids detected')

        quality_metrics['quality_issues'] = quality_issues
        quality_metrics['quality_passed'] = len(quality_issues) == 0

        self.logger.info(f"Quality assessment complete. Issues: {len(quality_issues)}")
        return quality_metrics

    def _validate_email_formats(self, email_series: pd.Series) -> dict[str, int]:
        """Validate email format consistency"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        valid_emails = 0
        invalid_emails = 0

        for email in email_series.dropna():
            # Handle complex email formats like "Name <email@domain.com>"
            clean_email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(email))
            if clean_email and email_pattern.match(clean_email.group()):
                valid_emails += 1
            else:
                invalid_emails += 1

        return {
            'valid_emails': valid_emails,
            'invalid_emails': invalid_emails,
            'validity_rate': valid_emails / (valid_emails + invalid_emails) * 100 if (valid_emails + invalid_emails) > 0 else 0
        }

    def classify_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply hierarchical email classification"""
        self.logger.info("Starting email classification")

        def categorize_email(row):
            subject = str(row.get('subject', '')).lower()
            sender = str(row.get('sender', '')).lower()
            content = str(row.get('plain_text_content', '')).lower()

            # Combine text for analysis
            combined_text = f"{subject} {content}"

            # Apply classification rules in priority order
            for category, rules in sorted(self.classification_rules.items(),
                                        key=lambda x: x[1]['priority']):

                # Check keywords
                if any(keyword in combined_text for keyword in rules['keywords']):
                    return category

                # Check sender patterns
                for pattern in rules.get('sender_patterns', []):
                    if re.search(pattern, sender):
                        return category

            return 'Other'

        # Apply classification
        df['category'] = df.apply(categorize_email, axis=1)

        # Calculate classification confidence
        df['classification_confidence'] = df.apply(self._calculate_classification_confidence, axis=1)

        # Detect automation
        df['is_automated'] = df.apply(self._detect_automation, axis=1)

        # Calculate content metrics
        df['content_length'] = df['plain_text_content'].str.len().fillna(0)
        df['word_count'] = df['plain_text_content'].str.split().str.len().fillna(0)

        self.logger.info(f"Classification complete. Categories: {df['category'].value_counts().to_dict()}")
        return df

    def _calculate_classification_confidence(self, row) -> float:
        """Calculate confidence score for classification"""
        subject = str(row.get('subject', '')).lower()
        sender = str(row.get('sender', '')).lower()
        content = str(row.get('plain_text_content', '')).lower()
        category = row.get('category', 'Other')

        if category == 'Other':
            return 0.5

        combined_text = f"{subject} {content}"
        rules = self.classification_rules.get(category, {})

        # Count matching patterns
        keyword_matches = sum(1 for keyword in rules.get('keywords', [])
                            if keyword in combined_text)
        sender_matches = sum(1 for pattern in rules.get('sender_patterns', [])
                           if re.search(pattern, sender))

        total_patterns = len(rules.get('keywords', [])) + len(rules.get('sender_patterns', []))
        match_ratio = (keyword_matches + sender_matches) / max(total_patterns, 1)

        # Base confidence + match bonus
        confidence = 0.7 + (0.3 * min(match_ratio, 1.0))
        return round(confidence, 3)

    def _detect_automation(self, row) -> bool:
        """Detect if email is automated based on multiple indicators"""
        sender = str(row.get('sender', '')).lower()
        subject = str(row.get('subject', ''))

        automated_indicators = [
            'noreply', 'no-reply', 'notification', 'alert', 'service',
            'support', 'help', 'admin', 'system', 'donotreply',
            'automated', 'robot', 'bot', 'mailer-daemon'
        ]

        # Check sender patterns
        automation_score = sum(1 for indicator in automated_indicators if indicator in sender)

        # Check subject patterns
        if re.match(r'^(Re:|Fwd:|AUTO:|ALERT:|NOTIFICATION:)', subject):
            automation_score += 0.5

        # Check for common automated domains
        automated_domains = ['amazonaws.com', 'sendgrid.', 'mailgun.', 'mailchimp.']
        if any(domain in sender for domain in automated_domains):
            automation_score += 1

        return automation_score >= 1.0

    def analyze_temporal_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Comprehensive temporal analysis"""
        self.logger.info("Analyzing temporal patterns")

        df['date_received'] = pd.to_datetime(df['date_received'])

        # Daily patterns
        daily_volume = df.groupby(df['date_received'].dt.date).size()

        # Time-based patterns
        df['hour'] = df['date_received'].dt.hour
        df['day_of_week'] = df['date_received'].dt.dayofweek
        df['day_name'] = df['date_received'].dt.day_name()

        temporal_metrics = {
            'date_range': {
                'start_date': df['date_received'].min().isoformat(),
                'end_date': df['date_received'].max().isoformat(),
                'span_days': (df['date_received'].max() - df['date_received'].min()).days,
                'total_emails': len(df)
            },
            'volume_patterns': {
                'daily_average': daily_volume.mean(),
                'daily_median': daily_volume.median(),
                'daily_std': daily_volume.std(),
                'peak_day': {
                    'date': daily_volume.idxmax().isoformat(),
                    'volume': int(daily_volume.max())
                },
                'min_day': {
                    'date': daily_volume.idxmin().isoformat(),
                    'volume': int(daily_volume.min())
                }
            },
            'hourly_distribution': df['hour'].value_counts().sort_index().to_dict(),
            'daily_distribution': {
                'by_number': df['day_of_week'].value_counts().sort_index().to_dict(),
                'by_name': df['day_name'].value_counts().to_dict()
            },
            'category_temporal_patterns': self._analyze_category_temporal_patterns(df)
        }

        return temporal_metrics

    def _analyze_category_temporal_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze temporal patterns by email category"""
        patterns = {}

        for category in df['category'].unique():
            category_emails = df[df['category'] == category]

            patterns[category] = {
                'peak_hours': category_emails['hour'].value_counts().head(3).to_dict(),
                'peak_days': category_emails['day_name'].value_counts().head(3).to_dict(),
                'average_per_day': len(category_emails) / df['date_received'].dt.date.nunique(),
                'temporal_concentration': self._calculate_temporal_concentration(category_emails)
            }

        return patterns

    def _calculate_temporal_concentration(self, emails_df: pd.DataFrame) -> float:
        """Calculate how concentrated emails are in time (Gini coefficient)"""
        if len(emails_df) < 2:
            return 0.0

        daily_counts = emails_df.groupby(emails_df['date_received'].dt.date).size().values
        daily_counts = np.sort(daily_counts)

        n = len(daily_counts)
        cumsum = np.cumsum(daily_counts)

        # Gini coefficient calculation
        gini = (2 * np.sum((np.arange(1, n + 1)) * daily_counts)) / (n * np.sum(daily_counts)) - (n + 1) / n

        return round(gini, 3)

    def analyze_senders(self, df: pd.DataFrame) -> dict[str, Any]:
        """Comprehensive sender analysis"""
        self.logger.info("Analyzing sender patterns")

        sender_analysis = {
            'sender_metrics': {
                'total_unique_senders': df['sender'].nunique(),
                'total_emails': len(df),
                'average_emails_per_sender': len(df) / df['sender'].nunique()
            },
            'top_senders': self._analyze_top_senders(df),
            'automation_analysis': self._analyze_automation_patterns(df),
            'domain_analysis': self._analyze_domains(df),
            'sender_diversity': self._calculate_sender_diversity(df)
        }

        return sender_analysis

    def _analyze_top_senders(self, df: pd.DataFrame, top_n: int = 20) -> dict[str, Any]:
        """Detailed analysis of top email senders"""
        sender_counts = df['sender'].value_counts().head(top_n)

        top_senders = {}
        for sender, count in sender_counts.items():
            sender_emails = df[df['sender'] == sender]

            top_senders[sender] = {
                'email_count': int(count),
                'percentage': round(count / len(df) * 100, 2),
                'categories': sender_emails['category'].value_counts().to_dict(),
                'is_automated': bool(sender_emails['is_automated'].iloc[0]),
                'avg_content_length': int(sender_emails['content_length'].mean()),
                'date_range': {
                    'first': sender_emails['date_received'].min().isoformat(),
                    'last': sender_emails['date_received'].max().isoformat()
                },
                'sending_frequency': count / sender_emails['date_received'].dt.date.nunique()
            }

        return top_senders

    def _analyze_automation_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze automation patterns in email data"""
        automated_count = df['is_automated'].sum()
        total_count = len(df)

        return {
            'automation_rate': round(automated_count / total_count * 100, 2),
            'automated_emails': int(automated_count),
            'personal_emails': int(total_count - automated_count),
            'top_automated_senders': (
                df[df['is_automated'] == True]['sender']
                .value_counts().head(10).to_dict()
            ),
            'automation_by_category': (
                df.groupby('category')['is_automated']
                .agg(['count', 'sum', 'mean']).round(3).to_dict()
            )
        }

    def _analyze_domains(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze sender domains and patterns"""
        # Extract domains from sender emails
        df['sender_domain'] = df['sender'].str.extract(r'@([^>\s]+)')[0]

        domain_counts = df['sender_domain'].value_counts().head(20)

        return {
            'total_unique_domains': df['sender_domain'].nunique(),
            'top_domains': domain_counts.to_dict(),
            'domain_diversity': self._calculate_domain_diversity(df),
            'corporate_vs_service': self._classify_domain_types(domain_counts)
        }

    def _calculate_sender_diversity(self, df: pd.DataFrame) -> dict[str, float]:
        """Calculate sender diversity metrics"""
        sender_counts = df['sender'].value_counts()

        # Shannon diversity index
        proportions = sender_counts / sender_counts.sum()
        shannon_diversity = -np.sum(proportions * np.log(proportions))

        # Simpson diversity index
        simpson_diversity = 1 - np.sum(proportions ** 2)

        # Concentration ratio (top 10 senders)
        top_10_ratio = sender_counts.head(10).sum() / sender_counts.sum()

        return {
            'shannon_diversity': round(shannon_diversity, 3),
            'simpson_diversity': round(simpson_diversity, 3),
            'top_10_concentration': round(top_10_ratio, 3),
            'effective_senders': round(np.exp(shannon_diversity), 1)
        }

    def _calculate_domain_diversity(self, df: pd.DataFrame) -> float:
        """Calculate domain diversity using Shannon index"""
        domain_counts = df['sender_domain'].value_counts()
        proportions = domain_counts / domain_counts.sum()
        return round(-np.sum(proportions * np.log(proportions)), 3)

    def _classify_domain_types(self, domain_counts: pd.Series) -> dict[str, int]:
        """Classify domains into corporate, service, and personal categories"""
        service_patterns = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        service_indicators = ['noreply', 'mail', 'email', 'notify', 'alerts']

        corporate = 0
        service = 0
        personal = 0

        for domain, count in domain_counts.items():
            domain_lower = str(domain).lower()

            if domain_lower in service_patterns:
                personal += count
            elif any(indicator in domain_lower for indicator in service_indicators):
                service += count
            else:
                corporate += count

        return {
            'corporate': corporate,
            'service': service,
            'personal': personal
        }

    def analyze_content(self, df: pd.DataFrame) -> dict[str, Any]:
        """Comprehensive content analysis"""
        self.logger.info("Analyzing email content")

        content_metrics = {
            'length_statistics': self._analyze_content_length(df),
            'content_patterns': self._analyze_content_patterns(df),
            'subject_analysis': self._analyze_subjects(df),
            'language_analysis': self._analyze_language_patterns(df)
        }

        return content_metrics

    def _analyze_content_length(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze email content length patterns"""
        lengths = df['content_length']

        # Create length buckets
        length_buckets = pd.cut(
            lengths,
            bins=[0, 500, 2000, 5000, 10000, 20000, float('inf')],
            labels=['Very Short', 'Short', 'Medium', 'Long', 'Very Long', 'Extremely Long']
        )

        return {
            'basic_stats': {
                'mean': round(lengths.mean(), 1),
                'median': round(lengths.median(), 1),
                'std': round(lengths.std(), 1),
                'min': int(lengths.min()),
                'max': int(lengths.max())
            },
            'percentiles': {
                f'p{p}': int(lengths.quantile(p/100))
                for p in [25, 50, 75, 90, 95, 99]
            },
            'length_distribution': length_buckets.value_counts().to_dict(),
            'category_length_stats': (
                df.groupby('category')['content_length']
                .agg(['mean', 'median', 'std']).round(1).to_dict()
            )
        }

    def _analyze_content_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze patterns in email content"""
        content_series = df['plain_text_content'].astype(str)

        # URL analysis
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls_per_email = content_series.apply(lambda x: len(url_pattern.findall(x)))

        # Email signature detection (simple heuristic)
        signature_indicators = ['best regards', 'sincerely', 'thanks', 'cheers', 'signature']
        has_signature = content_series.str.lower().str.contains('|'.join(signature_indicators))

        return {
            'url_analysis': {
                'emails_with_urls': int(urls_per_email[urls_per_email > 0].count()),
                'average_urls_per_email': round(urls_per_email.mean(), 2),
                'max_urls_in_email': int(urls_per_email.max())
            },
            'signature_analysis': {
                'emails_with_signatures': int(has_signature.sum()),
                'signature_rate': round(has_signature.mean() * 100, 1)
            },
            'word_count_stats': {
                'average_words': round(df['word_count'].mean(), 1),
                'median_words': round(df['word_count'].median(), 1)
            }
        }

    def _analyze_subjects(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze email subject patterns"""
        subjects = df['subject'].astype(str)

        # Subject length analysis
        subject_lengths = subjects.str.len()

        # Common prefixes
        prefix_pattern = re.compile(r'^(Re:|Fwd:|FW:|RE:)', re.IGNORECASE)
        has_prefix = subjects.str.contains(prefix_pattern)

        # Most common subjects
        subject_counts = subjects.value_counts().head(10)

        return {
            'length_stats': {
                'average_length': round(subject_lengths.mean(), 1),
                'median_length': round(subject_lengths.median(), 1),
                'max_length': int(subject_lengths.max())
            },
            'prefix_analysis': {
                'emails_with_prefixes': int(has_prefix.sum()),
                'prefix_rate': round(has_prefix.mean() * 100, 1)
            },
            'most_common_subjects': subject_counts.to_dict(),
            'subject_diversity': len(subjects.unique()) / len(subjects)
        }

    def _analyze_language_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Basic language pattern analysis"""
        content_series = df['plain_text_content'].astype(str)

        # Simple language indicators
        english_indicators = ['the', 'and', 'you', 'your', 'this', 'that', 'with', 'have']

        english_score = content_series.apply(
            lambda x: sum(1 for word in english_indicators if word.lower() in x.lower()) / len(english_indicators)
        )

        return {
            'english_content_estimate': round(english_score.mean() * 100, 1),
            'multilingual_detection': 'Basic analysis - English indicators only'
        }

    def generate_insights(self, analysis_results: dict[str, Any]) -> dict[str, Any]:
        """Generate actionable insights from analysis results"""
        self.logger.info("Generating actionable insights")

        insights = {
            'volume_insights': self._generate_volume_insights(analysis_results),
            'category_insights': self._generate_category_insights(analysis_results),
            'sender_insights': self._generate_sender_insights(analysis_results),
            'automation_insights': self._generate_automation_insights(analysis_results),
            'content_insights': self._generate_content_insights(analysis_results),
            'recommendations': self._generate_recommendations(analysis_results)
        }

        return insights

    def _generate_volume_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about email volume patterns"""
        insights = []
        temporal = results.get('temporal_analysis', {})
        volume_patterns = temporal.get('volume_patterns', {})

        daily_avg = volume_patterns.get('daily_average', 0)
        if daily_avg > 50:
            insights.append(f"High email volume detected: {daily_avg:.1f} emails/day average")
        elif daily_avg < 5:
            insights.append(f"Low email volume: {daily_avg:.1f} emails/day average")

        peak_volume = volume_patterns.get('peak_day', {}).get('volume', 0)
        if peak_volume > daily_avg * 3:
            insights.append(f"Significant volume spike detected: {peak_volume} emails on peak day")

        return insights

    def _generate_category_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about email categories"""
        insights = []
        classification = results.get('classification_summary', {})

        for category, stats in classification.items():
            if isinstance(stats, dict) and 'count' in stats:
                percentage = stats.get('percentage', 0)
                if percentage > 30:
                    insights.append(f"High {category} email volume: {percentage:.1f}% of total")

        return insights

    def _generate_sender_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about sender patterns"""
        insights = []
        sender_analysis = results.get('sender_analysis', {})

        # Top sender concentration
        diversity = sender_analysis.get('sender_diversity', {})
        top_10_concentration = diversity.get('top_10_concentration', 0)

        if top_10_concentration > 0.5:
            insights.append(f"High sender concentration: Top 10 senders account for {top_10_concentration*100:.1f}% of emails")

        # Automation rate
        automation = sender_analysis.get('automation_analysis', {})
        automation_rate = automation.get('automation_rate', 0)

        if automation_rate > 70:
            insights.append(f"High automation rate: {automation_rate:.1f}% of emails are automated")

        return insights

    def _generate_automation_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about automation patterns"""
        insights = []
        sender_analysis = results.get('sender_analysis', {})
        automation = sender_analysis.get('automation_analysis', {})

        automated_count = automation.get('automated_emails', 0)
        total_emails = results.get('metadata', {}).get('total_emails', 1)

        if automated_count > total_emails * 0.6:
            insights.append("High potential for email filtering - majority of emails are automated")

        return insights

    def _generate_content_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about content patterns"""
        insights = []
        content_analysis = results.get('content_analysis', {})
        length_stats = content_analysis.get('length_statistics', {}).get('basic_stats', {})

        avg_length = length_stats.get('mean', 0)
        if avg_length > 5000:
            insights.append(f"Long email content detected: {avg_length:.0f} average characters")
            insights.append("Consider implementing email summarization tools")

        return insights

    def _generate_recommendations(self, results: dict[str, Any]) -> list[dict[str, str]]:
        """Generate prioritized recommendations"""
        recommendations = []

        # Extract key metrics for recommendation logic
        sender_analysis = results.get('sender_analysis', {})
        automation_rate = sender_analysis.get('automation_analysis', {}).get('automation_rate', 0)

        classification = results.get('classification_summary', {})
        financial_pct = classification.get('Financial', {}).get('percentage', 0)
        notification_pct = classification.get('Notifications', {}).get('percentage', 0)

        # High priority recommendations
        if financial_pct > 25:
            recommendations.append({
                'priority': 'High',
                'category': 'Financial Processing',
                'recommendation': f'Set up dedicated financial email processing - {financial_pct:.1f}% of emails are financial',
                'impact': 'High automation potential'
            })

        if notification_pct > 20:
            recommendations.append({
                'priority': 'High',
                'category': 'Notification Management',
                'recommendation': f'Audit notification subscriptions - {notification_pct:.1f}% are notifications',
                'impact': 'Reduce email noise'
            })

        if automation_rate > 60:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Automation',
                'recommendation': f'Implement advanced filtering - {automation_rate:.1f}% of emails are automated',
                'impact': 'Improved inbox management'
            })

        return recommendations

def main():
    """Main execution function for daily email analysis"""
    parser = argparse.ArgumentParser(description='Daily Email Analysis')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--date', help='Specific date to analyze (YYYY-MM-DD)')
    parser.add_argument('--yesterday', action='store_true', help='Analyze yesterday\'s emails')
    parser.add_argument('--incremental', action='store_true', help='Incremental analysis mode')
    parser.add_argument('--days', type=int, default=1, help='Number of days to analyze')
    parser.add_argument('--input', required=True, help='Input parquet file path')
    parser.add_argument('--output', default='analysis_results.json', help='Output file path')

    args = parser.parse_args()

    # Load configuration
    try:
        with open(args.config) as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {
            'quality_thresholds': {'min_completeness': 95},
            'log_file': 'logs/email_analysis.log'
        }

    # Initialize analysis engine
    engine = EmailAnalysisEngine(config)

    try:
        # Load data
        engine.logger.info(f"Loading data from {args.input}")
        df = pd.read_parquet(args.input)

        # Date filtering if specified
        if args.date or args.yesterday:
            df['date_received'] = pd.to_datetime(df['date_received'])

            if args.yesterday:
                target_date = datetime.now().date() - timedelta(days=1)
            else:
                target_date = datetime.strptime(args.date, '%Y-%m-%d').date()

            df = df[df['date_received'].dt.date == target_date]
            engine.logger.info(f"Filtered to {len(df)} emails for date {target_date}")

        if df.empty:
            engine.logger.warning("No data found for analysis")
            return

        # Execute analysis pipeline
        start_time = datetime.now()

        # Step 1: Quality Assessment
        quality_metrics = engine.analyze_data_quality(df)

        if not quality_metrics['quality_passed']:
            engine.logger.error(f"Quality issues detected: {quality_metrics['quality_issues']}")
            return

        # Step 2: Classification
        df_classified = engine.classify_emails(df)

        # Step 3: Analysis
        temporal_analysis = engine.analyze_temporal_patterns(df_classified)
        sender_analysis = engine.analyze_senders(df_classified)
        content_analysis = engine.analyze_content(df_classified)

        # Step 4: Generate Summary
        classification_summary = df_classified['category'].value_counts().to_dict()
        classification_percentages = (df_classified['category'].value_counts() / len(df_classified) * 100).to_dict()

        # Combine results
        analysis_results = {
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_emails': len(df_classified),
                'analysis_duration_seconds': (datetime.now() - start_time).total_seconds(),
                'data_source': args.input,
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

        # Step 5: Generate Insights
        insights = engine.generate_insights(analysis_results)
        analysis_results['insights'] = insights

        # Step 6: Save Results
        with open(args.output, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)

        engine.logger.info(f"Analysis complete. Results saved to {args.output}")

        # Print summary
        print("\n📊 Email Analysis Summary")
        print("=" * 40)
        print(f"Total emails analyzed: {len(df_classified):,}")
        print(f"Analysis duration: {(datetime.now() - start_time).total_seconds():.2f} seconds")
        print(f"Data quality: {quality_metrics['completeness']['overall_completeness']:.1f}%")

        print("\n📈 Category Distribution:")
        for category, stats in analysis_results['classification_summary'].items():
            print(f"  {category}: {stats['count']} ({stats['percentage']}%)")

        print("\n🎯 Key Insights:")
        for insight in insights.get('recommendations', [])[:3]:
            print(f"  • {insight['recommendation']}")

    except Exception as e:
        engine.logger.error(f"Analysis failed: {e!s}")
        sys.exit(1)

if __name__ == "__main__":
    main()
