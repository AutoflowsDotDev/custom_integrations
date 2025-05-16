#!/usr/bin/env python3
"""Test runner script with coverage reporting."""
import os
import sys
import subprocess
import argparse


def main():
    """Run tests with code coverage."""
    parser = argparse.ArgumentParser(description='Run tests with code coverage.')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test-path', '-t', type=str, help='Specific test path to run')
    parser.add_argument('--coverage-only', '-c', action='store_true', help='Show coverage report only, no tests')
    parser.add_argument('--html', action='store_true', help='Generate HTML coverage report')
    
    args = parser.parse_args()
    
    # Base command using pytest.ini settings
    cmd = ["pytest"]
    
    # Add verbosity if requested
    if args.verbose:
        cmd.append("-vv")
    
    # Add coverage options 
    cmd.extend(["--cov=src", "--cov-report=term"])
    
    # Add HTML coverage if requested
    if args.html:
        cmd.append("--cov-report=html")
    
    # Add specific test path if provided
    if args.test_path:
        cmd.append(args.test_path)
    
    # If coverage-only, just show the report from previous run
    if args.coverage_only:
        coverage_cmd = ["coverage", "report", "-m"]
        subprocess.run(coverage_cmd)
        if args.html:
            print("\nHTML coverage report generated in htmlcov/ directory")
            # Try to open in browser if possible
            try:
                if sys.platform.startswith('darwin'):  # macOS
                    subprocess.run(["open", "htmlcov/index.html"])
                elif sys.platform.startswith('win'):  # Windows
                    os.startfile("htmlcov/index.html")
                elif sys.platform.startswith('linux'):  # Linux
                    subprocess.run(["xdg-open", "htmlcov/index.html"])
            except:
                pass
        return
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    # Print helpful message about HTML report if generated
    if args.html:
        print("\nHTML coverage report generated in htmlcov/ directory")
    
    # Return the exit code from pytest
    return result.returncode


if __name__ == "__main__":
    sys.exit(main()) 