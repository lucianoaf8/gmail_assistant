#!/usr/bin/env python3
"""
Gmail Safety Validator
Pre-flight checks and safety validation for Gmail deletion operations.
Prevents accidental data loss through comprehensive validation.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

class GmailSafetyValidator:
    def __init__(self):
        self.validation_results = {}
        self.safety_score = 0
        self.warnings = []
        self.blockers = []

    def validate_environment(self) -> Dict[str, bool]:
        """Validate environment setup"""
        print("🔍 Validating environment setup...")

        results = {
            'credentials_exist': False,
            'token_exists': False,
            'dependencies_installed': False,
            'gmail_api_access': False
        }

        # Check credentials.json
        if Path('credentials.json').exists():
            results['credentials_exist'] = True
            print("   ✓ credentials.json found")
        else:
            self.blockers.append("credentials.json not found")
            print("   ❌ credentials.json missing")

        # Check token.json
        if Path('token.json').exists():
            results['token_exists'] = True
            print("   ✓ token.json found")

            # Validate token scopes
            try:
                with open('token.json', 'r') as f:
                    token_data = json.load(f)
                scopes = token_data.get('scopes', [])

                has_modify = any('gmail.modify' in scope for scope in scopes)
                if has_modify:
                    results['gmail_api_access'] = True
                    print("   ✓ Gmail modify scope available")
                else:
                    self.warnings.append("Token may not have gmail.modify scope")
                    print("   ⚠️  Gmail modify scope not confirmed")

            except Exception as e:
                self.warnings.append(f"Could not validate token: {e}")
                print(f"   ⚠️  Token validation failed: {e}")
        else:
            print("   ⚠️  token.json not found (will authenticate on first run)")

        # Check dependencies
        required_packages = ['google_auth', 'google_api_python_client', 'pandas', 'rich']
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if not missing_packages:
            results['dependencies_installed'] = True
            print("   ✓ All required dependencies installed")
        else:
            self.blockers.append(f"Missing packages: {missing_packages}")
            print(f"   ❌ Missing packages: {missing_packages}")

        return results

    def validate_query_safety(self, query: str) -> Dict[str, any]:
        """Validate safety of a Gmail search query"""
        print(f"🔍 Validating query safety: '{query}'")

        results = {
            'query': query,
            'risk_level': 'UNKNOWN',
            'estimated_scope': 'UNKNOWN',
            'safety_concerns': [],
            'recommendations': []
        }

        # Analyze query components
        query_lower = query.lower()

        # Risk assessment
        high_risk_patterns = [
            ('', 'ALL EMAILS - EXTREMELY HIGH RISK'),
            ('is:read', 'ALL READ EMAILS - HIGH RISK'),
            ('has:attachment', 'ALL EMAILS WITH ATTACHMENTS - HIGH RISK'),
            ('-has:attachment', 'ALL EMAILS WITHOUT ATTACHMENTS - HIGH RISK')
        ]

        medium_risk_patterns = [
            ('is:unread', 'ALL UNREAD EMAILS - MEDIUM RISK'),
            ('older_than:1y', 'EMAILS OLDER THAN 1 YEAR - MEDIUM RISK'),
            ('larger:10m', 'LARGE EMAILS >10MB - MEDIUM RISK')
        ]

        low_risk_patterns = [
            ('is:unread older_than:30d', 'OLD UNREAD EMAILS - LOW RISK'),
            ('is:unread larger:5m', 'LARGE UNREAD EMAILS - LOW RISK'),
            ('from:', 'SPECIFIC SENDER - LOW RISK'),
            ('subject:', 'SPECIFIC SUBJECT - LOW RISK'),
            ('(payment or invoice)', 'FINANCIAL CATEGORY - LOW RISK')
        ]

        # Determine risk level
        results['risk_level'] = 'LOW'

        for pattern, description in high_risk_patterns:
            if pattern == query_lower or (pattern and pattern in query_lower):
                results['risk_level'] = 'HIGH'
                results['safety_concerns'].append(description)
                break

        if results['risk_level'] != 'HIGH':
            for pattern, description in medium_risk_patterns:
                if pattern in query_lower:
                    results['risk_level'] = 'MEDIUM'
                    results['safety_concerns'].append(description)
                    break

        if results['risk_level'] not in ['HIGH', 'MEDIUM']:
            for pattern, description in low_risk_patterns:
                if pattern in query_lower:
                    results['safety_concerns'].append(description)
                    break

        # Generate recommendations
        if results['risk_level'] == 'HIGH':
            results['recommendations'].extend([
                "STRONGLY RECOMMEND: Backup all emails before deletion",
                "STRONGLY RECOMMEND: Test with --max-delete 10 first",
                "STRONGLY RECOMMEND: Use more specific query to reduce scope"
            ])
        elif results['risk_level'] == 'MEDIUM':
            results['recommendations'].extend([
                "RECOMMEND: Backup important emails before deletion",
                "RECOMMEND: Test with --dry-run first",
                "RECOMMEND: Consider using --max-delete for testing"
            ])
        else:
            results['recommendations'].extend([
                "RECOMMEND: Always test with --dry-run first",
                "CONSIDER: Backup if emails might be important"
            ])

        # Safety score calculation
        if results['risk_level'] == 'HIGH':
            self.safety_score = max(0, self.safety_score - 30)
        elif results['risk_level'] == 'MEDIUM':
            self.safety_score = max(0, self.safety_score - 15)
        else:
            self.safety_score = min(100, self.safety_score + 5)

        return results

    def test_gmail_connection(self) -> Dict[str, any]:
        """Test Gmail API connection and get basic stats"""
        print("🔗 Testing Gmail API connection...")

        results = {
            'connected': False,
            'email_address': None,
            'total_emails': 0,
            'unread_emails': 0,
            'connection_error': None
        }

        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from scripts.gmail_deleter import GmailDeleter
            deleter = GmailDeleter()

            # Get basic counts
            unread_count = deleter.get_email_count("is:unread")
            total_count = deleter.get_email_count("")

            # Get profile info
            profile = deleter.service.users().getProfile(userId='me').execute()
            email_address = profile.get('emailAddress', 'Unknown')

            results.update({
                'connected': True,
                'email_address': email_address,
                'total_emails': total_count,
                'unread_emails': unread_count
            })

            print(f"   ✅ Connected to: {email_address}")
            print(f"   📧 Total emails: {total_count:,}")
            print(f"   📨 Unread emails: {unread_count:,}")

            self.safety_score += 20

        except Exception as e:
            results['connection_error'] = str(e)
            self.blockers.append(f"Gmail connection failed: {e}")
            print(f"   ❌ Connection failed: {e}")

        return results

    def estimate_deletion_impact(self, query: str) -> Dict[str, any]:
        """Estimate the impact of a deletion query"""
        print(f"📊 Estimating deletion impact for: '{query}'")

        results = {
            'query': query,
            'estimated_count': 0,
            'percentage_of_total': 0,
            'percentage_of_unread': 0,
            'impact_level': 'UNKNOWN',
            'time_estimate': 'UNKNOWN'
        }

        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from scripts.gmail_deleter import GmailDeleter
            deleter = GmailDeleter()

            # Get counts
            deletion_count = deleter.get_email_count(query)
            total_count = deleter.get_email_count("")
            unread_count = deleter.get_email_count("is:unread")

            results['estimated_count'] = deletion_count

            if total_count > 0:
                results['percentage_of_total'] = (deletion_count / total_count) * 100

            if unread_count > 0 and 'unread' in query.lower():
                results['percentage_of_unread'] = (deletion_count / unread_count) * 100

            # Impact assessment
            if deletion_count == 0:
                results['impact_level'] = 'NONE'
            elif deletion_count < 100:
                results['impact_level'] = 'LOW'
            elif deletion_count < 1000:
                results['impact_level'] = 'MEDIUM'
            else:
                results['impact_level'] = 'HIGH'

            # Time estimation (rough)
            if deletion_count > 0:
                # Estimate ~100 emails per batch, ~0.1s per batch + processing time
                estimated_minutes = max(1, (deletion_count / 100) * 0.1 + (deletion_count / 1000))
                if estimated_minutes < 1:
                    results['time_estimate'] = "< 1 minute"
                elif estimated_minutes < 60:
                    results['time_estimate'] = f"~{int(estimated_minutes)} minutes"
                else:
                    results['time_estimate'] = f"~{int(estimated_minutes/60)} hours"

            print(f"   📈 Estimated deletions: {deletion_count:,}")
            print(f"   📊 Percentage of total: {results['percentage_of_total']:.1f}%")
            if 'unread' in query.lower():
                print(f"   📨 Percentage of unread: {results['percentage_of_unread']:.1f}%")
            print(f"   ⏱️  Estimated time: {results['time_estimate']}")
            print(f"   📊 Impact level: {results['impact_level']}")

            # Adjust safety score based on impact
            if results['impact_level'] == 'HIGH':
                self.safety_score = max(0, self.safety_score - 25)
            elif results['impact_level'] == 'MEDIUM':
                self.safety_score = max(0, self.safety_score - 10)

        except Exception as e:
            print(f"   ❌ Impact estimation failed: {e}")
            results['error'] = str(e)

        return results

    def validate_backup_status(self) -> Dict[str, any]:
        """Check if backups exist"""
        print("💾 Checking backup status...")

        results = {
            'backup_folders_found': [],
            'backup_recommendation': 'NONE'
        }

        # Look for common backup patterns
        backup_patterns = [
            'gmail_backup*',
            'backup*',
            '*_backup',
            'downloads/*gmail*',
            'takeout*'
        ]

        backup_folders = []
        for pattern in backup_patterns:
            import glob
            matches = glob.glob(pattern)
            backup_folders.extend([f for f in matches if os.path.isdir(f)])

        results['backup_folders_found'] = backup_folders

        if backup_folders:
            print(f"   ✓ Found backup folders: {backup_folders}")
            results['backup_recommendation'] = 'EXISTING_BACKUPS_FOUND'
            self.safety_score += 15
        else:
            print("   ⚠️  No backup folders found")
            results['backup_recommendation'] = 'CREATE_BACKUP_FIRST'
            self.warnings.append("No existing backups found - consider creating backup first")

        return results

    def generate_safety_report(self) -> Dict[str, any]:
        """Generate comprehensive safety report"""
        print("\n" + "="*60)
        print("🛡️  GMAIL DELETION SAFETY REPORT")
        print("="*60)

        # Calculate final safety score
        if self.blockers:
            self.safety_score = 0
        elif self.warnings:
            self.safety_score = max(0, self.safety_score - len(self.warnings) * 5)

        safety_level = 'UNSAFE'
        if self.safety_score >= 80:
            safety_level = 'SAFE'
        elif self.safety_score >= 60:
            safety_level = 'MODERATE'
        elif self.safety_score >= 40:
            safety_level = 'RISKY'

        report = {
            'safety_score': self.safety_score,
            'safety_level': safety_level,
            'blockers': self.blockers,
            'warnings': self.warnings,
            'validation_results': self.validation_results
        }

        # Display report
        safety_emoji = {
            'SAFE': '🟢',
            'MODERATE': '🟡',
            'RISKY': '🟠',
            'UNSAFE': '🔴'
        }

        print(f"\n📊 SAFETY ASSESSMENT")
        print(f"   Safety Score: {self.safety_score}/100")
        print(f"   Safety Level: {safety_emoji[safety_level]} {safety_level}")

        if self.blockers:
            print(f"\n🚨 BLOCKERS (Must fix before proceeding):")
            for blocker in self.blockers:
                print(f"   • {blocker}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")

        if safety_level == 'UNSAFE':
            print("   🔴 DO NOT PROCEED - Fix blockers first")
            print("   📋 Run: python gmail_setup_integrated.py")
        elif safety_level == 'RISKY':
            print("   🟠 PROCEED WITH EXTREME CAUTION")
            print("   📋 MANDATORY: Create backup first")
            print("   📋 MANDATORY: Test with --dry-run")
            print("   📋 MANDATORY: Test with --max-delete 10")
        elif safety_level == 'MODERATE':
            print("   🟡 PROCEED WITH CAUTION")
            print("   📋 RECOMMENDED: Create backup first")
            print("   📋 REQUIRED: Test with --dry-run")
        else:
            print("   🟢 SAFE TO PROCEED")
            print("   📋 RECOMMENDED: Test with --dry-run first")

        return report

def main():
    parser = argparse.ArgumentParser(description='Gmail Deletion Safety Validator')
    parser.add_argument('--query', type=str, help='Gmail query to validate')
    parser.add_argument('--command', type=str, help='Full command to validate')
    parser.add_argument('--quick', action='store_true', help='Quick validation (skip connection test)')

    args = parser.parse_args()

    validator = GmailSafetyValidator()

    print("🛡️  Gmail Deletion Safety Validator")
    print("=" * 50)

    # Step 1: Environment validation
    env_results = validator.validate_environment()
    validator.validation_results['environment'] = env_results

    # Step 2: Connection test (unless quick mode)
    if not args.quick and not validator.blockers:
        connection_results = validator.test_gmail_connection()
        validator.validation_results['connection'] = connection_results

    # Step 3: Query validation
    if args.query:
        query_results = validator.validate_query_safety(args.query)
        validator.validation_results['query'] = query_results

        # Step 4: Impact estimation
        if not validator.blockers:
            impact_results = validator.estimate_deletion_impact(args.query)
            validator.validation_results['impact'] = impact_results

    # Step 5: Backup status
    backup_results = validator.validate_backup_status()
    validator.validation_results['backup'] = backup_results

    # Step 6: Generate final report
    safety_report = validator.generate_safety_report()

    # Step 7: Command-specific advice
    if args.command:
        print(f"\n🔧 COMMAND ANALYSIS")
        print(f"Command: {args.command}")

        if '--dry-run' in args.command:
            print("   ✅ Dry-run detected - safe for testing")
        else:
            print("   ⚠️  No dry-run detected - this will actually delete emails")

        if '--max-delete' in args.command:
            print("   ✅ Max-delete limit detected - good for testing")
        else:
            print("   ⚠️  No deletion limit - could delete many emails")

    print(f"\n🎯 NEXT STEPS:")

    if validator.blockers:
        print("   1. Fix all blockers listed above")
        print("   2. Re-run validation")
    else:
        print("   1. Create backup if recommended")
        print("   2. Always test with --dry-run first")
        print("   3. Start with small limits (--max-delete 10)")
        print("   4. Monitor progress and results")

    return safety_report

if __name__ == "__main__":
    main()