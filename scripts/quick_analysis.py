#!/usr/bin/env python3
"""
Quick Email Analysis Script
Convenience wrapper for running daily email analysis with the integrated Gmail fetcher.
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def main():
    """Main entry point for quick analysis"""

    # Get project root
    project_root = Path(__file__).parent.parent
    main_script = project_root / "main.py"

    if not main_script.exists():
        print("❌ Error: main.py not found")
        sys.exit(1)

    # Change to project directory
    os.chdir(project_root)

    # Parse simple arguments
    if len(sys.argv) < 2:
        print("Quick Email Analysis")
        print("Usage:")
        print("  python scripts/quick_analysis.py yesterday    # Analyze yesterday's emails")
        print("  python scripts/quick_analysis.py last7days    # Analyze last 7 days")
        print("  python scripts/quick_analysis.py YYYY-MM-DD   # Analyze specific date")
        print("  python scripts/quick_analysis.py setup        # Setup analysis environment")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "setup":
        # Run setup script
        setup_script = project_root / "src" / "analysis" / "setup_email_analysis.py"
        if setup_script.exists():
            print("🔧 Setting up email analysis environment...")
            result = subprocess.run([sys.executable, str(setup_script)],
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            sys.exit(result.returncode)
        else:
            print("❌ Setup script not found")
            sys.exit(1)

    elif command == "yesterday":
        # Analyze yesterday's emails
        print("📅 Analyzing yesterday's emails...")
        cmd = [sys.executable, str(main_script), "analyze", "--yesterday"]

    elif command == "last7days":
        # Analyze last 7 days
        print("📅 Analyzing emails from last 7 days...")
        cmd = [sys.executable, str(main_script), "analyze", "--days", "7"]

    elif len(command) == 10 and command.count('-') == 2:
        # Specific date (YYYY-MM-DD format)
        print(f"📅 Analyzing emails for date: {command}")
        cmd = [sys.executable, str(main_script), "analyze", "--date", command]

    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'yesterday', 'last7days', 'YYYY-MM-DD', or 'setup'")
        sys.exit(1)

    # Run the analysis command
    print("🚀 Running analysis...")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()