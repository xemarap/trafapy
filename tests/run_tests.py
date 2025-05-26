#!/usr/bin/env python3
"""
Test Runner for TrafaPy

This script provides a convenient way to run different types of tests
for the TrafaPy library with various configurations.

Usage:
    python run_tests.py [options]
    
Examples:
    python run_tests.py --unit           # Run only unit tests
    python run_tests.py --integration    # Run only integration tests
    python run_tests.py --all            # Run all tests
    python run_tests.py --coverage       # Run with coverage report
    python run_tests.py --fast           # Run fast tests only
    python run_tests.py --verbose        # Run with verbose output
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False


def check_prerequisites():
    """Check if required packages are installed."""
    required_packages = ['pytest', 'pytest-cov']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = ["pytest", "-m", "not integration"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend(["--cov=trafapy", "--cov-report=term-missing"])
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = ["pytest", "-m", "integration", "--maxfail=3"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    print("\n⚠️  Integration tests may hit the real API and could fail due to:")
    print("   - Network connectivity issues")
    print("   - API changes or downtime")
    print("   - Rate limiting")
    
    return run_command(cmd, "Integration Tests")


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend(["--cov=trafapy", "--cov-report=html", "--cov-report=term-missing"])
    
    return run_command(cmd, "All Tests")


def run_fast_tests(verbose=False):
    """Run fast tests only."""
    cmd = ["pytest", "-m", "not slow and not integration"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    return run_command(cmd, "Fast Tests")


def run_lint_checks():
    """Run code quality checks."""
    checks = [
        (["flake8", "trafapy", "tests"], "Flake8 Linting"),
        (["black", "--check", "trafapy", "tests"], "Black Code Formatting"),
        (["mypy", "trafapy", "--ignore-missing-imports"], "MyPy Type Checking")
    ]
    
    all_passed = True
    for cmd, description in checks:
        success = run_command(cmd, description)
        if not success:
            all_passed = False
    
    return all_passed


def generate_coverage_report():
    """Generate detailed coverage report."""
    cmd = ["pytest", "--cov=trafapy", "--cov-report=html", "--cov-report=xml", "-m", "not integration"]
    
    success = run_command(cmd, "Coverage Report Generation")
    
    if success:
        html_report = Path("htmlcov/index.html")
        if html_report.exists():
            print(f"\n📊 Coverage report generated: {html_report.absolute()}")
            print("Open this file in your browser to view the detailed coverage report.")
    
    return success


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for TrafaPy library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --unit --verbose          Run unit tests with verbose output
  %(prog)s --integration             Run integration tests
  %(prog)s --all --coverage          Run all tests with coverage
  %(prog)s --fast                    Run only fast tests
  %(prog)s --lint                    Run code quality checks
  %(prog)s --coverage-report         Generate detailed coverage report
        """
    )
    
    # Test type options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument('--unit', action='store_true', 
                           help='Run unit tests only (excludes integration tests)')
    test_group.add_argument('--integration', action='store_true',
                           help='Run integration tests only (may hit real API)')
    test_group.add_argument('--all', action='store_true',
                           help='Run all tests (default)')
    test_group.add_argument('--fast', action='store_true',
                           help='Run fast tests only (excludes slow and integration)')
    
    # Quality checks
    parser.add_argument('--lint', action='store_true',
                       help='Run code quality checks (flake8, black, mypy)')
    parser.add_argument('--coverage-report', action='store_true',
                       help='Generate detailed coverage report')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--coverage', action='store_true',
                       help='Include coverage reporting')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Determine what to run
    success = True
    
    if args.lint:
        success = run_lint_checks()
    elif args.coverage_report:
        success = generate_coverage_report()
    elif args.unit:
        success = run_unit_tests(args.verbose, args.coverage)
    elif args.integration:
        success = run_integration_tests(args.verbose)
    elif args.fast:
        success = run_fast_tests(args.verbose)
    elif args.all:
        success = run_all_tests(args.verbose, args.coverage)
    else:
        # Default: run unit tests
        success = run_unit_tests(args.verbose, args.coverage)
    
    # Print summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("💥 Some tests failed. Check the output above for details.")
    print('='*60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
