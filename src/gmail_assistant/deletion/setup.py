#!/usr/bin/env python3
"""
Gmail Deletion Setup & Validation Script
Helps set up and validate your Gmail API connection before bulk deletion.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'google-auth', 'google-auth-oauthlib', 'google-api-python-client',
        'pandas', 'tqdm', 'pyarrow'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies installed")
    return True

def check_credentials():
    """Check for Gmail API credentials"""
    print("\n🔑 Checking Gmail API credentials...")
    
    creds_file = Path('credentials.json')
    token_file = Path('token.json')
    
    if not creds_file.exists():
        print("❌ credentials.json not found")
        print("\n📋 To get credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create/select a project")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download as 'credentials.json'")
        return False
    
    print("   ✓ credentials.json found")
    
    if token_file.exists():
        print("   ✓ token.json found (already authenticated)")
    else:
        print("   ⚠️  token.json not found (will authenticate on first run)")
    
    return True

def test_gmail_connection():
    """Test Gmail API connection"""
    print("\n🔗 Testing Gmail API connection...")
    
    try:
        from gmail_deleter import GmailDeleter
        
        deleter = GmailDeleter()
        
        # Test basic connection
        unread_count = deleter.get_email_count("is:unread")
        total_count = deleter.get_email_count("")
        
        print(f"   ✅ Connection successful!")
        print(f"   📧 Total emails: {total_count:,}")
        print(f"   📨 Unread emails: {unread_count:,}")
        
        return True, {'total': total_count, 'unread': unread_count}
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False, {}

def analyze_current_state():
    """Analyze current Gmail state for deletion planning"""
    print("\n📊 Analyzing current Gmail state...")
    
    try:
        from gmail_deleter import GmailDeleter
        deleter = GmailDeleter()
        
        # Different email categories
        categories = {
            'Total emails': '',
            'Unread emails': 'is:unread',
            'Old emails (>1 year)': 'older_than:1y',
            'Large emails (>10MB)': 'larger:10M',
            'Financial emails': 'payment OR invoice OR bill OR receipt OR bank',
            'Notifications': 'notification OR alert OR backup OR report',
            'Marketing emails': 'unsubscribe OR newsletter OR marketing',
            'Social emails': 'social OR friend OR follow',
            'Emails with attachments': 'has:attachment'
        }
        
        print("\n📈 Email breakdown:")
        results = {}
        for category, query in categories.items():
            count = deleter.get_email_count(query)
            results[category] = count
            print(f"   {category:<25}: {count:>8,}")
        
        # Top senders analysis (if we have unread emails)
        unread_count = results.get('Unread emails', 0)
        if unread_count > 0:
            print(f"\n💡 Deletion opportunities:")
            
            # Estimate deletions by category
            old_unread = deleter.get_email_count('is:unread older_than:30d')
            large_unread = deleter.get_email_count('is:unread larger:1M')
            notification_unread = deleter.get_email_count('is:unread (notification OR alert OR backup)')
            
            if old_unread > 0:
                print(f"   📅 Old unread (>30 days): {old_unread:,} emails")
            if large_unread > 0:
                print(f"   📦 Large unread (>1MB): {large_unread:,} emails")
            if notification_unread > 0:
                print(f"   🔔 Notification unread: {notification_unread:,} emails")
        
        return results
        
    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        return {}

def create_deletion_plan(email_stats):
    """Suggest deletion strategies based on current state"""
    unread = email_stats.get('Unread emails', 0)
    total = email_stats.get('Total emails', 0)
    
    if unread == 0:
        print("\n✅ No unread emails - inbox already clean!")
        return
    
    print(f"\n🎯 Suggested deletion strategies:")
    print(f"   Current unread: {unread:,} emails")
    
    strategies = [
        {
            'name': 'Fresh Start (Delete All Unread)',
            'command': 'python clean_unread_inbox.py --dry-run',
            'impact': f'Deletes all {unread:,} unread emails'
        },
        {
            'name': 'Conservative (Keep Recent)',
            'command': 'python clean_unread_inbox.py --keep-recent 7 --dry-run',
            'impact': 'Deletes unread emails older than 7 days'
        },
        {
            'name': 'Category-Based (Financial Only)',
            'command': 'python gmail_deleter.py --query "is:unread (payment OR invoice OR bill)" --dry-run',
            'impact': 'Deletes only financial unread emails'
        }
    ]
    
    for i, strategy in enumerate(strategies, 1):
        print(f"\n   {i}. {strategy['name']}")
        print(f"      Command: {strategy['command']}")
        print(f"      Impact: {strategy['impact']}")

def main():
    print("🚀 Gmail Deletion Setup & Validation")
    print("=" * 50)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Setup incomplete - install missing dependencies first")
        return
    
    # Step 2: Check credentials
    if not check_credentials():
        print("\n❌ Setup incomplete - add Gmail API credentials")
        return
    
    # Step 3: Test connection
    connected, stats = test_gmail_connection()
    if not connected:
        print("\n❌ Setup incomplete - fix Gmail API connection")
        return
    
    # Step 4: Analyze current state
    email_stats = analyze_current_state()
    
    # Step 5: Create deletion plan
    if email_stats:
        create_deletion_plan(email_stats)
    
    print(f"\n✅ Setup complete!")
    print(f"\n🎯 Next steps:")
    print(f"   1. Choose a deletion strategy above")
    print(f"   2. Run with --dry-run first to test")
    print(f"   3. Execute the actual deletion")
    print(f"\n📚 For detailed guide: cat GMAIL_DELETION_GUIDE.md")

if __name__ == "__main__":
    main()
