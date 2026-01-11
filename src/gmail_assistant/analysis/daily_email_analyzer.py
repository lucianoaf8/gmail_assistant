#!/usr/bin/env python3
"""
Daily Email Analysis Engine - Production Implementation
Comprehensive email analysis following the documented methodology with hierarchical classification,
temporal analysis, sender profiling, and actionable insights generation.

This implements the core analysis engine designed for daily incremental processing of Gmail data
with multi-dimensional analysis including categorization, quality assessment, and pattern detection.
"""

import json
import logging
import re
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)


class DataQualityAssessment:
    """Comprehensive data quality assessment with validation gates"""

    def __init__(self, quality_thresholds: dict[str, float]):
        self.thresholds = quality_thresholds

    def assess_quality(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Multi-dimensional data quality assessment
        
        Args:
            df: DataFrame with email data
            
        Returns:
            Dict with quality metrics and validation results
        """
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
                    col: int(df[col].isnull().sum())
                    for col in df.columns if df[col].isnull().sum() > 0
                }
            },
            'consistency': {
                'duplicate_gmail_ids': int(df.get('gmail_id', pd.Series()).duplicated().sum()),
                'unique_gmail_ids': len(df.get('gmail_id', pd.Series()).unique()),
                'total_records': len(df),
                'id_uniqueness_rate': len(df.get('gmail_id', pd.Series()).unique()) / len(df) * 100 if len(df) > 0 else 0
            },
            'validity': self._assess_validity(df)
        }

        # Quality gate validation
        quality_issues = self._validate_quality_gates(quality_metrics)
        quality_metrics['quality_issues'] = quality_issues
        quality_metrics['quality_passed'] = len(quality_issues) == 0

        return quality_metrics

    def _assess_validity(self, df: pd.DataFrame) -> dict[str, Any]:
        """Assess data validity including date and email format validation"""
        validity_metrics = {}

        # Date validation
        if 'date_received' in df.columns:
            valid_dates = df['date_received'].notna().sum()
            validity_metrics.update({
                'valid_dates': int(valid_dates),
                'date_range': {
                    'min_date': df['date_received'].min().isoformat() if valid_dates > 0 else None,
                    'max_date': df['date_received'].max().isoformat() if valid_dates > 0 else None,
                    'span_days': (df['date_received'].max() - df['date_received'].min()).days if valid_dates > 0 else 0
                }
            })

        # Email format validation
        if 'sender' in df.columns:
            email_validity = self._validate_email_formats(df['sender'])
            validity_metrics['email_format_validity'] = email_validity

        return validity_metrics

    def _validate_email_formats(self, email_series: pd.Series) -> dict[str, Any]:
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

        total = valid_emails + invalid_emails
        return {
            'valid_emails': valid_emails,
            'invalid_emails': invalid_emails,
            'validity_rate': valid_emails / total * 100 if total > 0 else 0
        }

    def _validate_quality_gates(self, quality_metrics: dict[str, Any]) -> list[str]:
        """Validate quality gates and return list of issues"""
        issues = []

        # Completeness check
        overall_completeness = quality_metrics['completeness']['overall_completeness']
        if overall_completeness < self.thresholds.get('min_completeness', 95):
            issues.append(f'Low data completeness: {overall_completeness:.1f}%')

        # Duplicate check
        duplicates = quality_metrics['consistency']['duplicate_gmail_ids']
        if duplicates > 0:
            issues.append(f'Duplicate gmail_ids detected: {duplicates}')

        # Field-level null rate check
        for field, completeness in quality_metrics['completeness']['field_completeness'].items():
            null_rate = 100 - completeness
            if null_rate > self.thresholds.get('max_null_rate', 5):
                issues.append(f'High null rate in {field}: {null_rate:.1f}%')

        return issues


class HierarchicalClassifier:
    """Hierarchical email classification engine with confidence scoring"""

    def __init__(self, classification_rules: dict[str, dict]):
        self.rules = classification_rules
        self.custom_categories = {}

    def add_custom_categories(self, custom_categories: dict[str, dict]):
        """Add custom categories to the classification engine"""
        self.custom_categories = custom_categories

    def classify_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply hierarchical email classification with confidence scoring
        
        Args:
            df: DataFrame with email data
            
        Returns:
            DataFrame with added classification columns
        """
        # Create a copy to avoid modifying original data
        df_classified = df.copy()

        # Apply classification
        df_classified['category'] = df_classified.apply(self._categorize_email, axis=1)
        df_classified['classification_confidence'] = df_classified.apply(self._calculate_confidence, axis=1)
        df_classified['is_automated'] = df_classified.apply(self._detect_automation, axis=1)

        # Calculate derived metrics
        df_classified['content_length'] = df_classified.get('plain_text_content', pd.Series()).str.len().fillna(0)
        df_classified['word_count'] = df_classified.get('plain_text_content', pd.Series()).str.split().str.len().fillna(0)

        return df_classified

    def _categorize_email(self, row) -> str:
        """Categorize single email using hierarchical rules"""
        subject = str(row.get('subject', '')).lower()
        sender = str(row.get('sender', '')).lower()
        content = str(row.get('plain_text_content', '')).lower()

        # Combine text for analysis
        combined_text = f"{subject} {content}"

        # Combine base rules with custom categories
        all_rules = {**self.rules, **self.custom_categories}

        # Apply classification rules in priority order
        for category, rules in sorted(all_rules.items(), key=lambda x: x[1].get('priority', 10)):
            # Check keywords
            keywords = rules.get('keywords', [])
            if any(keyword in combined_text for keyword in keywords):
                return category

            # Check sender patterns
            sender_patterns = rules.get('sender_patterns', [])
            for pattern in sender_patterns:
                if re.search(pattern.lower(), sender):
                    return category

        return 'Other'

    def _calculate_confidence(self, row) -> float:
        """Calculate confidence score for classification"""
        subject = str(row.get('subject', '')).lower()
        sender = str(row.get('sender', '')).lower()
        content = str(row.get('plain_text_content', '')).lower()
        category = row.get('category', 'Other')

        if category == 'Other':
            return 0.5

        combined_text = f"{subject} {content}"
        all_rules = {**self.rules, **self.custom_categories}
        rules = all_rules.get(category, {})

        # Count matching patterns
        keywords = rules.get('keywords', [])
        keyword_matches = sum(1 for keyword in keywords if keyword in combined_text)

        sender_patterns = rules.get('sender_patterns', [])
        sender_matches = sum(1 for pattern in sender_patterns if re.search(pattern.lower(), sender))

        total_patterns = len(keywords) + len(sender_patterns)
        if total_patterns == 0:
            return 0.5

        match_ratio = (keyword_matches + sender_matches) / total_patterns

        # Base confidence + match bonus, capped at category threshold
        confidence = 0.7 + (0.3 * min(match_ratio, 1.0))
        threshold = rules.get('confidence_threshold', 0.8)

        return round(min(confidence, threshold), 3)

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
        automated_domains = ['amazonaws.com', 'sendgrid.', 'mailgun.', 'mailchimp.', 'beehiiv.com']
        if any(domain in sender for domain in automated_domains):
            automation_score += 1

        return automation_score >= 1.0


class TemporalAnalyzer:
    """Temporal analysis engine with peak detection and trend analysis"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.peak_threshold = config.get('peak_detection_threshold', 2.0)
        self.rolling_window = config.get('rolling_window_days', 7)

    def analyze_temporal_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Comprehensive temporal analysis with peak detection
        
        Args:
            df: DataFrame with classified email data
            
        Returns:
            Dict with temporal analysis results
        """
        if 'date_received' not in df.columns:
            return {'error': 'date_received column not found'}

        df = df.copy()
        df['date_received'] = pd.to_datetime(df['date_received'])

        # Extract time components
        df['hour'] = df['date_received'].dt.hour
        df['day_of_week'] = df['date_received'].dt.dayofweek
        df['day_name'] = df['date_received'].dt.day_name()
        df['date'] = df['date_received'].dt.date

        # Daily volume analysis
        daily_volume = df.groupby('date').size()

        temporal_metrics = {
            'date_range': {
                'start_date': df['date_received'].min().isoformat(),
                'end_date': df['date_received'].max().isoformat(),
                'span_days': (df['date_received'].max() - df['date_received'].min()).days + 1,
                'total_emails': len(df)
            },
            'volume_patterns': self._analyze_volume_patterns(daily_volume),
            'time_distribution': {
                'hourly_distribution': df['hour'].value_counts().sort_index().to_dict(),
                'daily_distribution': {
                    'by_number': df['day_of_week'].value_counts().sort_index().to_dict(),
                    'by_name': df['day_name'].value_counts().to_dict()
                }
            },
            'peak_analysis': self._detect_peaks(daily_volume),
            'category_temporal_patterns': self._analyze_category_patterns(df)
        }

        return temporal_metrics

    def _analyze_volume_patterns(self, daily_volume: pd.Series) -> dict[str, Any]:
        """Analyze email volume patterns and statistics"""
        if len(daily_volume) == 0:
            return {}

        return {
            'daily_average': round(daily_volume.mean(), 2),
            'daily_median': round(daily_volume.median(), 2),
            'daily_std': round(daily_volume.std(), 2),
            'peak_day': {
                'date': daily_volume.idxmax().isoformat(),
                'volume': int(daily_volume.max())
            },
            'min_day': {
                'date': daily_volume.idxmin().isoformat(),
                'volume': int(daily_volume.min())
            },
            'volatility': round(daily_volume.std() / daily_volume.mean(), 3) if daily_volume.mean() > 0 else 0
        }

    def _detect_peaks(self, daily_volume: pd.Series) -> dict[str, Any]:
        """Statistical peak detection using rolling statistics"""
        if len(daily_volume) < self.rolling_window:
            return {'peaks_detected': 0, 'insufficient_data': True}

        # Calculate rolling statistics
        rolling_mean = daily_volume.rolling(window=self.rolling_window, center=True).mean()
        rolling_std = daily_volume.rolling(window=self.rolling_window, center=True).std()

        # Define threshold for peaks
        threshold = rolling_mean + (self.peak_threshold * rolling_std)

        # Identify peaks
        peaks = daily_volume[daily_volume > threshold].dropna()

        return {
            'peaks_detected': len(peaks),
            'peak_dates': [date.isoformat() for date in peaks.index],
            'peak_volumes': peaks.values.tolist(),
            'average_peak_size': round(peaks.mean(), 1) if len(peaks) > 0 else 0,
            'peak_frequency_percent': round(len(peaks) / len(daily_volume) * 100, 2)
        }

    def _analyze_category_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze temporal patterns by email category"""
        patterns = {}

        for category in df['category'].unique():
            category_emails = df[df['category'] == category]

            if len(category_emails) == 0:
                continue

            patterns[category] = {
                'peak_hours': category_emails['hour'].value_counts().head(3).to_dict(),
                'peak_days': category_emails['day_name'].value_counts().head(3).to_dict(),
                'average_per_day': round(len(category_emails) / df['date'].nunique(), 2),
                'temporal_concentration': self._calculate_temporal_concentration(category_emails)
            }

        return patterns

    def _calculate_temporal_concentration(self, emails_df: pd.DataFrame) -> float:
        """Calculate temporal concentration using Gini coefficient"""
        if len(emails_df) < 2:
            return 0.0

        daily_counts = emails_df.groupby('date').size().values
        if len(daily_counts) < 2:
            return 0.0

        daily_counts = np.sort(daily_counts)
        n = len(daily_counts)
        cumsum = np.cumsum(daily_counts)

        # Gini coefficient calculation
        gini = (2 * np.sum((np.arange(1, n + 1)) * daily_counts)) / (n * np.sum(daily_counts)) - (n + 1) / n

        return round(gini, 3)


class SenderAnalyzer:
    """Sender profiling and automation detection engine"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.top_senders_count = config.get('top_senders_count', 50)

    def analyze_senders(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Comprehensive sender analysis with automation detection
        
        Args:
            df: DataFrame with classified email data
            
        Returns:
            Dict with sender analysis results
        """
        if 'sender' not in df.columns:
            return {'error': 'sender column not found'}

        sender_analysis = {
            'sender_metrics': self._calculate_sender_metrics(df),
            'top_senders': self._analyze_top_senders(df),
            'automation_analysis': self._analyze_automation_patterns(df),
            'domain_analysis': self._analyze_domains(df),
            'sender_diversity': self._calculate_sender_diversity(df)
        }

        return sender_analysis

    def _calculate_sender_metrics(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculate basic sender metrics"""
        return {
            'total_unique_senders': df['sender'].nunique(),
            'total_emails': len(df),
            'average_emails_per_sender': round(len(df) / df['sender'].nunique(), 2) if df['sender'].nunique() > 0 else 0
        }

    def _analyze_top_senders(self, df: pd.DataFrame) -> dict[str, Any]:
        """Detailed analysis of top email senders"""
        sender_counts = df['sender'].value_counts().head(self.top_senders_count)

        top_senders = {}
        for sender, count in sender_counts.items():
            sender_emails = df[df['sender'] == sender]

            # Calculate date range safely
            date_range = {}
            if 'date_received' in df.columns and len(sender_emails) > 0:
                dates = pd.to_datetime(sender_emails['date_received']).dropna()
                if len(dates) > 0:
                    unique_dates = dates.dt.date.nunique()
                    date_range = {
                        'first': dates.min().isoformat(),
                        'last': dates.max().isoformat(),
                        'sending_frequency': round(count / max(unique_dates, 1), 2)
                    }

            top_senders[sender] = {
                'email_count': int(count),
                'percentage': round(count / len(df) * 100, 2),
                'categories': sender_emails.get('category', pd.Series()).value_counts().to_dict(),
                'is_automated': bool(sender_emails.get('is_automated', pd.Series(dtype=bool)).iloc[0]) if len(sender_emails) > 0 and not sender_emails.get('is_automated', pd.Series(dtype=bool)).empty else False,
                'avg_content_length': int(sender_emails.get('content_length', pd.Series([0])).fillna(0).mean()) if len(sender_emails) > 0 else 0,
                'date_range': date_range
            }

        return top_senders

    def _analyze_automation_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze automation patterns in email data"""
        automated_series = df.get('is_automated', pd.Series(dtype=bool))
        automated_count = automated_series.sum()
        total_count = len(df)

        automation_analysis = {
            'automation_rate': round(automated_count / total_count * 100, 2) if total_count > 0 else 0,
            'automated_emails': int(automated_count),
            'personal_emails': int(total_count - automated_count)
        }

        # Top automated senders
        if 'sender' in df.columns:
            automated_senders = df[automated_series == True]['sender'].value_counts().head(10)
            automation_analysis['top_automated_senders'] = automated_senders.to_dict()

        # Automation by category
        if 'category' in df.columns:
            category_automation = df.groupby('category')['is_automated'].agg(['count', 'sum', 'mean']).round(3)
            automation_analysis['automation_by_category'] = category_automation.to_dict()

        return automation_analysis

    def _analyze_domains(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze sender domains and patterns"""
        # Extract domains from sender emails
        df = df.copy()
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

        if len(sender_counts) == 0:
            return {
                'shannon_diversity': 0.0,
                'simpson_diversity': 0.0,
                'top_10_concentration': 0.0,
                'effective_senders': 0.0
            }

        # Shannon diversity index
        proportions = sender_counts / sender_counts.sum()
        shannon_diversity = -np.sum(proportions * np.log(proportions + 1e-10))  # Add small epsilon to avoid log(0)

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
        if len(domain_counts) == 0:
            return 0.0

        proportions = domain_counts / domain_counts.sum()
        return round(-np.sum(proportions * np.log(proportions + 1e-10)), 3)

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


class ContentAnalyzer:
    """Content analytics engine with pattern recognition"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.length_buckets = config.get('length_buckets', [0, 500, 2000, 5000, 10000, 20000])
        self.bucket_labels = config.get('bucket_labels',
            ['Very Short', 'Short', 'Medium', 'Long', 'Very Long', 'Extremely Long'])

    def analyze_content(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Comprehensive content analysis with pattern recognition
        
        Args:
            df: DataFrame with classified email data
            
        Returns:
            Dict with content analysis results
        """
        content_metrics = {
            'length_statistics': self._analyze_content_length(df),
            'content_patterns': self._analyze_content_patterns(df),
            'subject_analysis': self._analyze_subjects(df),
            'language_analysis': self._analyze_language_patterns(df)
        }

        return content_metrics

    def _analyze_content_length(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze email content length patterns"""
        if 'content_length' not in df.columns:
            return {'error': 'content_length column not found'}

        lengths = df['content_length']

        # Create length buckets - ensure bins and labels match
        bins = self.length_buckets + [float('inf')]
        labels = self.bucket_labels

        # Ensure we have the right number of labels (one fewer than bins)
        if len(labels) != len(bins) - 1:
            labels = labels[:len(bins)-1]

        length_buckets = pd.cut(
            lengths,
            bins=bins,
            labels=labels,
            include_lowest=True
        )

        length_stats = {
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
            'length_distribution': length_buckets.value_counts().to_dict()
        }

        # Category-specific length stats
        if 'category' in df.columns:
            category_stats = df.groupby('category')['content_length'].agg(['mean', 'median', 'std']).round(1)
            length_stats['category_length_stats'] = category_stats.to_dict()

        return length_stats

    def _analyze_content_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze patterns in email content"""
        if 'plain_text_content' not in df.columns:
            return {'error': 'plain_text_content column not found'}

        content_series = df['plain_text_content'].astype(str)

        # URL analysis
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls_per_email = content_series.apply(lambda x: len(url_pattern.findall(x)))

        # Email signature detection
        signature_indicators = ['best regards', 'sincerely', 'thanks', 'cheers', 'signature']
        has_signature = content_series.str.lower().str.contains('|'.join(signature_indicators), na=False)

        # Word count analysis
        word_counts = df.get('word_count', pd.Series()).fillna(0)

        return {
            'url_analysis': {
                'emails_with_urls': int(urls_per_email[urls_per_email > 0].count()),
                'average_urls_per_email': round(urls_per_email.mean(), 2),
                'max_urls_in_email': int(urls_per_email.max()) if len(urls_per_email) > 0 else 0
            },
            'signature_analysis': {
                'emails_with_signatures': int(has_signature.sum()),
                'signature_rate': round(has_signature.mean() * 100, 1)
            },
            'word_count_stats': {
                'average_words': round(word_counts.mean(), 1),
                'median_words': round(word_counts.median(), 1),
                'total_words': int(word_counts.sum())
            }
        }

    def _analyze_subjects(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze email subject patterns"""
        if 'subject' not in df.columns:
            return {'error': 'subject column not found'}

        subjects = df['subject'].astype(str)

        # Subject length analysis
        subject_lengths = subjects.str.len()

        # Common prefixes
        prefix_pattern = re.compile(r'^(Re:|Fwd:|FW:|RE:)', re.IGNORECASE)
        has_prefix = subjects.str.contains(prefix_pattern, na=False)

        # Most common subjects (top 10)
        subject_counts = subjects.value_counts().head(10)

        return {
            'length_stats': {
                'average_length': round(subject_lengths.mean(), 1),
                'median_length': round(subject_lengths.median(), 1),
                'max_length': int(subject_lengths.max()) if len(subject_lengths) > 0 else 0
            },
            'prefix_analysis': {
                'emails_with_prefixes': int(has_prefix.sum()),
                'prefix_rate': round(has_prefix.mean() * 100, 1)
            },
            'most_common_subjects': subject_counts.to_dict(),
            'subject_diversity': round(len(subjects.unique()) / len(subjects), 3) if len(subjects) > 0 else 0
        }

    def _analyze_language_patterns(self, df: pd.DataFrame) -> dict[str, Any]:
        """Basic language pattern analysis"""
        if 'plain_text_content' not in df.columns:
            return {'error': 'plain_text_content column not found'}

        content_series = df['plain_text_content'].astype(str)

        # Simple English indicators
        english_indicators = ['the', 'and', 'you', 'your', 'this', 'that', 'with', 'have']

        english_score = content_series.apply(
            lambda x: sum(1 for word in english_indicators if word.lower() in x.lower()) / len(english_indicators)
        )

        return {
            'english_content_estimate': round(english_score.mean() * 100, 1),
            'multilingual_detection': 'Basic analysis - English indicators only',
            'content_language_score': round(english_score.mean(), 3)
        }


class InsightsGenerator:
    """Actionable insights generation engine with prioritized recommendations"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.alert_thresholds = config.get('alert_thresholds', {})

    def generate_insights(self, analysis_results: dict[str, Any]) -> dict[str, Any]:
        """
        Generate actionable insights from comprehensive analysis results
        
        Args:
            analysis_results: Complete analysis results from all engines
            
        Returns:
            Dict with categorized insights and recommendations
        """
        insights = {
            'volume_insights': self._generate_volume_insights(analysis_results),
            'category_insights': self._generate_category_insights(analysis_results),
            'sender_insights': self._generate_sender_insights(analysis_results),
            'automation_insights': self._generate_automation_insights(analysis_results),
            'content_insights': self._generate_content_insights(analysis_results),
            'quality_insights': self._generate_quality_insights(analysis_results),
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
            insights.append(f"High email volume: {daily_avg:.1f} emails/day average - consider automation")
        elif daily_avg < 5:
            insights.append(f"Low email volume: {daily_avg:.1f} emails/day - focused processing recommended")

        # Peak analysis
        peak_analysis = temporal.get('peak_analysis', {})
        peaks_detected = peak_analysis.get('peaks_detected', 0)
        if peaks_detected > 0:
            peak_freq = peak_analysis.get('peak_frequency_percent', 0)
            insights.append(f"Volume spikes detected: {peaks_detected} peaks ({peak_freq:.1f}% of days)")

        # Volatility analysis
        volatility = volume_patterns.get('volatility', 0)
        if volatility > 1.0:
            insights.append(f"High volume volatility: {volatility:.2f} - inconsistent email patterns")

        return insights

    def _generate_category_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about email category distribution"""
        insights = []
        classification = results.get('classification_summary', {})

        for category, stats in classification.items():
            if isinstance(stats, dict) and 'percentage' in stats:
                percentage = stats.get('percentage', 0)
                count = stats.get('count', 0)

                if percentage > 30:
                    insights.append(f"High {category} volume: {percentage:.1f}% ({count} emails) - automation opportunity")
                elif percentage > 20:
                    insights.append(f"Significant {category} category: {percentage:.1f}% - review for optimization")

        return insights

    def _generate_sender_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about sender patterns"""
        insights = []
        sender_analysis = results.get('sender_analysis', {})

        # Sender concentration analysis
        diversity = sender_analysis.get('sender_diversity', {})
        top_10_concentration = diversity.get('top_10_concentration', 0)

        if top_10_concentration > 0.6:
            insights.append(f"High sender concentration: Top 10 senders = {top_10_concentration*100:.1f}% of emails")

        # Domain diversity
        domain_analysis = sender_analysis.get('domain_analysis', {})
        domain_types = domain_analysis.get('corporate_vs_service', {})
        service_emails = domain_types.get('service', 0)
        total_emails = results.get('metadata', {}).get('total_emails', 1)

        if service_emails / total_emails > 0.5:
            service_pct = (service_emails / total_emails) * 100
            insights.append(f"Service-heavy inbox: {service_pct:.1f}% from service domains")

        return insights

    def _generate_automation_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about automation patterns"""
        insights = []
        sender_analysis = results.get('sender_analysis', {})
        automation = sender_analysis.get('automation_analysis', {})

        automation_rate = automation.get('automation_rate', 0)

        if automation_rate > 70:
            insights.append(f"High automation potential: {automation_rate:.1f}% automated emails")
        elif automation_rate > 50:
            insights.append(f"Moderate automation: {automation_rate:.1f}% automated - filtering opportunities")

        # Top automated senders analysis
        top_automated = automation.get('top_automated_senders', {})
        if top_automated:
            top_sender = max(top_automated, key=top_automated.get)
            count = top_automated[top_sender]
            insights.append(f"Top automated sender: {top_sender} ({count} emails)")

        return insights

    def _generate_content_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about content patterns"""
        insights = []
        content_analysis = results.get('content_analysis', {})
        length_stats = content_analysis.get('length_statistics', {}).get('basic_stats', {})

        avg_length = length_stats.get('mean', 0)
        if avg_length > 10000:
            insights.append(f"Very long emails: {avg_length:.0f} avg characters - summarization recommended")
        elif avg_length > 5000:
            insights.append(f"Long email content: {avg_length:.0f} avg characters - consider preprocessing")

        # URL analysis
        patterns = content_analysis.get('content_patterns', {})
        url_analysis = patterns.get('url_analysis', {})
        emails_with_urls = url_analysis.get('emails_with_urls', 0)
        total_emails = results.get('metadata', {}).get('total_emails', 1)

        if emails_with_urls / total_emails > 0.8:
            url_pct = (emails_with_urls / total_emails) * 100
            insights.append(f"URL-heavy content: {url_pct:.1f}% contain links - potential marketing/news")

        return insights

    def _generate_quality_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate insights about data quality"""
        insights = []
        quality_metrics = results.get('quality_metrics', {})

        completeness = quality_metrics.get('completeness', {})
        overall_completeness = completeness.get('overall_completeness', 100)

        if overall_completeness < 98:
            insights.append(f"Data quality concern: {overall_completeness:.1f}% completeness")

        # Check for quality issues
        quality_issues = quality_metrics.get('quality_issues', [])
        if quality_issues:
            insights.append(f"Quality issues detected: {len(quality_issues)} problems found")

        return insights

    def _generate_recommendations(self, results: dict[str, Any]) -> list[dict[str, str]]:
        """Generate prioritized actionable recommendations"""
        recommendations = []

        # Extract key metrics for recommendation logic
        sender_analysis = results.get('sender_analysis', {})
        automation_rate = sender_analysis.get('automation_analysis', {}).get('automation_rate', 0)

        classification = results.get('classification_summary', {})
        temporal = results.get('temporal_analysis', {})
        content = results.get('content_analysis', {})

        # High priority recommendations

        # Financial email processing
        financial_pct = classification.get('Financial', {}).get('percentage', 0)
        if financial_pct > 25:
            recommendations.append({
                'priority': 'High',
                'category': 'Financial Processing',
                'recommendation': f'Set up dedicated financial email processing - {financial_pct:.1f}% of emails are financial',
                'impact': 'High automation ROI potential',
                'action': 'Create financial email filters and automated processing rules'
            })

        # Notification management
        notification_pct = classification.get('Notifications', {}).get('percentage', 0)
        if notification_pct > 20:
            recommendations.append({
                'priority': 'High',
                'category': 'Notification Management',
                'recommendation': f'Audit notification subscriptions - {notification_pct:.1f}% are notifications',
                'impact': 'Reduce email noise and improve focus',
                'action': 'Review and unsubscribe from unnecessary notifications'
            })

        # Automation opportunities
        if automation_rate > 60:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Email Automation',
                'recommendation': f'Implement advanced filtering - {automation_rate:.1f}% of emails are automated',
                'impact': 'Improved inbox management efficiency',
                'action': 'Set up rules for automated email handling'
            })

        # Content optimization
        avg_length = content.get('length_statistics', {}).get('basic_stats', {}).get('mean', 0)
        if avg_length > 5000:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Content Processing',
                'recommendation': f'Consider email summarization - {avg_length:.0f} avg characters',
                'impact': 'Faster email processing and comprehension',
                'action': 'Implement automated email summarization tools'
            })

        # Volume management
        daily_avg = temporal.get('volume_patterns', {}).get('daily_average', 0)
        if daily_avg > 100:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Volume Management',
                'recommendation': f'High email volume detected - {daily_avg:.1f} emails/day',
                'impact': 'Prevent email overload and missed important messages',
                'action': 'Implement batching and priority-based processing'
            })

        # Sender concentration
        top_10_conc = sender_analysis.get('sender_diversity', {}).get('top_10_concentration', 0)
        if top_10_conc > 0.5:
            recommendations.append({
                'priority': 'Low',
                'category': 'Sender Management',
                'recommendation': f'High sender concentration - top 10 senders = {top_10_conc*100:.1f}%',
                'impact': 'Opportunity for targeted sender-specific rules',
                'action': 'Create custom filters for high-volume senders'
            })

        return recommendations


class DailyEmailAnalyzer:
    """
    Main orchestration class for comprehensive daily email analysis
    
    This class coordinates all analysis engines to provide a complete
    daily email analysis following the documented methodology.
    """

    def __init__(self, config_path: str):
        """
        Initialize the email analyzer with configuration
        
        Args:
            config_path: Path to configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Initialize analysis engines
        self.quality_assessor = DataQualityAssessment(self.config.get('quality_thresholds', {}))
        self.classifier = HierarchicalClassifier(self.config.get('classification_rules', {}))
        self.temporal_analyzer = TemporalAnalyzer(self.config.get('temporal_analysis', {}))
        self.sender_analyzer = SenderAnalyzer(self.config.get('sender_analysis', {}))
        self.content_analyzer = ContentAnalyzer(self.config.get('content_analysis', {}))
        self.insights_generator = InsightsGenerator(self.config)

        # Add custom categories if configured
        custom_categories = self.config.get('custom_categories', {})
        if custom_categories:
            self.classifier.add_custom_categories(custom_categories)

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration if file not found
            return {
                'quality_thresholds': {'min_completeness': 95},
                'classification_rules': {},
                'logging_config': {'log_level': 'INFO'}
            }

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for analysis pipeline"""
        logger = logging.getLogger('DailyEmailAnalyzer')

        log_config = self.config.get('logging_config', {})
        log_level = log_config.get('log_level', 'INFO')
        logger.setLevel(getattr(logging, log_level))

        # Create handlers if not already present
        if not logger.handlers:
            # File handler
            log_file = log_config.get('log_file', 'logs/daily_analysis.log')
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)

            # Console handler if enabled
            handlers = [file_handler]
            if log_config.get('console_output', True):
                console_handler = logging.StreamHandler()
                handlers.append(console_handler)

            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            for handler in handlers:
                handler.setFormatter(formatter)
                logger.addHandler(handler)

        return logger

    def analyze_emails(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Run comprehensive email analysis pipeline
        
        Args:
            df: DataFrame with email data
            
        Returns:
            Dict with complete analysis results
        """
        start_time = datetime.now()
        self.logger.info(f"Starting email analysis for {len(df)} emails")

        try:
            # Step 1: Data Quality Assessment
            self.logger.info("Step 1: Assessing data quality")
            quality_metrics = self.quality_assessor.assess_quality(df)

            if not quality_metrics['quality_passed']:
                self.logger.error(f"Quality assessment failed: {quality_metrics['quality_issues']}")
                return {
                    'error': 'Quality assessment failed',
                    'quality_metrics': quality_metrics,
                    'timestamp': datetime.now().isoformat()
                }

            # Step 2: Email Classification
            self.logger.info("Step 2: Classifying emails")
            df_classified = self.classifier.classify_emails(df)

            # Step 3: Generate classification summary
            classification_summary = self._generate_classification_summary(df_classified)

            # Step 4: Temporal Analysis
            self.logger.info("Step 3: Analyzing temporal patterns")
            temporal_analysis = self.temporal_analyzer.analyze_temporal_patterns(df_classified)

            # Step 5: Sender Analysis
            self.logger.info("Step 4: Analyzing sender patterns")
            sender_analysis = self.sender_analyzer.analyze_senders(df_classified)

            # Step 6: Content Analysis
            self.logger.info("Step 5: Analyzing content patterns")
            content_analysis = self.content_analyzer.analyze_content(df_classified)

            # Step 7: Compile results
            analysis_results = {
                'metadata': {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'total_emails': len(df_classified),
                    'analysis_duration_seconds': (datetime.now() - start_time).total_seconds(),
                    'configuration_version': self.config.get('analysis_config', {}).get('version', '1.0.0')
                },
                'quality_metrics': quality_metrics,
                'classification_summary': classification_summary,
                'temporal_analysis': temporal_analysis,
                'sender_analysis': sender_analysis,
                'content_analysis': content_analysis
            }

            # Step 8: Generate Insights
            self.logger.info("Step 6: Generating actionable insights")
            insights = self.insights_generator.generate_insights(analysis_results)
            analysis_results['insights'] = insights

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Analysis completed successfully in {duration:.2f} seconds")

            return analysis_results

        except Exception as e:
            self.logger.error(f"Analysis failed: {e!s}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'partial_results': locals().get('analysis_results', {})
            }

    def _generate_classification_summary(self, df: pd.DataFrame) -> dict[str, Any]:
        """Generate summary of email classification results"""
        if 'category' not in df.columns:
            return {}

        category_counts = df['category'].value_counts()
        category_percentages = (category_counts / len(df) * 100).round(2)

        classification_summary = {}
        for category, count in category_counts.items():
            classification_summary[category] = {
                'count': int(count),
                'percentage': float(category_percentages[category])
            }

        # Add confidence statistics
        if 'classification_confidence' in df.columns:
            avg_confidence = df.groupby('category')['classification_confidence'].mean().round(3)
            for category in classification_summary:
                if category in avg_confidence:
                    classification_summary[category]['average_confidence'] = float(avg_confidence[category])

        return classification_summary

    def analyze_date_range(self, df: pd.DataFrame, start_date: str, end_date: str) -> dict[str, Any]:
        """
        Analyze emails within a specific date range
        
        Args:
            df: DataFrame with email data
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dict with analysis results for the date range
        """
        if 'date_received' not in df.columns:
            return {'error': 'date_received column not found'}

        # Filter data by date range
        df_filtered = df.copy()
        df_filtered['date_received'] = pd.to_datetime(df_filtered['date_received'])

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        mask = (df_filtered['date_received'] >= start_dt) & (df_filtered['date_received'] <= end_dt)
        df_filtered = df_filtered[mask]

        if len(df_filtered) == 0:
            return {'error': f'No emails found in date range {start_date} to {end_date}'}

        self.logger.info(f"Analyzing {len(df_filtered)} emails from {start_date} to {end_date}")

        # Run analysis on filtered data
        results = self.analyze_emails(df_filtered)

        # Add date range info to metadata
        if 'metadata' in results:
            results['metadata']['date_range'] = {
                'start_date': start_date,
                'end_date': end_date,
                'emails_in_range': len(df_filtered),
                'total_available': len(df)
            }

        return results

    def generate_summary_report(self, analysis_results: dict[str, Any]) -> str:
        """
        Generate a human-readable summary report
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Formatted summary report as string
        """
        if 'error' in analysis_results:
            return f"Analysis Error: {analysis_results['error']}"

        metadata = analysis_results.get('metadata', {})
        classification = analysis_results.get('classification_summary', {})
        insights = analysis_results.get('insights', {})

        report_lines = [
            "EMAIL ANALYSIS SUMMARY",
            "=" * 50,
            f"Analysis Date: {metadata.get('analysis_timestamp', 'Unknown')[:19]}",
            f"Total Emails: {metadata.get('total_emails', 0):,}",
            f"Processing Time: {metadata.get('analysis_duration_seconds', 0):.2f} seconds",
            "",
            "CATEGORY DISTRIBUTION:",
        ]

        # Add category breakdown
        for category, stats in sorted(classification.items(),
                                    key=lambda x: x[1].get('percentage', 0), reverse=True):
            count = stats.get('count', 0)
            percentage = stats.get('percentage', 0)
            confidence = stats.get('average_confidence', 0)
            report_lines.append(f"  {category}: {count:,} emails ({percentage:.1f}%) [confidence: {confidence:.2f}]")

        # Add key insights
        recommendations = insights.get('recommendations', [])
        if recommendations:
            report_lines.extend([
                "",
                "KEY RECOMMENDATIONS:",
            ])

            for rec in recommendations[:5]:  # Top 5 recommendations
                priority = rec.get('priority', 'Medium')
                category = rec.get('category', 'General')
                recommendation = rec.get('recommendation', '')
                report_lines.append(f"  [{priority}] {category}: {recommendation}")

        # Add automation insights
        sender_analysis = analysis_results.get('sender_analysis', {})
        automation_rate = sender_analysis.get('automation_analysis', {}).get('automation_rate', 0)

        report_lines.extend([
            "",
            "AUTOMATION ANALYSIS:",
            f"  Automation Rate: {automation_rate:.1f}% of emails are automated",
            f"  Manual Processing: {100-automation_rate:.1f}% require human attention"
        ])

        return "\n".join(report_lines)


# Example usage and testing functions
def create_sample_data() -> pd.DataFrame:
    """Create sample email data for testing"""
    # Create lists with exactly 50 elements each
    subjects = [
        'Payment Receipt', 'Newsletter Update', 'Meeting Reminder',
        'Bill Statement', 'Social Notification', 'Work Assignment',
        'Bird ride receipt', 'Backup completed', 'AI Newsletter'
    ]
    senders = [
        'billing@company.com', 'newsletter@news.com', 'calendar@work.com',
        'statements@bank.com', 'notifications@social.com', 'team@workplace.com',
        'noreply@bird.co', 'no-reply@backupstatus.idrive.com', 'hello@mindstream.news'
    ]
    contents = [
        'Your payment has been processed successfully for $25.00.',
        'Here is your weekly newsletter with the latest AI updates.',
        'Reminder: You have a meeting scheduled for tomorrow at 2 PM.',
        'Your monthly statement is now available for review.',
        'You have new notifications on your social media account.',
        'New assignment has been added to your project dashboard.',
        'Thanks for riding with Bird! Your trip cost $3.50.',
        'Backup completed successfully. 15GB backed up to cloud.',
        'Latest AI news and trends in this week\'s edition.'
    ]

    sample_data = {
        'gmail_id': [f'id_{i:04d}' for i in range(50)],
        'date_received': [
            datetime.now() - timedelta(days=i//5, hours=i%24)
            for i in range(50)
        ],
        'subject': [subjects[i % len(subjects)] for i in range(50)],
        'sender': [senders[i % len(senders)] for i in range(50)],
        'plain_text_content': [contents[i % len(contents)] for i in range(50)]
    }

    return pd.DataFrame(sample_data)


if __name__ == "__main__":
    # Example usage
    print("Daily Email Analyzer - Production Implementation")
    print("=" * 50)

    # Create sample data for testing
    sample_df = create_sample_data()
    print(f"Created sample dataset with {len(sample_df)} emails")

    # Initialize analyzer with default config
    analyzer = DailyEmailAnalyzer('config/analysis/0922-1430_daily_analysis_config.json')

    # Run analysis
    results = analyzer.analyze_emails(sample_df)

    # Generate and print summary report
    summary = analyzer.generate_summary_report(results)
    print("\n" + summary)

    # Save detailed results
    output_file = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: {output_file}")
