#!/usr/bin/env python3
"""
Comprehensive Email Classification System

This script implements a multi-phase email classification system that categorizes
emails based on sender patterns, content analysis, subject line patterns, and
behavioral analysis. It adds classification columns to the database and provides
comprehensive reporting and analysis tools.

Phases:
1. Foundation Classification (sender patterns, Gmail labels, frequency)
2. Content Enhancement (subject patterns, keyword analysis)
3. Advanced Analytics (confidence scoring, temporal patterns)

Usage:
    python email_classifier.py --db emails.db [--phase 1|2|3|all] [--analyze] [--report]

Author: Gmail Fetcher System
Date: 2025-09-18
"""

import argparse
import json
import logging
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any


class EmailClassifier:
    """Comprehensive email classification system with multi-phase analysis."""

    def __init__(self, db_path: str):
        """Initialize the classifier with database connection."""
        self.db_path = db_path
        self.logger = self._setup_logging()

        # Classification categories
        self.primary_categories = [
            'Newsletter', 'Service_Notification', 'Support', 'Marketing',
            'Personal', 'Transactional', 'Educational', 'System'
        ]

        self.domain_categories = [
            'AI/Technology', 'Business/Productivity', 'Finance', 'Education',
            'Entertainment', 'Health/Fitness', 'Travel/Transportation',
            'Shopping/Retail', 'Social/Personal', 'Government/Legal', 'Other'
        ]

        self.priority_levels = ['High', 'Medium', 'Low']
        self.source_types = ['Human', 'Automated', 'Semi-automated']
        self.action_types = ['Reply_Needed', 'Read_Only', 'Archive', 'Delete']

        # Classification rules and patterns
        self._initialize_classification_rules()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        from pathlib import Path
        log_dir = Path('logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'email_classifier.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)

    def _initialize_classification_rules(self):
        """Initialize all classification rules and patterns."""

        # Sender pattern rules
        self.sender_patterns = {
            'Newsletter': [
                r'newsletter@', r'news@', r'hello@.*news', r'@mail\.', r'@newsletter\.',
                r'mindstream', r'theresanaiforthat', r'rundown', r'futureblueprint'
            ],
            'Service_Notification': [
                r'noreply@', r'no-reply@', r'notification@', r'alerts@', r'bird\.co',
                r'backupstatus', r'netdata', r'@service\.'
            ],
            'Support': [
                r'support@', r'help@', r'customer@', r'service@', r'care@'
            ],
            'Marketing': [
                r'marketing@', r'promo@', r'offers@', r'sales@', r'@promo\.',
                r'affirm-billing', r'@deals\.'
            ],
            'Transactional': [
                r'billing@', r'receipts@', r'orders@', r'payments@', r'account@'
            ],
            'Educational': [
                r'@edu', r'learning@', r'training@', r'courses@', r'estacio'
            ]
        }

        # Subject pattern rules
        self.subject_patterns = {
            'Support': [r'^Re:', r'\[.*Support.*\]', r'help', r'issue', r'problem'],
            'Transactional': [
                r'receipt', r'order', r'payment', r'invoice', r'billing',
                r'confirmation', r'your account'
            ],
            'Marketing': [
                r'sale', r'offer', r'discount', r'deal', r'promo', r'limited time',
                r'% off', r'free shipping'
            ],
            'Newsletter': [
                r'weekly', r'daily', r'roundup', r'digest', r'newsletter',
                r'update.*\d{4}', r'edition'
            ],
            'Service_Notification': [
                r'alert', r'notification', r'reminder', r'scheduled', r'backup',
                r'ride receipt', r'trip summary'
            ],
            'Personal': [r'^Re:', r'^Fwd:', r'meeting', r'lunch', r'call'],
            'System': [r'security', r'login', r'password', r'verify', r'activate']
        }

        # Content keyword rules for domain classification
        self.domain_keywords = {
            'AI/Technology': [
                'artificial intelligence', 'machine learning', 'chatgpt', 'gpt',
                'neural network', 'deep learning', 'ai', 'llm', 'algorithm',
                'tech', 'software', 'api', 'coding', 'programming', 'startup'
            ],
            'Finance': [
                'bank', 'credit', 'loan', 'investment', 'stock', 'crypto',
                'bitcoin', 'financial', 'money', 'payment', 'mastercard', 'visa'
            ],
            'Travel/Transportation': [
                'flight', 'hotel', 'travel', 'trip', 'vacation', 'ride',
                'uber', 'lyft', 'bird', 'scooter', 'transport'
            ],
            'Education': [
                'course', 'learning', 'study', 'university', 'college', 'school',
                'education', 'training', 'certificate', 'degree'
            ],
            'Health/Fitness': [
                'health', 'fitness', 'workout', 'diet', 'medical', 'doctor',
                'nutrition', 'wellness', 'exercise'
            ],
            'Shopping/Retail': [
                'shop', 'store', 'buy', 'purchase', 'product', 'cart',
                'amazon', 'ebay', 'retail', 'order'
            ]
        }

        # High-priority indicators
        self.priority_keywords = {
            'High': [
                'urgent', 'important', 'action required', 'expires', 'deadline',
                'security alert', 'verify', 'suspend', 'immediate'
            ],
            'Medium': [
                'reminder', 'notice', 'update', 'changes', 'attention',
                'review', 'confirmation'
            ]
        }

        # Automated content indicators
        self.automation_indicators = [
            'this is an automated', 'do not reply', 'unsubscribe',
            'automatically generated', 'no-reply', 'system message'
        ]

    def create_classification_schema(self) -> bool:
        """Create the classification columns in the database."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()

            # Check existing columns
            cursor.execute("PRAGMA table_info(emails)")
            existing_columns = {col[1] for col in cursor.fetchall()}

            classification_columns = [
                ('primary_category', 'TEXT'),
                ('domain_category', 'TEXT'),
                ('priority_level', 'TEXT'),
                ('source_type', 'TEXT'),
                ('action_required', 'TEXT'),
                ('confidence_score', 'REAL'),
                ('classification_rules', 'TEXT'),  # JSON of applied rules
                ('classification_date', 'TEXT'),
                ('sender_frequency', 'INTEGER'),   # How often this sender emails
                ('is_thread', 'BOOLEAN'),          # Part of email thread
                ('has_unsubscribe', 'BOOLEAN'),    # Has unsubscribe link
                ('automated_score', 'REAL')       # Automation likelihood 0-1
            ]

            added_columns = []
            for col_name, col_type in classification_columns:
                if col_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE emails ADD COLUMN {col_name} {col_type}")
                    added_columns.append(col_name)
                    self.logger.info(f"Added column: {col_name}")

            # Create indexes for better query performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_primary_category ON emails(primary_category)",
                "CREATE INDEX IF NOT EXISTS idx_domain_category ON emails(domain_category)",
                "CREATE INDEX IF NOT EXISTS idx_priority_level ON emails(priority_level)",
                "CREATE INDEX IF NOT EXISTS idx_sender_frequency ON emails(sender_frequency)",
                "CREATE INDEX IF NOT EXISTS idx_classification_date ON emails(classification_date)"
            ]

            for index_sql in indexes:
                cursor.execute(index_sql)

            conn.commit()

            if added_columns:
                self.logger.info(f"Successfully added {len(added_columns)} classification columns")
            else:
                self.logger.info("All classification columns already exist")

            return True

        except Exception as e:
            self.logger.error(f"Error creating classification schema: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def analyze_sender_patterns(self) -> dict[str, Any]:
        """Analyze sender patterns for frequency and domain analysis."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            # Get sender frequency data
            cursor.execute('''
                SELECT sender, COUNT(*) as frequency,
                       MIN(parsed_date) as first_email,
                       MAX(parsed_date) as last_email
                FROM emails
                WHERE sender IS NOT NULL
                GROUP BY sender
                ORDER BY frequency DESC
            ''')

            sender_stats = {}
            for row in cursor.fetchall():
                sender, freq, first, last = row
                sender_stats[sender] = {
                    'frequency': freq,
                    'first_email': first,
                    'last_email': last,
                    'domain': self._extract_domain(sender),
                    'email_prefix': self._extract_email_prefix(sender)
                }

            return sender_stats

        except Exception as e:
            self.logger.error(f"Error analyzing sender patterns: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def _extract_domain(self, sender: str) -> str:
        """Extract domain from sender email."""
        match = re.search(r'<([^@]+@([^>]+))>', sender)
        if match:
            return match.group(2)
        match = re.search(r'([^@\s]+@([^@\s]+))', sender)
        if match:
            return match.group(2)
        return 'unknown'

    def _extract_email_prefix(self, sender: str) -> str:
        """Extract email prefix (before @) from sender."""
        match = re.search(r'<([^@]+)@[^>]+>', sender)
        if match:
            return match.group(1)
        match = re.search(r'([^@\s]+)@', sender)
        if match:
            return match.group(1)
        return 'unknown'

    def classify_by_sender(self, sender: str, sender_stats: dict) -> dict[str, Any]:
        """Classify email based on sender patterns."""
        classification = {
            'primary_category': None,
            'source_type': None,
            'confidence': 0.0,
            'rules_applied': []
        }

        sender_lower = sender.lower()
        self._extract_domain(sender)
        self._extract_email_prefix(sender)

        # Check sender patterns
        for category, patterns in self.sender_patterns.items():
            for pattern in patterns:
                if re.search(pattern, sender_lower):
                    classification['primary_category'] = category
                    classification['confidence'] += 0.8
                    classification['rules_applied'].append(f'sender_pattern_{category}_{pattern}')
                    break
            if classification['primary_category']:
                break

        # Determine source type
        automation_indicators = [
            'noreply', 'no-reply', 'donotreply', 'automated', 'system'
        ]

        if any(indicator in sender_lower for indicator in automation_indicators):
            classification['source_type'] = 'Automated'
            classification['confidence'] += 0.3
            classification['rules_applied'].append('automated_sender')
        elif classification['primary_category'] in ['Newsletter', 'Service_Notification']:
            classification['source_type'] = 'Semi-automated'
            classification['confidence'] += 0.2
        else:
            classification['source_type'] = 'Human'
            classification['confidence'] += 0.1

        # Frequency analysis
        if sender in sender_stats:
            freq = sender_stats[sender]['frequency']
            if freq > 50:  # High frequency senders
                if not classification['primary_category']:
                    classification['primary_category'] = 'Newsletter'
                classification['confidence'] += 0.4
                classification['rules_applied'].append('high_frequency_sender')
            elif freq == 1:  # One-off senders
                if not classification['primary_category']:
                    classification['primary_category'] = 'Personal'
                classification['confidence'] += 0.2
                classification['rules_applied'].append('single_email_sender')

        return classification

    def classify_by_subject(self, subject: str) -> dict[str, Any]:
        """Classify email based on subject line patterns."""
        classification = {
            'primary_category': None,
            'priority_level': 'Medium',
            'is_thread': False,
            'confidence': 0.0,
            'rules_applied': []
        }

        if not subject:
            return classification

        subject_lower = subject.lower()

        # Check for thread indicators
        if re.search(r'^(re:|fwd:|fw:)', subject_lower):
            classification['is_thread'] = True
            classification['confidence'] += 0.3
            classification['rules_applied'].append('thread_indicator')

        # Check subject patterns
        for category, patterns in self.subject_patterns.items():
            for pattern in patterns:
                if re.search(pattern, subject_lower):
                    classification['primary_category'] = category
                    classification['confidence'] += 0.6
                    classification['rules_applied'].append(f'subject_pattern_{category}_{pattern}')
                    break
            if classification['primary_category']:
                break

        # Check priority indicators
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in subject_lower:
                    classification['priority_level'] = priority
                    classification['confidence'] += 0.2
                    classification['rules_applied'].append(f'priority_{priority}_{keyword}')
                    break

        return classification

    def classify_by_content(self, content: str, labels: str = '') -> dict[str, Any]:
        """Classify email based on content analysis."""
        classification = {
            'domain_category': None,
            'automated_score': 0.0,
            'has_unsubscribe': False,
            'action_required': 'Read_Only',
            'confidence': 0.0,
            'rules_applied': []
        }

        if not content:
            return classification

        content_lower = content.lower()

        # Check for unsubscribe links
        if 'unsubscribe' in content_lower:
            classification['has_unsubscribe'] = True
            classification['confidence'] += 0.3
            classification['rules_applied'].append('has_unsubscribe')

        # Check automation indicators
        automation_score = 0
        for indicator in self.automation_indicators:
            if indicator in content_lower:
                automation_score += 0.2
                classification['rules_applied'].append(f'automation_{indicator}')

        classification['automated_score'] = min(automation_score, 1.0)

        # Domain classification based on keywords
        domain_scores = defaultdict(int)
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                count = content_lower.count(keyword)
                if count > 0:
                    domain_scores[domain] += count * 0.1
                    classification['rules_applied'].append(f'domain_keyword_{domain}_{keyword}')

        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            classification['domain_category'] = best_domain[0]
            classification['confidence'] += min(best_domain[1], 0.5)

        # Check Gmail labels for additional classification
        if labels:
            labels_lower = labels.lower()
            if 'important' in labels_lower:
                classification['action_required'] = 'Reply_Needed'
                classification['confidence'] += 0.2
                classification['rules_applied'].append('gmail_important_label')
            elif 'category_promotions' in labels_lower:
                if not classification['domain_category']:
                    classification['domain_category'] = 'Shopping/Retail'
                classification['confidence'] += 0.3
                classification['rules_applied'].append('gmail_promotions_category')

        return classification

    def calculate_confidence_score(self, classifications: list[dict]) -> float:
        """Calculate overall confidence score from multiple classification results."""
        total_confidence = 0.0
        total_weight = 0.0

        weights = {
            'sender': 0.4,
            'subject': 0.3,
            'content': 0.3
        }

        for i, cls in enumerate(classifications):
            weight_key = ['sender', 'subject', 'content'][i]
            weight = weights[weight_key]
            confidence = cls.get('confidence', 0.0)

            total_confidence += confidence * weight
            total_weight += weight

        return min(total_confidence / total_weight if total_weight > 0 else 0.0, 1.0)

    def merge_classifications(self, sender_cls: dict, subject_cls: dict, content_cls: dict) -> dict:
        """Merge classification results from different analyses."""
        merged = {
            'primary_category': None,
            'domain_category': None,
            'priority_level': 'Medium',
            'source_type': 'Human',
            'action_required': 'Read_Only',
            'is_thread': False,
            'has_unsubscribe': False,
            'automated_score': 0.0,
            'confidence_score': 0.0,
            'classification_rules': [],
            'classification_date': datetime.now().isoformat()
        }

        # Primary category (priority: sender > subject > default)
        merged['primary_category'] = (
            sender_cls.get('primary_category') or
            subject_cls.get('primary_category') or
            'Other'
        )

        # Domain category from content analysis
        merged['domain_category'] = content_cls.get('domain_category') or 'Other'

        # Source type from sender analysis
        merged['source_type'] = sender_cls.get('source_type', 'Human')

        # Priority from subject analysis
        merged['priority_level'] = subject_cls.get('priority_level', 'Medium')

        # Action required from content analysis
        merged['action_required'] = content_cls.get('action_required', 'Read_Only')

        # Boolean flags
        merged['is_thread'] = subject_cls.get('is_thread', False)
        merged['has_unsubscribe'] = content_cls.get('has_unsubscribe', False)
        merged['automated_score'] = content_cls.get('automated_score', 0.0)

        # Merge all applied rules
        all_rules = []
        for cls in [sender_cls, subject_cls, content_cls]:
            all_rules.extend(cls.get('rules_applied', []))

        merged['classification_rules'] = json.dumps(all_rules)

        # Calculate overall confidence
        confidences = [
            sender_cls.get('confidence', 0.0),
            subject_cls.get('confidence', 0.0),
            content_cls.get('confidence', 0.0)
        ]
        merged['confidence_score'] = self.calculate_confidence_score([
            {'confidence': c} for c in confidences
        ])

        return merged

    def classify_emails_batch(self, batch_size: int = 100, offset: int = 0) -> tuple[int, int]:
        """Classify a batch of emails."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()

            # Get sender statistics for frequency analysis
            sender_stats = self.analyze_sender_patterns()

            # Get batch of unclassified emails
            cursor.execute('''
                SELECT id, sender, subject, plain_text_content, labels
                FROM emails
                WHERE primary_category IS NULL
                LIMIT ? OFFSET ?
            ''', (batch_size, offset))

            emails = cursor.fetchall()
            processed = 0
            errors = 0

            for email_id, sender, subject, content, labels in emails:
                try:
                    # Perform all classification analyses
                    sender_cls = self.classify_by_sender(sender or '', sender_stats)
                    subject_cls = self.classify_by_subject(subject or '')
                    content_cls = self.classify_by_content(content or '', labels or '')

                    # Merge results
                    final_classification = self.merge_classifications(
                        sender_cls, subject_cls, content_cls
                    )

                    # Add sender frequency
                    final_classification['sender_frequency'] = (
                        sender_stats.get(sender, {}).get('frequency', 0)
                    )

                    # Update database
                    update_sql = '''
                        UPDATE emails SET
                            primary_category = ?,
                            domain_category = ?,
                            priority_level = ?,
                            source_type = ?,
                            action_required = ?,
                            confidence_score = ?,
                            classification_rules = ?,
                            classification_date = ?,
                            sender_frequency = ?,
                            is_thread = ?,
                            has_unsubscribe = ?,
                            automated_score = ?
                        WHERE id = ?
                    '''

                    cursor.execute(update_sql, (
                        final_classification['primary_category'],
                        final_classification['domain_category'],
                        final_classification['priority_level'],
                        final_classification['source_type'],
                        final_classification['action_required'],
                        final_classification['confidence_score'],
                        final_classification['classification_rules'],
                        final_classification['classification_date'],
                        final_classification['sender_frequency'],
                        final_classification['is_thread'],
                        final_classification['has_unsubscribe'],
                        final_classification['automated_score'],
                        email_id
                    ))

                    processed += 1

                    if processed % 10 == 0:
                        self.logger.debug(f"Processed {processed} emails...")

                except Exception as e:
                    self.logger.error(f"Error classifying email {email_id}: {e}")
                    errors += 1

            conn.commit()
            return processed, errors

        except Exception as e:
            self.logger.error(f"Error in batch classification: {e}")
            return 0, 1
        finally:
            if conn:
                conn.close()

    def classify_all_emails(self, batch_size: int = 100) -> bool:
        """Classify all emails in the database."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM emails WHERE primary_category IS NULL')
            total_unclassified = cursor.fetchone()[0]

            if total_unclassified == 0:
                self.logger.info("All emails are already classified")
                return True

            self.logger.info(f"Classifying {total_unclassified} unclassified emails...")

            total_processed = 0
            total_errors = 0
            offset = 0

            while offset < total_unclassified:
                batch_end = min(offset + batch_size, total_unclassified)
                self.logger.info(f"Processing batch {offset // batch_size + 1}: "
                               f"emails {offset + 1}-{batch_end} of {total_unclassified}")

                processed, errors = self.classify_emails_batch(batch_size, offset)

                total_processed += processed
                total_errors += errors
                offset += batch_size

                if processed == 0:
                    break

            self.logger.info(f"Classification complete: {total_processed} processed, {total_errors} errors")
            return total_errors == 0

        except Exception as e:
            self.logger.error(f"Error classifying all emails: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def generate_classification_report(self) -> dict[str, Any]:
        """Generate comprehensive classification analysis report."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

            report = {
                'overview': {},
                'primary_categories': {},
                'domain_categories': {},
                'confidence_analysis': {},
                'sender_analysis': {},
                'temporal_analysis': {},
                'quality_metrics': {}
            }

            # Overview statistics
            cursor.execute('SELECT COUNT(*) FROM emails')
            total_emails = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM emails WHERE primary_category IS NOT NULL')
            classified_emails = cursor.fetchone()[0]

            cursor.execute('SELECT AVG(confidence_score) FROM emails WHERE confidence_score IS NOT NULL')
            avg_confidence = cursor.fetchone()[0] or 0.0

            report['overview'] = {
                'total_emails': total_emails,
                'classified_emails': classified_emails,
                'classification_rate': f"{(classified_emails/total_emails)*100:.1f}%",
                'average_confidence': f"{avg_confidence:.3f}"
            }

            # Primary category distribution
            cursor.execute('''
                SELECT primary_category, COUNT(*) as count,
                       AVG(confidence_score) as avg_confidence
                FROM emails
                WHERE primary_category IS NOT NULL
                GROUP BY primary_category
                ORDER BY count DESC
            ''')

            report['primary_categories'] = {
                row[0]: {
                    'count': row[1],
                    'percentage': f"{(row[1]/classified_emails)*100:.1f}%",
                    'avg_confidence': f"{row[2]:.3f}"
                }
                for row in cursor.fetchall()
            }

            # Domain category distribution
            cursor.execute('''
                SELECT domain_category, COUNT(*) as count,
                       AVG(confidence_score) as avg_confidence
                FROM emails
                WHERE domain_category IS NOT NULL AND domain_category != 'Other'
                GROUP BY domain_category
                ORDER BY count DESC
            ''')

            report['domain_categories'] = {
                row[0]: {
                    'count': row[1],
                    'percentage': f"{(row[1]/classified_emails)*100:.1f}%",
                    'avg_confidence': f"{row[2]:.3f}"
                }
                for row in cursor.fetchall()
            }

            # Top senders by category
            cursor.execute('''
                SELECT primary_category, sender, COUNT(*) as count
                FROM emails
                WHERE primary_category IS NOT NULL
                GROUP BY primary_category, sender
                HAVING count >= 3
                ORDER BY primary_category, count DESC
            ''')

            sender_analysis = defaultdict(list)
            for category, sender, count in cursor.fetchall():
                sender_analysis[category].append({
                    'sender': sender[:50] + '...' if len(sender) > 50 else sender,
                    'count': count
                })

            # Keep only top 5 senders per category
            report['sender_analysis'] = {
                category: senders[:5] for category, senders in sender_analysis.items()
            }

            # Confidence analysis
            cursor.execute('''
                SELECT
                    CASE
                        WHEN confidence_score >= 0.8 THEN 'High (0.8+)'
                        WHEN confidence_score >= 0.6 THEN 'Medium (0.6-0.8)'
                        WHEN confidence_score >= 0.4 THEN 'Low (0.4-0.6)'
                        ELSE 'Very Low (<0.4)'
                    END as confidence_range,
                    COUNT(*) as count
                FROM emails
                WHERE confidence_score IS NOT NULL
                GROUP BY confidence_range
                ORDER BY confidence_score DESC
            ''')

            report['confidence_analysis'] = {
                row[0]: {
                    'count': row[1],
                    'percentage': f"{(row[1]/classified_emails)*100:.1f}%"
                }
                for row in cursor.fetchall()
            }

            # Quality metrics
            cursor.execute('SELECT COUNT(*) FROM emails WHERE automated_score > 0.5')
            automated_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM emails WHERE has_unsubscribe = 1')
            newsletter_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM emails WHERE is_thread = 1')
            thread_count = cursor.fetchone()[0]

            report['quality_metrics'] = {
                'automated_emails': f"{automated_count} ({(automated_count/total_emails)*100:.1f}%)",
                'emails_with_unsubscribe': f"{newsletter_count} ({(newsletter_count/total_emails)*100:.1f}%)",
                'thread_emails': f"{thread_count} ({(thread_count/total_emails)*100:.1f}%)"
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def print_classification_report(self, report: dict[str, Any]):
        """Print a formatted classification report."""
        print("\n" + "="*80)
        print("📊 EMAIL CLASSIFICATION ANALYSIS REPORT")
        print("="*80)

        # Overview
        overview = report.get('overview', {})
        print("\n📈 OVERVIEW")
        print(f"   Total Emails: {overview.get('total_emails', 0):,}")
        print(f"   Classified: {overview.get('classified_emails', 0):,} ({overview.get('classification_rate', '0%')})")
        print(f"   Average Confidence: {overview.get('average_confidence', '0.000')}")

        # Primary Categories
        print("\n🏷️  PRIMARY CATEGORIES")
        categories = report.get('primary_categories', {})
        for category, stats in categories.items():
            print(f"   {category:<20}: {stats['count']:>4} emails ({stats['percentage']}) - conf: {stats['avg_confidence']}")

        # Domain Categories
        print("\n🌐 DOMAIN CATEGORIES")
        domains = report.get('domain_categories', {})
        for domain, stats in domains.items():
            print(f"   {domain:<20}: {stats['count']:>4} emails ({stats['percentage']}) - conf: {stats['avg_confidence']}")

        # Confidence Analysis
        print("\n✅ CONFIDENCE ANALYSIS")
        confidence = report.get('confidence_analysis', {})
        for conf_range, stats in confidence.items():
            print(f"   {conf_range:<15}: {stats['count']:>4} emails ({stats['percentage']})")

        # Quality Metrics
        print("\n🔍 QUALITY METRICS")
        metrics = report.get('quality_metrics', {})
        for metric, value in metrics.items():
            print(f"   {metric.replace('_', ' ').title():<25}: {value}")

        # Top Senders by Category
        print("\n👥 TOP SENDERS BY CATEGORY")
        senders = report.get('sender_analysis', {})
        for category, sender_list in senders.items():
            if sender_list:
                print(f"   {category}:")
                for sender_info in sender_list[:3]:  # Show top 3
                    print(f"      {sender_info['count']:>3}: {sender_info['sender']}")

        print("\n" + "="*80)


def main():
    """Main entry point for the email classifier."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Email Classification System"
    )

    parser.add_argument(
        '--db',
        required=True,
        help='Path to the email database'
    )

    parser.add_argument(
        '--phase',
        choices=['1', '2', '3', 'all'],
        default='all',
        help='Classification phase to run (default: all)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing (default: 100)'
    )

    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze patterns without classifying'
    )

    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Only generate classification report'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    print("🚀 Email Classification System")
    print(f"Database: {args.db}")
    print(f"Phase: {args.phase}")
    print(f"Batch size: {args.batch_size}")
    print("-" * 60)

    classifier = EmailClassifier(args.db)

    # Generate report only
    if args.report_only:
        print("Generating classification report...")
        report = classifier.generate_classification_report()
        classifier.print_classification_report(report)
        return

    # Analysis only
    if args.analyze_only:
        print("Analyzing email patterns...")
        sender_stats = classifier.analyze_sender_patterns()
        print(f"Found {len(sender_stats)} unique senders")

        # Show top patterns
        top_senders = sorted(sender_stats.items(),
                           key=lambda x: x[1]['frequency'], reverse=True)[:10]

        print("\nTop 10 Senders:")
        for sender, stats in top_senders:
            print(f"  {stats['frequency']:>3}: {sender[:60]}...")

        return

    # Create schema
    if not classifier.create_classification_schema():
        print("❌ Failed to create classification schema")
        sys.exit(1)

    # Run classification
    start_time = datetime.now()

    if args.phase in ['1', 'all']:
        print("🔄 Phase 1: Foundation Classification (Sender & Frequency Analysis)")

    if args.phase in ['2', 'all']:
        print("🔄 Phase 2: Content Enhancement (Subject & Content Analysis)")

    if args.phase in ['3', 'all']:
        print("🔄 Phase 3: Advanced Analytics (Confidence Scoring)")

    success = classifier.classify_all_emails(args.batch_size)
    end_time = datetime.now()

    print(f"\n⏱️  Processing completed in {end_time - start_time}")

    if success:
        print("✅ Classification completed successfully!")

        # Generate and display report
        print("\n📊 Generating classification report...")
        report = classifier.generate_classification_report()
        classifier.print_classification_report(report)

    else:
        print("❌ Classification completed with errors. Check the log file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
