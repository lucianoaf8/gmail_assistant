#!/usr/bin/env python3
"""
Gmail AI Newsletter Cleaner - Example Usage
Generates sample email data and demonstrates the cleaner functionality
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from gmail_ai_newsletter_cleaner import EmailData, GmailCleaner

def generate_sample_emails():
    """Generate sample email data for testing"""
    
    # AI Newsletter samples
    ai_newsletters = [
        {
            "id": "ai_001",
            "subject": "The Batch: AI Weekly Newsletter",
            "sender": "noreply@deeplearning.ai",
            "date": "2024-01-15",
            "snippet": "This week in AI: GPT-4 updates, new research findings. Unsubscribe here."
        },
        {
            "id": "ai_002", 
            "subject": "Import AI Newsletter #342",
            "sender": "jack@importai.substack.com",
            "date": "2024-01-14",
            "snippet": "Neural networks breakthrough, machine learning trends. Manage preferences."
        },
        {
            "id": "ai_003",
            "subject": "AI Weekly Digest - OpenAI Updates",
            "sender": "newsletter@openai.com", 
            "date": "2024-01-13",
            "snippet": "Latest ChatGPT improvements and API changes. Click to unsubscribe."
        },
        {
            "id": "ai_004",
            "subject": "Anthropic Claude Research Update",
            "sender": "research@anthropic.com",
            "date": "2024-01-12", 
            "snippet": "Constitutional AI developments and safety research. Update email preferences."
        },
        {
            "id": "ai_005",
            "subject": "Towards Data Science Daily",
            "sender": "medium-daily@medium.com",
            "date": "2024-01-11",
            "snippet": "Deep learning tutorials and AI insights. Unsubscribe from this list."
        },
        {
            "id": "ai_006",
            "subject": "The Sequence - ML Engineering",
            "sender": "noreply@thesequence.substack.com", 
            "date": "2024-01-10",
            "snippet": "Machine learning infrastructure and transformer models. Manage subscription."
        },
        {
            "id": "ai_007",
            "subject": "Hugging Face Newsletter",
            "sender": "newsletter@huggingface.co",
            "date": "2024-01-09",
            "snippet": "New models and datasets on the Hub. Click here to opt out."
        },
        {
            "id": "ai_008",
            "subject": "AI News from VentureBeat",
            "sender": "newsletter@venturebeat.com",
            "date": "2024-01-08", 
            "snippet": "Generative AI startups and industry updates. Unsubscribe instantly."
        }
    ]
    
    # Regular emails (not AI newsletters)
    regular_emails = [
        {
            "id": "reg_001",
            "subject": "Meeting reminder: Team standup",
            "sender": "sarah@company.com",
            "date": "2024-01-15",
            "snippet": "Don't forget our weekly team meeting at 10 AM."
        },
        {
            "id": "reg_002", 
            "subject": "Invoice #1234 from AWS",
            "sender": "billing@aws.amazon.com",
            "date": "2024-01-14",
            "snippet": "Your monthly AWS bill is ready for review."
        },
        {
            "id": "reg_003",
            "subject": "Flight confirmation",
            "sender": "confirmations@airline.com", 
            "date": "2024-01-13",
            "snippet": "Your flight booking has been confirmed."
        },
        {
            "id": "reg_004",
            "subject": "Weekend plans?",
            "sender": "mom@family.com",
            "date": "2024-01-12",
            "snippet": "Hi honey, what are your plans for this weekend?"
        },
        {
            "id": "reg_005",
            "subject": "GitHub security alert",
            "sender": "noreply@github.com",
            "date": "2024-01-11", 
            "snippet": "We found a potential security vulnerability in your repository."
        },
        {
            "id": "reg_006",
            "subject": "Job application update",
            "sender": "hr@techcompany.com",
            "date": "2024-01-10",
            "snippet": "Thank you for your application. We'll be in touch soon."
        },
        {
            "id": "reg_007",
            "subject": "Bank statement available",
            "sender": "statements@bank.com", 
            "date": "2024-01-09",
            "snippet": "Your monthly bank statement is now available online."
        },
        {
            "id": "reg_008",
            "subject": "Package delivery update",
            "sender": "tracking@fedex.com",
            "date": "2024-01-08",
            "snippet": "Your package will be delivered tomorrow between 9-5 PM."
        }
    ]
    
    # Combine all emails
    all_emails = ai_newsletters + regular_emails
    
    return all_emails

def create_sample_data_files():
    """Create sample JSON and CSV files"""
    
    emails = generate_sample_emails()
    
    # Create JSON file
    json_file = "sample_emails.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(emails, f, indent=2)
    
    # Create CSV file
    csv_file = "sample_emails.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("id,subject,sender,date,snippet\n")
        for email in emails:
            # Escape commas and quotes in CSV
            subject = email['subject'].replace('"', '""')
            sender = email['sender'].replace('"', '""') 
            snippet = email['snippet'].replace('"', '""')
            
            f.write(f'"{email["id"]}","{subject}","{sender}","{email["date"]}","{snippet}"\n')
    
    print(f"✅ Created sample data files:")
    print(f"   📄 {json_file} ({len(emails)} emails)")
    print(f"   📄 {csv_file} ({len(emails)} emails)")
    
    return json_file, csv_file

def run_example():
    """Run example cleanup on sample data"""
    
    print("🚀 Gmail AI Newsletter Cleaner - Example")
    print("=" * 50)
    
    # Create sample data
    json_file, csv_file = create_sample_data_files()
    
    # Load and analyze JSON data
    print(f"\n📊 Analyzing {json_file}...")
    
    # Initialize cleaner in dry-run mode
    cleaner = GmailCleaner(dry_run=True)
    
    # Load emails from JSON
    from gmail_ai_newsletter_cleaner import EmailDataLoader
    emails = EmailDataLoader.load_from_json(json_file)
    
    # Analyze emails
    analysis_result = cleaner.analyze_emails(emails)
    
    # Show results
    cleaner.delete_ai_newsletters(analysis_result['ai_newsletters'])
    cleaner.generate_summary(analysis_result)
    
    print(f"\n📋 Example completed. Check the log file for details.")
    print(f"💡 To run with your actual data:")
    print(f"   python gmail_ai_newsletter_cleaner.py your_emails.json")
    print(f"   python gmail_api_client.py --credentials credentials.json")

if __name__ == "__main__":
    run_example()
