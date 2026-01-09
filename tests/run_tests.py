#!/usr/bin/env python3
"""
Test Runner Script - Ensures all test artifacts stay in tests folder
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_test_environment():
    """Setup test environment and ensure working directory is tests folder."""
    # Get the tests directory
    tests_dir = Path(__file__).parent
    
    # Change to tests directory
    os.chdir(tests_dir)
    
    # Ensure we're in the right directory
    print(f"Working directory: {os.getcwd()}")
    assert os.getcwd().endswith('tests'), "Must be in tests directory"
    
    # Clean up any existing artifacts
    artifacts_to_clean = [
        'htmlcov',
        '.coverage',
        '.coverage.*',
        'coverage.json',
        'coverage.xml',
        '.pytest_cache'
    ]
    
    for artifact in artifacts_to_clean:
        if '*' in artifact:
            # Handle glob patterns
            import glob
            for file_path in glob.glob(artifact):
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path, ignore_errors=True)
                    else:
                        os.remove(file_path)
        else:
            if os.path.exists(artifact):
                if os.path.isdir(artifact):
                    shutil.rmtree(artifact, ignore_errors=True)
                else:
                    os.remove(artifact)

def run_tests_with_coverage():
    """Run tests with coverage, keeping all files in tests folder."""
    setup_test_environment()
    
    # Add src to Python path
    src_path = str(Path('..').resolve() / 'src')
    env = os.environ.copy()
    env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')
    
    # Run pytest with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        '--cov=../src',
        '--cov-report=html:htmlcov/',
        '--cov-report=term-missing',
        '--cov-report=json:coverage.json',
        '--cov-config=coverage.ini',
        '--cache-dir=.pytest_cache',
        '-v'
    ]
    
    # Add any additional arguments passed to this script
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    
    # Run the command
    result = subprocess.run(cmd, env=env)
    
    # Verify all artifacts are in tests folder
    print("\nTest artifacts created:")
    for item in os.listdir('.'):
        if item.startswith('.coverage') or item in ['htmlcov', 'coverage.json', 'coverage.xml', '.pytest_cache']:
            print(f"  ✓ {item}")
    
    return result.returncode

def run_specific_test_file(test_file):
    """Run a specific test file with coverage."""
    setup_test_environment()
    
    # Add src to Python path
    src_path = str(Path('..').resolve() / 'src')
    env = os.environ.copy()
    env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')
    
    cmd = [
        sys.executable, '-m', 'pytest',
        test_file,
        '--cov=../src',
        '--cov-report=term-missing',
        '-v'
    ]
    
    print(f"Running specific test: {test_file}")
    result = subprocess.run(cmd, env=env)
    return result.returncode

def generate_coverage_report():
    """Generate detailed coverage report."""
    setup_test_environment()
    
    if not os.path.exists('.coverage'):
        print("No coverage data found. Run tests first.")
        return 1
    
    # Generate HTML report
    cmd = [sys.executable, '-m', 'coverage', 'html', '-d', 'htmlcov']
    subprocess.run(cmd)
    
    # Generate terminal report
    cmd = [sys.executable, '-m', 'coverage', 'report', '--show-missing']
    subprocess.run(cmd)
    
    print(f"\nCoverage report generated in: {os.path.join(os.getcwd(), 'htmlcov')}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--report-only":
        exit_code = generate_coverage_report()
    elif len(sys.argv) > 1 and sys.argv[1].startswith("test_"):
        exit_code = run_specific_test_file(sys.argv[1])
    else:
        exit_code = run_tests_with_coverage()
    
    sys.exit(exit_code)
