#!/usr/bin/env python3
"""
Test runner script for the YouTube downloader application.

This script provides a convenient way to run tests with different configurations
and generate coverage reports.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for YouTube downloader")
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run only integration tests"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--fast", 
        action="store_true", 
        help="Skip slow tests"
    )
    parser.add_argument(
        "--no-network", 
        action="store_true", 
        help="Skip tests requiring network"
    )
    parser.add_argument(
        "--path", 
        type=str, 
        help="Run tests from specific path"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    # Add test selection
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    
    # Add path selection
    if args.path:
        cmd.append(args.path)
    else:
        cmd.append("tests/")
    
    # Add marker filters
    markers = []
    if args.fast:
        markers.append("not slow")
    if args.no_network:
        markers.append("not requires_network")
    
    if markers:
        cmd.extend(["-m", " and ".join(markers)])
    
    # Run the tests
    success = run_command(cmd, "Test Suite")
    
    # Generate coverage report if requested and tests passed
    if args.coverage and success:
        print(f"\n{'='*60}")
        print("Coverage report generated in htmlcov/index.html")
        print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
