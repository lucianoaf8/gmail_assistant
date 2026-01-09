#!/usr/bin/env python3
"""
Integrated Gmail Setup & Operations Manager
Combines Gmail fetching and deletion capabilities with unified setup and validation.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import argparse

def check_all_dependencies():
    """Check if all required packages are installed (fetcher + deletion)"""
    print("🔍 Checking all dependencies...")

    required_packages = [
        # Core Gmail API
        'google-auth', 'google-auth-oauthlib', 'google-auth-httplib2', 'google-api-python-client',
        # HTML processing
        'html2text',
        # Data processing and deletion
        'pandas', 'rich', 'pyarrow'
    ]

    missing = []
    installed = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            installed.append(package)
            print(f"   ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"   ❌ {package} - MISSING")

    print(f"\n📊 Dependency Status:")
    print(f"   Installed: {len(installed)}/{len(required_packages)}")
    print(f"   Missing: {len(missing)}")

    if missing:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False

    print("✅ All dependencies installed")
    return True

def check_gmail_credentials():
    """Check for Gmail API credentials"""
    print("\n🔑 Checking Gmail API credentials...")

    creds_file = Path('credentials.json')
    token_file = Path('token.json')

    if not creds_file.exists():
        print("❌ credentials.json not found")
        print("\n📋 To get Gmail API credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create/select a project")
        print("3. Enable Gmail API")
        print("4. Go to APIs & Services > Credentials")
        print("5. Create OAuth 2.0 Client ID (Desktop application)")
        print("6. Download JSON and save as 'credentials.json'")
        print("\n🔐 Required scopes:")
        print("   • https://www.googleapis.com/auth/gmail.readonly (for fetching)")
        print("   • https://www.googleapis.com/auth/gmail.modify (for deletion)")
        return False

    print("   ✓ credentials.json found")

    if token_file.exists():
        print("   ✓ token.json found (already authenticated)")

        # Check token scopes
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            scopes = token_data.get('scopes', [])

            has_readonly = any('gmail.readonly' in scope for scope in scopes)
            has_modify = any('gmail.modify' in scope for scope in scopes)

            print(f"   📋 Token scopes:")
            print(f"      Gmail read: {'✓' if has_readonly else '❌'}")
            print(f"      Gmail modify: {'✓' if has_modify else '❌'}")

            if not (has_readonly or has_modify):
                print("   ⚠️  Token may need refresh for required scopes")

        except Exception as e:
            print(f"   ⚠️  Could not read token scopes: {e}")
    else:
        print("   ⚠️  token.json not found (will authenticate on first run)")

    return True

def test_gmail_operations():
    """Test both fetching and deletion capabilities"""
    print("\n🔗 Testing Gmail API operations...")

    # Test basic fetcher functionality
    print("   📥 Testing Gmail fetcher...")
    try:
        from gmail_assistant import GmailFetcher
        fetcher = GmailFetcher()

        # Test basic connection without downloading
        service = fetcher._get_gmail_service()
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        total_messages = profile.get('messagesTotal', 0)

        print(f"      ✅ Fetcher connected to: {email_address}")
        print(f"      📧 Total messages: {total_messages:,}")

    except Exception as e:
        print(f"      ❌ Fetcher test failed: {e}")
        return False

    # Test deletion functionality
    print("   🗑️  Testing Gmail deleter...")
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from scripts.gmail_deleter import GmailDeleter
        deleter = GmailDeleter()

        # Test basic connection and counts
        unread_count = deleter.get_email_count("is:unread")
        total_count = deleter.get_email_count("")

        print(f"      ✅ Deleter connected successfully")
        print(f"      📨 Unread emails: {unread_count:,}")
        print(f"      📧 Total emails: {total_count:,}")

        return True, {
            'email_address': email_address,
            'total_messages': total_messages,
            'unread_count': unread_count,
            'total_count': total_count
        }

    except Exception as e:
        print(f"      ❌ Deleter test failed: {e}")
        return False, {}

def analyze_gmail_state():
    """Comprehensive Gmail state analysis"""
    print("\n📊 Analyzing Gmail state...")

    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from scripts.gmail_deleter import GmailDeleter
        deleter = GmailDeleter()

        # Comprehensive categories
        categories = {
            'Total emails': '',
            'Unread emails': 'is:unread',
            'Read emails': 'is:read',
            'Starred emails': 'is:starred',
            'Important emails': 'is:important',
            'Old emails (>1 year)': 'older_than:1y',
            'Large emails (>10MB)': 'larger:10M',
            'Medium emails (1-10MB)': 'larger:1M smaller:10M',
            'Financial emails': 'payment OR invoice OR bill OR receipt OR bank OR card',
            'Notifications': 'notification OR alert OR backup OR report OR reminder',
            'Marketing emails': 'unsubscribe OR newsletter OR marketing OR offer OR deal',
            'Social emails': 'social OR friend OR follow OR linkedin OR facebook',
            'Emails with attachments': 'has:attachment',
            'Emails without attachments': '-has:attachment'
        }

        print("\n📈 Comprehensive email breakdown:")
        results = {}
        for category, query in categories.items():
            count = deleter.get_email_count(query)
            results[category] = count
            print(f"   {category:<30}: {count:>8,}")

        # Deletion opportunities
        unread_count = results.get('Unread emails', 0)
        if unread_count > 0:
            print(f"\n💡 Deletion opportunities analysis:")

            opportunities = {
                'Old unread (>30 days)': 'is:unread older_than:30d',
                'Old unread (>90 days)': 'is:unread older_than:90d',
                'Large unread (>1MB)': 'is:unread larger:1M',
                'Large unread (>5MB)': 'is:unread larger:5M',
                'Notification unread': 'is:unread (notification OR alert OR backup)',
                'Marketing unread': 'is:unread (unsubscribe OR newsletter OR marketing)',
                'Financial unread': 'is:unread (payment OR invoice OR bill OR receipt)',
                'Social unread': 'is:unread (social OR friend OR follow)'
            }

            for category, query in opportunities.items():
                count = deleter.get_email_count(query)
                if count > 0:
                    percentage = (count / unread_count) * 100
                    print(f"   {category:<25}: {count:>6,} ({percentage:>5.1f}%)")

        return results

    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        return {}

def create_comprehensive_plan(email_stats):
    """Create comprehensive deletion and management plan"""
    unread = email_stats.get('Unread emails', 0)
    total = email_stats.get('Total emails', 0)

    if unread == 0:
        print("\n✅ No unread emails - inbox already clean!")
        print("\n📋 Available operations:")
        print("   • Backup emails: python gmail_assistant.py --query 'is:starred' --max 1000")
        print("   • Backup important: python gmail_assistant.py --query 'is:important' --max 1000")
        return

    print(f"\n🎯 Comprehensive deletion strategies:")
    print(f"   Current unread: {unread:,} emails")
    print(f"   Total emails: {total:,} emails")

    strategies = [
        {
            'name': '🚀 Fresh Start (Delete All Unread)',
            'risk': 'HIGH',
            'command': 'python fresh_start.py',
            'test_command': 'python clean_unread_inbox.py --dry-run',
            'impact': f'Deletes all {unread:,} unread emails',
            'recovery': 'Gmail Trash (30 days)'
        },
        {
            'name': '🛡️ Conservative (Keep Recent)',
            'risk': 'MEDIUM',
            'command': 'python clean_unread_inbox.py --keep-recent 7',
            'test_command': 'python clean_unread_inbox.py --keep-recent 7 --dry-run',
            'impact': 'Deletes unread emails older than 7 days',
            'recovery': 'Gmail Trash (30 days)'
        },
        {
            'name': '🎯 Category-Based (Financial)',
            'risk': 'LOW',
            'command': 'python gmail_deleter.py --query "is:unread (payment OR invoice OR bill)"',
            'test_command': 'python gmail_deleter.py --query "is:unread (payment OR invoice OR bill)" --dry-run',
            'impact': 'Deletes only financial unread emails',
            'recovery': 'Gmail Trash (30 days)'
        },
        {
            'name': '📅 Time-Based (Old Emails)',
            'risk': 'MEDIUM',
            'command': 'python gmail_deleter.py --query "is:unread older_than:30d"',
            'test_command': 'python gmail_deleter.py --query "is:unread older_than:30d" --dry-run',
            'impact': 'Deletes unread emails older than 30 days',
            'recovery': 'Gmail Trash (30 days)'
        },
        {
            'name': '📦 Size-Based (Large Emails)',
            'risk': 'LOW',
            'command': 'python gmail_deleter.py --query "is:unread larger:5M"',
            'test_command': 'python gmail_deleter.py --query "is:unread larger:5M" --dry-run',
            'impact': 'Deletes large unread emails (>5MB)',
            'recovery': 'Gmail Trash (30 days)'
        }
    ]

    for i, strategy in enumerate(strategies, 1):
        risk_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[strategy['risk']]
        print(f"\n   {i}. {strategy['name']} {risk_emoji} {strategy['risk']}")
        print(f"      Test: {strategy['test_command']}")
        print(f"      Execute: {strategy['command']}")
        print(f"      Impact: {strategy['impact']}")
        print(f"      Recovery: {strategy['recovery']}")

def show_safety_checklist():
    """Display safety checklist before operations"""
    print(f"\n🔒 SAFETY CHECKLIST")
    print(f"=" * 50)
    print(f"Before running ANY deletion commands:")
    print(f"")
    print(f"1. ✅ Backup important emails first:")
    print(f"   python gmail_assistant.py --query 'is:starred OR is:important' --max 1000")
    print(f"")
    print(f"2. ✅ Always test with --dry-run first:")
    print(f"   python clean_unread_inbox.py --dry-run")
    print(f"")
    print(f"3. ✅ Start small if unsure:")
    print(f"   python gmail_deleter.py --query 'is:unread' --max-delete 10 --dry-run")
    print(f"")
    print(f"4. ✅ Understand recovery options:")
    print(f"   • Deleted emails go to Gmail Trash")
    print(f"   • Recoverable for 30 days")
    print(f"   • Access via Gmail web interface")
    print(f"")
    print(f"5. ✅ Have credentials.json ready")
    print(f"6. ✅ Ensure stable internet connection")
    print(f"7. ✅ Review deletion counts before confirming")

def main():
    parser = argparse.ArgumentParser(description='Integrated Gmail Setup & Operations Manager')
    parser.add_argument('--setup-only', action='store_true', help='Only run setup validation, no analysis')
    parser.add_argument('--analysis-only', action='store_true', help='Only run analysis, skip setup checks')
    parser.add_argument('--safety-checklist', action='store_true', help='Show safety checklist')

    args = parser.parse_args()

    print("🚀 Gmail Fetcher & Deletion - Integrated Setup")
    print("=" * 60)

    if args.safety_checklist:
        show_safety_checklist()
        return

    setup_success = True

    if not args.analysis_only:
        # Step 1: Check dependencies
        if not check_all_dependencies():
            print("\n❌ Setup incomplete - install missing dependencies first")
            setup_success = False

        # Step 2: Check credentials
        if not check_gmail_credentials():
            print("\n❌ Setup incomplete - add Gmail API credentials")
            setup_success = False

        # Step 3: Test operations
        if setup_success:
            connected, stats = test_gmail_operations()
            if not connected:
                print("\n❌ Setup incomplete - fix Gmail API connection")
                setup_success = False

    if args.setup_only:
        if setup_success:
            print(f"\n✅ Setup validation complete!")
        return

    # Step 4: Analyze current state (if setup successful or analysis-only)
    if setup_success or args.analysis_only:
        email_stats = analyze_gmail_state()

        # Step 5: Create comprehensive plan
        if email_stats:
            create_comprehensive_plan(email_stats)

    # Final recommendations
    if setup_success:
        print(f"\n✅ Complete setup and analysis finished!")
        print(f"\n🎯 Recommended next steps:")
        print(f"   1. Review safety checklist: python gmail_setup_integrated.py --safety-checklist")
        print(f"   2. Choose a deletion strategy from above")
        print(f"   3. ALWAYS test with --dry-run first")
        print(f"   4. Backup important emails before deletion")
        print(f"\n📚 Documentation:")
        print(f"   • Fetcher guide: see CLAUDE.md")
        print(f"   • Deletion guide: see _to_implement/gmail_emails_deletion/GMAIL_DELETION_GUIDE.md")

if __name__ == "__main__":
    main()