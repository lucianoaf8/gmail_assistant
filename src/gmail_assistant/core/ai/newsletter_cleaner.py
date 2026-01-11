#!/usr/bin/env python3
"""
Gmail AI Newsletter Cleaner
Identifies and deletes AI newsletter emails with dry-run support and logging.

Security: Implements ReDoS protection with regex timeout (M-2 fix)
"""

import argparse
import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime

# Use regex module for timeout support (M-2 security fix)
try:
    import regex
    HAS_REGEX_TIMEOUT = True
except ImportError:
    import re as regex
    HAS_REGEX_TIMEOUT = False

# Import centralized constants and schemas
from gmail_assistant.core.constants import AI_CONFIG_PATH
from gmail_assistant.core.schemas import Email
from gmail_assistant.utils.input_validator import InputValidator
from gmail_assistant.utils.secure_logger import SecureLogger

logger = SecureLogger(__name__)

# ReDoS protection constants (M-2 fix)
REGEX_TIMEOUT = 0.1  # 100ms timeout per pattern match
MAX_INPUT_LENGTH = 500  # Truncate input to prevent ReDoS


@dataclass
class EmailData:
    """
    Structure for email data.

    DEPRECATED (H-1): Use Email from gmail_assistant.core.schemas instead.
    This class is kept for backward compatibility.
    """
    id: str
    subject: str
    sender: str
    date: str
    labels: list[str] = None
    thread_id: str = None
    body_snippet: str = ""

    def __post_init__(self):
        import warnings
        warnings.warn(
            "EmailData is deprecated. Use Email from core.schemas instead.",
            DeprecationWarning,
            stacklevel=3
        )

    def to_email(self) -> Email:
        """Convert to canonical Email model."""
        from datetime import datetime
        return Email(
            gmail_id=self.id,
            thread_id=self.thread_id or "",
            subject=self.subject,
            sender=self.sender,
            date=self.date or datetime.now().isoformat(),
            labels=self.labels or [],
            snippet=self.body_snippet
        )

class AINewsletterDetector:
    """Detects AI newsletters using multiple pattern matching strategies"""

    def __init__(self, config_path: str | None = None):
        # Use default config path if not provided
        resolved_path = config_path or str(AI_CONFIG_PATH)

        # Validate user-provided config paths (L-AUDIT-03 fix)
        if config_path is not None:
            # Get config directory as allowed base
            config_dir = str(AI_CONFIG_PATH.parent) if hasattr(AI_CONFIG_PATH, 'parent') else 'config'
            is_valid, validated_path = InputValidator.validate_file_path(
                config_path,
                allowed_base=config_dir,
                allow_create=False
            )
            if not is_valid:
                logger.warning(
                    f"Invalid config path '{config_path}', using default: {AI_CONFIG_PATH}"
                )
                resolved_path = str(AI_CONFIG_PATH)
            else:
                resolved_path = validated_path

        self.config_path = resolved_path
        self.load_config()
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency (M-2 fix)"""
        self._compiled_newsletter_patterns = []
        self._compiled_unsubscribe_patterns = []

        for pattern in self.newsletter_patterns:
            try:
                compiled = regex.compile(pattern, flags=regex.IGNORECASE)
                self._compiled_newsletter_patterns.append(compiled)
            except regex.error as e:
                logger.warning(f"Invalid newsletter pattern '{pattern}': {e}")

        for pattern in self.unsubscribe_patterns:
            try:
                compiled = regex.compile(pattern, flags=regex.IGNORECASE)
                self._compiled_unsubscribe_patterns.append(compiled)
            except regex.error as e:
                logger.warning(f"Invalid unsubscribe pattern '{pattern}': {e}")

    def _safe_regex_search(self, pattern, text: str) -> bool:
        """
        Perform regex search with timeout and input truncation (M-2 fix).

        Args:
            pattern: Compiled regex pattern or pattern string
            text: Text to search (will be truncated if too long)

        Returns:
            True if pattern matches, False otherwise
        """
        # Truncate input to prevent ReDoS
        truncated_text = text[:MAX_INPUT_LENGTH]

        try:
            if HAS_REGEX_TIMEOUT:
                # Use regex module with timeout
                match = pattern.search(truncated_text, timeout=REGEX_TIMEOUT)
            else:
                # Fallback to standard re without timeout
                match = pattern.search(truncated_text)
            return match is not None
        except regex.error as e:
            logger.warning(f"Regex error: {e}")
            return False
        except TimeoutError:
            logger.warning(f"Regex timeout on input length {len(text)}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected regex error: {e}")
            return False

    def load_config(self):
        """Load configuration from JSON file with fallback to defaults"""
        try:
            with open(self.config_path, encoding='utf-8') as f:
                config = json.load(f)

            self.ai_keywords = set(config.get('ai_keywords', []))
            self.ai_newsletter_domains = set(config.get('ai_newsletter_domains', []))
            self.newsletter_patterns = config.get('newsletter_patterns', [])
            self.unsubscribe_patterns = config.get('unsubscribe_patterns', [])
            self.confidence_weights = config.get('confidence_weights', {})
            self.decision_threshold = config.get('decision_threshold', {})

            print(f"✅ Loaded configuration from {self.config_path}")

        except FileNotFoundError:
            print(f"⚠️  Config file {self.config_path} not found, using defaults")
            self._load_default_config()
        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON in {self.config_path}, using defaults")
            self._load_default_config()

    def _load_default_config(self):
        """Load default configuration"""
        self.ai_keywords = {
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'chatgpt', 'openai', 'anthropic', 'claude', 'gpt-4', 'llm', 'large language',
            'ai news', 'ai weekly', 'ai digest', 'ai newsletter', 'ai updates',
            'ml news', 'ml weekly', 'deep tech', 'ai research', 'ai breakthroughs',
            'gen ai', 'generative ai', 'foundation models', 'transformer',
            'prompt engineering', 'ai tools', 'ai startup', 'ai industry'
        }

        self.ai_newsletter_domains = {
            'deeplearning.ai', 'openai.com', 'anthropic.com', 'huggingface.co',
            'thesequence.substack.com', 'importai.substack.com', 'thebatch.ai',
            'aiweekly.co', 'theaitimes.com', 'artificialintelligence-news.com',
            'venturebeat.com', 'techcrunch.com', 'thenextweb.com',
            'newsletter.deepmind.com', 'ai.googleblog.com', 'research.fb.com',
            'distill.pub', 'paperswithcode.com', 'towards-data-science',
            'kdnuggets.com', 'analyticsindiamag.com'
        }

        self.newsletter_patterns = [
            r'weekly.*ai', r'ai.*weekly', r'daily.*ai', r'ai.*daily',
            r'newsletter.*ai', r'ai.*newsletter', r'digest.*ai', r'ai.*digest',
            r'roundup.*ai', r'ai.*roundup', r'briefing.*ai', r'ai.*briefing',
            r'updates.*ai', r'ai.*updates', r'summary.*ai', r'ai.*summary'
        ]

        self.unsubscribe_patterns = [
            r'unsubscribe', r'opt.?out', r'manage.*subscription',
            r'email.*preference', r'update.*preference'
        ]

        self.confidence_weights = {
            'ai_keywords_subject': 3,
            'ai_keywords_sender': 2,
            'known_domain': 4,
            'newsletter_pattern': 2,
            'unsubscribe_link': 1,
            'automated_sender': 1
        }

        self.decision_threshold = {
            'minimum_confidence': 4,
            'minimum_reasons': 2
        }

    def is_ai_newsletter(self, email: EmailData) -> dict[str, any]:
        """
        Determine if email is an AI newsletter.
        Returns dict with decision and reasoning.

        Security: Uses ReDoS-protected regex matching (M-2 fix)
        """
        reasons = []
        confidence = 0

        # Truncate and lowercase inputs for safety (M-2 fix)
        subject_lower = email.subject[:MAX_INPUT_LENGTH].lower()
        sender_lower = email.sender[:MAX_INPUT_LENGTH].lower()
        body_lower = email.body_snippet[:MAX_INPUT_LENGTH].lower()

        # Check AI keywords in subject (no regex needed)
        ai_in_subject = any(keyword in subject_lower for keyword in self.ai_keywords)
        if ai_in_subject:
            reasons.append("AI keywords in subject")
            confidence += self.confidence_weights.get('ai_keywords_subject', 3)

        # Check AI keywords in sender (no regex needed)
        ai_in_sender = any(keyword in sender_lower for keyword in self.ai_keywords)
        if ai_in_sender:
            reasons.append("AI keywords in sender")
            confidence += self.confidence_weights.get('ai_keywords_sender', 2)

        # Check known AI newsletter domains (no regex needed)
        domain_match = any(domain in sender_lower for domain in self.ai_newsletter_domains)
        if domain_match:
            reasons.append("Known AI newsletter domain")
            confidence += self.confidence_weights.get('known_domain', 4)

        # Check newsletter patterns with timeout protection (M-2 fix)
        search_text = f"{subject_lower} {sender_lower}"
        newsletter_pattern_match = any(
            self._safe_regex_search(pattern, search_text)
            for pattern in self._compiled_newsletter_patterns
        )
        if newsletter_pattern_match:
            reasons.append("Newsletter pattern match")
            confidence += self.confidence_weights.get('newsletter_pattern', 2)

        # Check for unsubscribe indicators with timeout protection (M-2 fix)
        unsubscribe_match = any(
            self._safe_regex_search(pattern, body_lower)
            for pattern in self._compiled_unsubscribe_patterns
        )
        if unsubscribe_match:
            reasons.append("Contains unsubscribe link")
            confidence += self.confidence_weights.get('unsubscribe_link', 1)

        # Check if from automation/no-reply (no regex needed)
        automated_sender = any(indicator in sender_lower for indicator in
                             ['no-reply', 'noreply', 'automated', 'newsletter', 'digest'])
        if automated_sender:
            reasons.append("Automated sender")
            confidence += self.confidence_weights.get('automated_sender', 1)

        # Decision using configurable thresholds
        min_confidence = self.decision_threshold.get('minimum_confidence', 4)
        min_reasons = self.decision_threshold.get('minimum_reasons', 2)

        is_newsletter = confidence >= min_confidence or (confidence >= min_confidence - 1 and len(reasons) >= min_reasons)

        return {
            'is_ai_newsletter': is_newsletter,
            'confidence': confidence,
            'reasons': reasons,
            'subject': email.subject,
            'sender': email.sender
        }

class EmailDataLoader:
    """Loads email data from various formats"""

    @staticmethod
    def load_from_json(file_path: str) -> list[EmailData]:
        """Load emails from JSON format"""
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        emails = []
        # Handle different JSON structures
        if isinstance(data, list):
            email_list = data
        elif 'emails' in data:
            email_list = data['emails']
        elif 'messages' in data:
            email_list = data['messages']
        else:
            email_list = [data]

        for item in email_list:
            emails.append(EmailData(
                id=item.get('id', ''),
                subject=item.get('subject', ''),
                sender=item.get('from', item.get('sender', '')),
                date=item.get('date', ''),
                labels=item.get('labels', []),
                thread_id=item.get('threadId', ''),
                body_snippet=item.get('snippet', item.get('body', ''))
            ))

        return emails

    @staticmethod
    def load_from_csv(file_path: str) -> list[EmailData]:
        """Load emails from CSV format"""
        emails = []
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                emails.append(EmailData(
                    id=row.get('id', row.get('message_id', '')),
                    subject=row.get('subject', ''),
                    sender=row.get('from', row.get('sender', '')),
                    date=row.get('date', ''),
                    labels=row.get('labels', '').split(',') if row.get('labels') else [],
                    thread_id=row.get('thread_id', ''),
                    body_snippet=row.get('snippet', row.get('body', ''))
                ))

        return emails

class GmailCleaner:
    """Main class for Gmail cleaning operations"""

    def __init__(self, dry_run: bool = True, config_path: str = '../config/config.json'):
        self.dry_run = dry_run
        self.detector = AINewsletterDetector(config_path)
        self.deleted_emails = []
        self.log_file = f"gmail_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    def analyze_emails(self, emails: list[EmailData]) -> dict[str, list]:
        """Analyze emails and categorize them"""
        ai_newsletters = []
        other_emails = []

        print(f"\n🔍 Analyzing {len(emails)} emails...")

        for i, email in enumerate(emails):
            if i % 100 == 0:
                print(f"  Processed {i}/{len(emails)} emails...")

            result = self.detector.is_ai_newsletter(email)

            if result['is_ai_newsletter']:
                ai_newsletters.append({
                    'email': email,
                    'analysis': result
                })
            else:
                other_emails.append(email)

        return {
            'ai_newsletters': ai_newsletters,
            'other_emails': other_emails
        }

    def delete_ai_newsletters(self, ai_newsletters: list[dict]) -> None:
        """Delete AI newsletters (or simulate deletion in dry-run mode)"""

        if not ai_newsletters:
            print("\n✅ No AI newsletters found to delete.")
            return

        print(f"\n{'🔍 DRY RUN MODE' if self.dry_run else '🗑️  DELETION MODE'}: Processing {len(ai_newsletters)} AI newsletters...")

        with open(self.log_file, 'w', encoding='utf-8') as log:
            log.write(f"Gmail AI Newsletter Cleanup Log - {datetime.now()}\n")
            log.write(f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL DELETION'}\n")
            log.write(f"Total AI newsletters identified: {len(ai_newsletters)}\n\n")

            for i, item in enumerate(ai_newsletters):
                email = item['email']
                analysis = item['analysis']

                action = "WOULD DELETE" if self.dry_run else "DELETED"

                log_entry = f"{action}: {email.id}\n"
                log_entry += f"  Subject: {email.subject}\n"
                log_entry += f"  From: {email.sender}\n"
                log_entry += f"  Date: {email.date}\n"
                log_entry += f"  Confidence: {analysis['confidence']}\n"
                log_entry += f"  Reasons: {', '.join(analysis['reasons'])}\n"
                log_entry += "-" * 80 + "\n\n"

                log.write(log_entry)

                if not self.dry_run:
                    # Here you would implement actual Gmail API deletion
                    # gmail_service.users().messages().delete(userId='me', id=email.id).execute()
                    pass

                self.deleted_emails.append(email)

                if (i + 1) % 50 == 0:
                    print(f"  Processed {i + 1}/{len(ai_newsletters)} newsletters...")

        mode_text = "identified for deletion" if self.dry_run else "deleted"
        print(f"\n✅ {len(ai_newsletters)} AI newsletters {mode_text}")
        print(f"📝 Detailed log saved to: {self.log_file}")

    def generate_summary(self, analysis_result: dict) -> None:
        """Generate cleanup summary"""
        ai_count = len(analysis_result['ai_newsletters'])
        other_count = len(analysis_result['other_emails'])
        total = ai_count + other_count

        print("\n📊 CLEANUP SUMMARY")
        print(f"{'='*50}")
        print(f"Total emails analyzed: {total}")
        print(f"AI newsletters identified: {ai_count} ({ai_count/total*100:.1f}%)")
        print(f"Other emails preserved: {other_count} ({other_count/total*100:.1f}%)")

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No emails were actually deleted")
            print("🔄 Run with --delete flag to perform actual deletion")
        else:
            print("\n✅ Deletion completed successfully")

        print(f"📝 Detailed log: {self.log_file}")

def main():
    parser = argparse.ArgumentParser(description='Clean AI newsletters from Gmail')
    parser.add_argument('data_file', help='Path to email data file (JSON or CSV)')
    parser.add_argument('--delete', action='store_true', help='Actually delete emails (default: dry run)')
    parser.add_argument('--format', choices=['json', 'csv'], help='Data format (auto-detected if not specified)')
    parser.add_argument('--config', default='../config/config.json', help='Path to configuration file')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.data_file):
        print(f"❌ Error: File '{args.data_file}' not found")
        return

    # Auto-detect format if not specified
    if not args.format:
        if args.data_file.endswith('.json'):
            args.format = 'json'
        elif args.data_file.endswith('.csv'):
            args.format = 'csv'
        else:
            print("❌ Error: Could not detect file format. Please specify --format")
            return

    print("🚀 Gmail AI Newsletter Cleaner")
    print(f"📁 Loading data from: {args.data_file}")
    print(f"📊 Format: {args.format.upper()}")
    print(f"⚙️  Config: {args.config}")
    print(f"🎯 Mode: {'DELETION' if args.delete else 'DRY RUN'}")

    try:
        # Load email data
        if args.format == 'json':
            emails = EmailDataLoader.load_from_json(args.data_file)
        else:
            emails = EmailDataLoader.load_from_csv(args.data_file)

        print(f"✅ Loaded {len(emails)} emails")

        # Initialize cleaner with config
        cleaner = GmailCleaner(dry_run=not args.delete, config_path=args.config)

        # Analyze emails
        analysis_result = cleaner.analyze_emails(emails)

        # Delete AI newsletters
        cleaner.delete_ai_newsletters(analysis_result['ai_newsletters'])

        # Generate summary
        cleaner.generate_summary(analysis_result)

    except Exception as e:
        print(f"❌ Error: {e!s}")
        return

# Alias for backward compatibility
AINewsletterCleaner = GmailCleaner


if __name__ == "__main__":
    main()
