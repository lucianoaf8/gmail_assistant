#!/bin/bash

# Gmail Complete Cleanup Workflow
# 1. Removes AI newsletters
# 2. Organizes remaining emails (keeps only essentials)

set -e  # Exit on any error

echo "🚀 Gmail Complete Cleanup Workflow"
echo "=================================="
echo ""

# Check if data file provided
if [ $# -eq 0 ]; then
    echo "❌ Error: Please provide email data file"
    echo "Usage: $0 <email_data_file> [--execute]"
    echo ""
    echo "Examples:"
    echo "  $0 emails.json                 # Dry run both steps"
    echo "  $0 emails.json --execute       # Execute both steps"
    echo ""
    exit 1
fi

DATA_FILE="$1"
EXECUTE_FLAG=""

# Check for execute flag
if [ "$2" = "--execute" ]; then
    EXECUTE_FLAG="--delete"
    EXECUTE_ORGANIZER="--execute"
    echo "🎯 MODE: EXECUTION (will actually delete/move emails)"
else
    EXECUTE_ORGANIZER=""
    echo "🎯 MODE: DRY RUN (will only simulate changes)"
fi

echo "📁 Data file: $DATA_FILE"
echo ""

# Validate data file exists
if [ ! -f "$DATA_FILE" ]; then
    echo "❌ Error: File '$DATA_FILE' not found"
    exit 1
fi

# Step 1: Remove AI newsletters
echo "STEP 1: 🤖 Removing AI newsletters..."
echo "======================================"
python3 gmail_ai_newsletter_cleaner.py "$DATA_FILE" $EXECUTE_FLAG

if [ $? -ne 0 ]; then
    echo "❌ Error in AI newsletter cleaning step"
    exit 1
fi

echo ""
echo "✅ Step 1 completed successfully"
echo ""

# Step 2: Organize remaining emails  
echo "STEP 2: 📁 Organizing remaining emails..."
echo "========================================"
python3 gmail_organizer.py "$DATA_FILE" $EXECUTE_ORGANIZER

if [ $? -ne 0 ]; then
    echo "❌ Error in email organization step"
    exit 1
fi

echo ""
echo "✅ Step 2 completed successfully"
echo ""

# Final summary
echo "🎉 COMPLETE CLEANUP FINISHED"
echo "============================="

if [ "$2" = "--execute" ]; then
    echo "✅ Your Gmail has been cleaned and organized!"
    echo "📁 Essential emails moved to organized folders"
    echo "🗑️ Non-essential emails deleted"
else
    echo "📋 Dry run completed - no actual changes made"
    echo "📝 Review the log files to see what would happen:"
    echo "   - gmail_cleanup_*.txt (AI newsletter decisions)"
    echo "   - email_organizer_*.txt (organization decisions)"
    echo ""
    echo "🚀 To execute the actual cleanup:"
    echo "   $0 $DATA_FILE --execute"
fi

echo ""
echo "📊 Check the log files for detailed reports!"
