#!/usr/bin/env python3
"""
Sample scripts for common Gmail backup scenarios
Usage: python samples.py [scenario_name]
"""

import subprocess
import sys
from datetime import datetime, timedelta

def run_gmail_assistant(query, max_emails, output_dir, format_type="both", organize="date"):
    """Helper function to run gmail_assistant with parameters"""
    cmd = [
        "python", "../src/gmail_assistant.py",
        "--query", query,
        "--max", str(max_emails),
        "--output", output_dir,
        "--format", format_type,
        "--organize", organize
    ]
    
    print(f"🚀 Running: {' '.join(cmd)}")
    return subprocess.run(cmd)

def scenario_unread_cleanup():
    """Download all unread emails for review before cleanup"""
    print("📧 Scenario: Unread Email Backup")
    print("Purpose: Backup all unread emails before mass archiving")
    
    run_gmail_assistant(
        query="is:unread",
        max_emails=2000,
        output_dir="backup_unread",
        format_type="both",
        organize="date"
    )

def scenario_newsletter_archive():
    """Archive all newsletters by sender"""
    print("📰 Scenario: Newsletter Archive")
    print("Purpose: Organize newsletters by sender for easy browsing")
    
    # AI/Tech newsletters
    run_gmail_assistant(
        query="from:(theresanaiforthat.com OR mindstream.news OR futurepedia.io OR newsletter.futurepedia.io)",
        max_emails=1000,
        output_dir="newsletters_ai",
        format_type="markdown",  # Better for reading
        organize="sender"
    )
    
    # Other common newsletters
    run_gmail_assistant(
        query="subject:newsletter OR subject:digest OR from:substack.com",
        max_emails=1000,
        output_dir="newsletters_general",
        format_type="markdown",
        organize="sender"
    )

def scenario_service_notifications():
    """Backup service notifications before deletion"""
    print("🔔 Scenario: Service Notifications Backup")
    print("Purpose: Backup important service emails before cleanup")
    
    services = [
        "namecheap.com",
        "pythonanywhere.com", 
        "zoho.com",
        "apollocover.com",
        "github.com",
        "google.com",
        "microsoft.com",
        "aws.amazon.com"
    ]
    
    query = f"from:({' OR '.join(services)})"
    
    run_gmail_assistant(
        query=query,
        max_emails=1000,
        output_dir="service_notifications",
        format_type="eml",  # Keep original format for records
        organize="sender"
    )

def scenario_important_backup():
    """Backup all important and starred emails"""
    print("⭐ Scenario: Important Email Backup")
    print("Purpose: Secure backup of starred and important emails")
    
    run_gmail_assistant(
        query="is:important OR is:starred",
        max_emails=500,
        output_dir="important_emails",
        format_type="both",
        organize="date"
    )

def scenario_large_emails():
    """Find and backup large emails (usually with attachments)"""
    print("📎 Scenario: Large Email Backup")
    print("Purpose: Backup emails with large attachments")
    
    run_gmail_assistant(
        query="larger:10M",
        max_emails=200,
        output_dir="large_emails",
        format_type="eml",  # EML preserves attachments better
        organize="date"
    )

def scenario_time_period():
    """Backup specific time periods"""
    print("📅 Scenario: Time Period Backup")
    print("Purpose: Backup emails from specific date ranges")
    
    # Last 6 months
    run_gmail_assistant(
        query="newer_than:6m",
        max_emails=2000,
        output_dir="last_6_months",
        format_type="both",
        organize="date"
    )
    
    # Previous year
    run_gmail_assistant(
        query="after:2024/01/01 before:2025/01/01",
        max_emails=3000,
        output_dir="year_2024",
        format_type="both",
        organize="date"
    )

def scenario_ai_content_analysis():
    """Download AI-related content for analysis"""
    print("🤖 Scenario: AI Content Analysis")
    print("Purpose: Collect AI-related emails for trend analysis")
    
    ai_keywords = [
        "artificial intelligence",
        "machine learning",
        "AI",
        "ML",
        "LLM", 
        "ChatGPT",
        "Claude",
        "Gemini",
        "OpenAI",
        "Anthropic"
    ]
    
    # Create query with AI keywords
    keyword_query = " OR ".join([f'subject:"{keyword}"' for keyword in ai_keywords])
    
    run_gmail_assistant(
        query=f"({keyword_query}) AND newer_than:1y",
        max_emails=1000,
        output_dir="ai_content_analysis",
        format_type="markdown",  # Better for text analysis
        organize="date"
    )

def scenario_comprehensive_backup():
    """Complete backup strategy"""
    print("💾 Scenario: Comprehensive Backup")
    print("Purpose: Complete email backup with organization")
    
    # Current year by month
    current_year = datetime.now().year
    for month in range(1, 13):
        if month > datetime.now().month and current_year == datetime.now().year:
            break  # Don't backup future months
            
        month_str = f"{month:02d}"
        query = f"after:{current_year}/{month_str}/01 before:{current_year}/{month_str}/31"
        
        run_gmail_assistant(
            query=query,
            max_emails=1000,
            output_dir=f"backup_{current_year}_{month_str}",
            format_type="both",
            organize="sender"
        )

def scenario_cleanup_preparation():
    """Prepare for inbox cleanup"""
    print("🧹 Scenario: Cleanup Preparation")
    print("Purpose: Backup before mass deletion/archiving")
    
    # Backup promotions before deletion
    run_gmail_assistant(
        query="category:promotions",
        max_emails=1000,
        output_dir="backup_promotions",
        format_type="eml",
        organize="sender"
    )
    
    # Backup old updates
    run_gmail_assistant(
        query="category:updates older_than:3m",
        max_emails=2000,
        output_dir="backup_old_updates",
        format_type="eml",
        organize="sender"
    )
    
    # Backup social notifications
    run_gmail_assistant(
        query="category:social",
        max_emails=500,
        output_dir="backup_social",
        format_type="markdown",
        organize="sender"
    )

def list_scenarios():
    """List all available scenarios"""
    scenarios = {
        "unread": "Backup all unread emails",
        "newsletters": "Archive newsletters by sender", 
        "services": "Backup service notifications",
        "important": "Backup starred and important emails",
        "large": "Backup large emails with attachments",
        "timeperiod": "Backup specific time periods",
        "ai": "Collect AI-related content for analysis",
        "comprehensive": "Complete backup strategy",
        "cleanup": "Prepare for inbox cleanup"
    }
    
    print("📋 Available Scenarios:")
    print("======================")
    for key, description in scenarios.items():
        print(f"{key:15} - {description}")
    print("\nUsage: python samples.py [scenario_name]")

def main():
    if len(sys.argv) < 2:
        list_scenarios()
        return
    
    scenario = sys.argv[1].lower()
    
    scenarios = {
        "unread": scenario_unread_cleanup,
        "newsletters": scenario_newsletter_archive,
        "services": scenario_service_notifications,
        "important": scenario_important_backup,
        "large": scenario_large_emails,
        "timeperiod": scenario_time_period,
        "ai": scenario_ai_content_analysis,
        "comprehensive": scenario_comprehensive_backup,
        "cleanup": scenario_cleanup_preparation
    }
    
    if scenario in scenarios:
        print(f"🎯 Starting scenario: {scenario}")
        print("=" * 50)
        scenarios[scenario]()
        print("✅ Scenario completed!")
    else:
        print(f"❌ Unknown scenario: {scenario}")
        list_scenarios()

if __name__ == "__main__":
    main()
