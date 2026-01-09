#!/usr/bin/env python3
"""
Gmail Essential Organizer
Keeps only essential emails and deletes everything else with detailed reporting.
"""

import json
import csv
import re
import os
import argparse
from datetime import datetime
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from pathlib import Path
from gmail_ai_newsletter_cleaner import EmailData, EmailDataLoader

@dataclass
class EmailAction:
    """Action to take on an email"""
    email: EmailData
    action: str  # 'keep', 'delete'
    category: str
    folder: str = None
    confidence: int = 0
    reasons: List[str] = None

class EssentialEmailDetector:
    """Detects essential emails that should be kept"""
    
    def __init__(self, config_path: str = 'organizer_config.json'):
        self.config_path = config_path
        self.load_config()
    
    def load_config(self):
        """Load configuration with fallback to defaults"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.work_patterns = config.get('work_patterns', {})
            self.urgent_patterns = config.get('urgent_patterns', {})
            self.financial_alert_patterns = config.get('financial_alert_patterns', {})
            self.legal_gov_patterns = config.get('legal_gov_patterns', {})
            self.tax_patterns = config.get('tax_patterns', {})
            self.delete_patterns = config.get('delete_patterns', {})
            
            print(f"✅ Loaded organizer configuration from {self.config_path}")
            
        except FileNotFoundError:
            print(f"⚠️  Config file {self.config_path} not found, using defaults")
            self._load_default_config()
        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON in {self.config_path}, using defaults")
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default patterns"""
        
        # Work emails needing responses
        self.work_patterns = {
            'keywords': [
                'urgent', 'asap', 'deadline', 'meeting', 'call', 'review', 'approval',
                'action required', 'please respond', 'need feedback', 'by eod',
                'follow up', 'status update', 'project', 'client', 'proposal'
            ],
            'domains': [
                'company.com', 'work.com', 'corp.com', 'org.com', 'enterprise.com'
                # Add your actual work domains here
            ],
            'senders': [
                'boss@', 'manager@', 'hr@', 'client@', 'customer@'
            ]
        }
        
        # Urgent personal correspondence
        self.urgent_patterns = {
            'keywords': [
                'emergency', 'urgent', 'important', 'critical', 'immediate',
                'hospital', 'accident', 'police', 'doctor', 'medical'
            ],
            'personal_domains': [
                'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'
            ]
        }
        
        # Financial alerts (fraud, payment due)
        self.financial_alert_patterns = {
            'keywords': [
                'fraud alert', 'suspicious activity', 'security alert', 'unauthorized',
                'payment due', 'overdue', 'past due', 'collection', 'delinquent',
                'account locked', 'account suspended', 'verify account'
            ],
            'domains': [
                'bank.com', 'chase.com', 'wellsfargo.com', 'bankofamerica.com',
                'citi.com', 'usbank.com', 'capitalone.com', 'discover.com',
                'amex.com', 'americanexpress.com', 'paypal.com', 'venmo.com'
            ]
        }
        
        # Legal/government communications
        self.legal_gov_patterns = {
            'keywords': [
                'court', 'legal', 'lawsuit', 'subpoena', 'jury duty', 'dmv',
                'irs', 'tax', 'government', 'federal', 'state', 'city hall',
                'license', 'permit', 'registration', 'violation', 'citation'
            ],
            'domains': [
                '.gov', '.org', 'irs.gov', 'dmv.', 'court.', 'state.',
                'city.', 'county.', 'federal'
            ]
        }
        
        # Tax documents
        self.tax_patterns = {
            'keywords': [
                'tax', 'w-2', 'w2', '1099', 'tax document', 'tax form',
                'tax return', 'refund', 'irs', 'tax preparation'
            ],
            'file_types': [
                '.pdf', 'tax document', 'tax form'
            ]
        }
        
        # Common deletion candidates
        self.delete_patterns = {
            'promotional': [
                'sale', 'discount', 'offer', 'deal', 'coupon', 'promo',
                'limited time', 'shop now', 'buy now', 'unsubscribe'
            ],
            'social_media': [
                'facebook', 'twitter', 'instagram', 'linkedin', 'tiktok',
                'notification', 'comment', 'like', 'follow', 'connection'
            ],
            'newsletters': [
                'newsletter', 'weekly', 'daily', 'digest', 'roundup',
                'update', 'briefing', 'summary'
            ]
        }
    
    def analyze_email(self, email: EmailData) -> EmailAction:
        """Analyze email and determine action"""
        
        subject_lower = email.subject.lower()
        sender_lower = email.sender.lower()
        body_lower = email.body_snippet.lower()
        
        # Check each keep category
        
        # 1. Work emails needing responses
        work_result = self._check_work_email(email, subject_lower, sender_lower, body_lower)
        if work_result:
            return work_result
        
        # 2. Urgent personal correspondence
        urgent_result = self._check_urgent_personal(email, subject_lower, sender_lower, body_lower)
        if urgent_result:
            return urgent_result
        
        # 3. Financial alerts
        financial_result = self._check_financial_alerts(email, subject_lower, sender_lower, body_lower)
        if financial_result:
            return financial_result
        
        # 4. Legal/government communications
        legal_result = self._check_legal_gov(email, subject_lower, sender_lower, body_lower)
        if legal_result:
            return legal_result
        
        # 5. Tax documents
        tax_result = self._check_tax_documents(email, subject_lower, sender_lower, body_lower)
        if tax_result:
            return tax_result
        
        # If none of the keep categories match, mark for deletion
        delete_category = self._categorize_for_deletion(email, subject_lower, sender_lower, body_lower)
        
        return EmailAction(
            email=email,
            action='delete',
            category=delete_category,
            confidence=5,
            reasons=[f"Not in essential categories, classified as {delete_category}"]
        )
    
    def _check_work_email(self, email, subject_lower, sender_lower, body_lower):
        """Check if email is work-related and needs response"""
        reasons = []
        confidence = 0
        
        # Check for work keywords
        work_keywords = any(keyword in subject_lower or keyword in body_lower 
                           for keyword in self.work_patterns['keywords'])
        if work_keywords:
            reasons.append("Contains work keywords")
            confidence += 3
        
        # Check work domains
        work_domain = any(domain in sender_lower for domain in self.work_patterns['domains'])
        if work_domain:
            reasons.append("From work domain")
            confidence += 4
        
        # Check work senders
        work_sender = any(sender in sender_lower for sender in self.work_patterns['senders'])
        if work_sender:
            reasons.append("From work-related sender")
            confidence += 3
        
        if confidence >= 3:
            return EmailAction(
                email=email,
                action='keep',
                category='Work - Action Required',
                folder='Work/Action Required',
                confidence=confidence,
                reasons=reasons
            )
        return None
    
    def _check_urgent_personal(self, email, subject_lower, sender_lower, body_lower):
        """Check if email is urgent personal correspondence"""
        reasons = []
        confidence = 0
        
        # Check urgent keywords
        urgent_keywords = any(keyword in subject_lower or keyword in body_lower 
                             for keyword in self.urgent_patterns['keywords'])
        if urgent_keywords:
            reasons.append("Contains urgent keywords")
            confidence += 4
        
        # Check if from personal domain with urgent markers
        personal_domain = any(domain in sender_lower for domain in self.urgent_patterns['personal_domains'])
        if personal_domain and urgent_keywords:
            reasons.append("Personal domain with urgent content")
            confidence += 2
        
        if confidence >= 4:
            return EmailAction(
                email=email,
                action='keep',
                category='Urgent Personal',
                folder='Personal/Urgent',
                confidence=confidence,
                reasons=reasons
            )
        return None
    
    def _check_financial_alerts(self, email, subject_lower, sender_lower, body_lower):
        """Check if email is financial alert"""
        reasons = []
        confidence = 0
        
        # Check financial alert keywords
        alert_keywords = any(keyword in subject_lower or keyword in body_lower 
                            for keyword in self.financial_alert_patterns['keywords'])
        if alert_keywords:
            reasons.append("Contains financial alert keywords")
            confidence += 4
        
        # Check financial domains
        financial_domain = any(domain in sender_lower for domain in self.financial_alert_patterns['domains'])
        if financial_domain:
            reasons.append("From financial institution")
            confidence += 3
        
        if confidence >= 4:
            return EmailAction(
                email=email,
                action='keep',
                category='Financial Alert',
                folder='Financial/Alerts',
                confidence=confidence,
                reasons=reasons
            )
        return None
    
    def _check_legal_gov(self, email, subject_lower, sender_lower, body_lower):
        """Check if email is legal/government communication"""
        reasons = []
        confidence = 0
        
        # Check legal/gov keywords
        legal_keywords = any(keyword in subject_lower or keyword in body_lower 
                            for keyword in self.legal_gov_patterns['keywords'])
        if legal_keywords:
            reasons.append("Contains legal/government keywords")
            confidence += 3
        
        # Check gov domains
        gov_domain = any(domain in sender_lower for domain in self.legal_gov_patterns['domains'])
        if gov_domain:
            reasons.append("From government domain")
            confidence += 4
        
        if confidence >= 3:
            return EmailAction(
                email=email,
                action='keep',
                category='Legal/Government',
                folder='Legal-Government',
                confidence=confidence,
                reasons=reasons
            )
        return None
    
    def _check_tax_documents(self, email, subject_lower, sender_lower, body_lower):
        """Check if email contains tax documents"""
        reasons = []
        confidence = 0
        
        # Check tax keywords
        tax_keywords = any(keyword in subject_lower or keyword in body_lower 
                          for keyword in self.tax_patterns['keywords'])
        if tax_keywords:
            reasons.append("Contains tax-related keywords")
            confidence += 4
        
        # Check for tax document file types
        tax_files = any(filetype in body_lower for filetype in self.tax_patterns['file_types'])
        if tax_files:
            reasons.append("Contains tax document attachments")
            confidence += 3
        
        if confidence >= 4:
            return EmailAction(
                email=email,
                action='keep',
                category='Tax Documents',
                folder='Financial/Tax-Documents',
                confidence=confidence,
                reasons=reasons
            )
        return None
    
    def _categorize_for_deletion(self, email, subject_lower, sender_lower, body_lower):
        """Categorize emails marked for deletion"""
        
        # Check promotional
        if any(keyword in subject_lower or keyword in body_lower 
               for keyword in self.delete_patterns['promotional']):
            return 'Promotional/Marketing'
        
        # Check social media
        if any(keyword in subject_lower or keyword in sender_lower 
               for keyword in self.delete_patterns['social_media']):
            return 'Social Media Notifications'
        
        # Check newsletters
        if any(keyword in subject_lower or keyword in sender_lower 
               for keyword in self.delete_patterns['newsletters']):
            return 'Newsletters/Updates'
        
        # Check for confirmations/receipts
        if any(keyword in subject_lower for keyword in ['confirmation', 'receipt', 'order', 'shipping']):
            return 'Confirmations/Receipts'
        
        # Check for travel
        if any(keyword in subject_lower for keyword in ['flight', 'hotel', 'booking', 'reservation']):
            return 'Travel/Bookings'
        
        # Default category
        return 'Other/Miscellaneous'

class EmailOrganizer:
    """Main organizer class"""
    
    def __init__(self, dry_run: bool = True, config_path: str = 'organizer_config.json'):
        self.dry_run = dry_run
        self.detector = EssentialEmailDetector(config_path)
        self.log_file = f"email_organizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.actions = []
    
    def analyze_emails(self, emails: List[EmailData]) -> Dict[str, List[EmailAction]]:
        """Analyze all emails and categorize actions"""
        print(f"\n🔍 Analyzing {len(emails)} emails...")
        
        keep_actions = []
        delete_actions = []
        
        for i, email in enumerate(emails):
            if i % 100 == 0:
                print(f"  Processed {i}/{len(emails)} emails...")
            
            action = self.detector.analyze_email(email)
            self.actions.append(action)
            
            if action.action == 'keep':
                keep_actions.append(action)
            else:
                delete_actions.append(action)
        
        return {
            'keep': keep_actions,
            'delete': delete_actions
        }
    
    def generate_report(self, analysis_result: Dict[str, List[EmailAction]]) -> None:
        """Generate detailed report"""
        
        keep_actions = analysis_result['keep']
        delete_actions = analysis_result['delete']
        
        with open(self.log_file, 'w', encoding='utf-8') as log:
            log.write(f"Gmail Essential Organizer Report - {datetime.now()}\n")
            log.write(f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL ORGANIZATION'}\n")
            log.write("=" * 80 + "\n\n")
            
            # Keep section
            log.write(f"📌 EMAILS TO KEEP ({len(keep_actions)})\n")
            log.write("=" * 40 + "\n\n")
            
            for action in keep_actions:
                email = action.email
                log.write(f"KEEP: {email.id}\n")
                log.write(f"  Category: {action.category}\n")
                log.write(f"  Folder: {action.folder}\n")
                log.write(f"  Subject: {email.subject}\n")
                log.write(f"  From: {email.sender}\n")
                log.write(f"  Confidence: {action.confidence}\n")
                log.write(f"  Reasons: {', '.join(action.reasons)}\n")
                log.write("-" * 60 + "\n\n")
            
            # Delete section with summary by category
            log.write(f"🗑️ EMAILS TO DELETE ({len(delete_actions)})\n")
            log.write("=" * 40 + "\n\n")
            
            # Group by category
            delete_by_category = {}
            for action in delete_actions:
                category = action.category
                if category not in delete_by_category:
                    delete_by_category[category] = []
                delete_by_category[category].append(action)
            
            # Summary by category
            log.write("DELETION SUMMARY BY CATEGORY:\n")
            for category, actions in delete_by_category.items():
                log.write(f"  {category}: {len(actions)} emails\n")
            log.write("\n")
            
            # Detailed deletion list
            for category, actions in delete_by_category.items():
                log.write(f"\n{category.upper()} ({len(actions)} emails):\n")
                log.write("-" * 40 + "\n")
                
                for action in actions:
                    email = action.email
                    log.write(f"DELETE: {email.id}\n")
                    log.write(f"  Subject: {email.subject}\n")
                    log.write(f"  From: {email.sender}\n")
                    log.write(f"  Date: {email.date}\n")
                    log.write("  " + "-" * 50 + "\n")
                log.write("\n")
    
    def execute_organization(self, analysis_result: Dict[str, List[EmailAction]]) -> None:
        """Execute the organization (or simulate in dry-run)"""
        
        keep_actions = analysis_result['keep']
        delete_actions = analysis_result['delete']
        
        print(f"\n{'🔍 DRY RUN MODE' if self.dry_run else '📁 ORGANIZING EMAILS'}")
        print(f"Keeping: {len(keep_actions)} emails")
        print(f"Deleting: {len(delete_actions)} emails")
        
        if not self.dry_run:
            # Here you would implement actual Gmail API operations
            # Move keep emails to folders and delete the rest
            print("🚧 Gmail API integration would execute here")
            pass
        
        print(f"\n📝 Detailed report saved to: {self.log_file}")
    
    def print_summary(self, analysis_result: Dict[str, List[EmailAction]]) -> None:
        """Print summary statistics"""
        
        keep_actions = analysis_result['keep']
        delete_actions = analysis_result['delete']
        total = len(keep_actions) + len(delete_actions)
        
        print(f"\n📊 ORGANIZATION SUMMARY")
        print(f"{'='*50}")
        print(f"Total emails analyzed: {total}")
        print(f"Essential emails to keep: {len(keep_actions)} ({len(keep_actions)/total*100:.1f}%)")
        print(f"Emails to delete: {len(delete_actions)} ({len(delete_actions)/total*100:.1f}%)")
        
        # Break down keeps by category
        if keep_actions:
            print(f"\n📌 KEEP BREAKDOWN:")
            keep_by_category = {}
            for action in keep_actions:
                category = action.category
                keep_by_category[category] = keep_by_category.get(category, 0) + 1
            
            for category, count in keep_by_category.items():
                print(f"  {category}: {count} emails")
        
        # Break down deletes by category
        if delete_actions:
            print(f"\n🗑️ DELETE BREAKDOWN:")
            delete_by_category = {}
            for action in delete_actions:
                category = action.category
                delete_by_category[category] = delete_by_category.get(category, 0) + 1
            
            for category, count in sorted(delete_by_category.items(), key=lambda x: x[1], reverse=True):
                print(f"  {category}: {count} emails")
        
        if self.dry_run:
            print(f"\n⚠️  DRY RUN MODE - No emails were actually moved or deleted")
            print(f"🔄 Run with --execute flag to perform actual organization")

def main():
    parser = argparse.ArgumentParser(description='Organize Gmail by keeping only essentials')
    parser.add_argument('data_file', help='Path to email data file (JSON or CSV)')
    parser.add_argument('--execute', action='store_true', help='Actually organize emails (default: dry run)')
    parser.add_argument('--format', choices=['json', 'csv'], help='Data format (auto-detected if not specified)')
    parser.add_argument('--config', default='organizer_config.json', help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.data_file):
        print(f"❌ Error: File '{args.data_file}' not found")
        return
    
    # Auto-detect format
    if not args.format:
        if args.data_file.endswith('.json'):
            args.format = 'json'
        elif args.data_file.endswith('.csv'):
            args.format = 'csv'
        else:
            print("❌ Error: Could not detect file format. Please specify --format")
            return
    
    print(f"🚀 Gmail Essential Organizer")
    print(f"📁 Loading data from: {args.data_file}")
    print(f"📊 Format: {args.format.upper()}")
    print(f"⚙️  Config: {args.config}")
    print(f"🎯 Mode: {'EXECUTION' if args.execute else 'DRY RUN'}")
    
    try:
        # Load email data
        if args.format == 'json':
            emails = EmailDataLoader.load_from_json(args.data_file)
        else:
            emails = EmailDataLoader.load_from_csv(args.data_file)
        
        print(f"✅ Loaded {len(emails)} emails")
        
        # Initialize organizer
        organizer = EmailOrganizer(dry_run=not args.execute, config_path=args.config)
        
        # Analyze emails
        analysis_result = organizer.analyze_emails(emails)
        
        # Generate report
        organizer.generate_report(analysis_result)
        
        # Execute organization
        organizer.execute_organization(analysis_result)
        
        # Print summary
        organizer.print_summary(analysis_result)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

if __name__ == "__main__":
    main()
