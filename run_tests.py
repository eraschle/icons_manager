#!/usr/bin/env python3
"""
Test runner script for the icon manager project.
This script provides a simple interface to run tests with different options.
"""

import argparse
import subprocess
import sys


def run_tests(test_path=None, coverage=False, verbose=False, markers=None):
    """Run pytest with the specified options."""
    cmd = ["python", "-m", "pytest"]

    if test_path:
        cmd.append(test_path)

    if coverage:
        cmd.extend(["--cov=icon_manager", "--cov-report=term-missing"])

    if verbose:
        cmd.append("-v")

    if markers:
        cmd.extend(["-m", markers])

    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(description="Run tests for the icon manager")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run tests in verbose mode")
    parser.add_argument(
        "--markers",
        "-m",
        type=str,
        help='Run tests with specific markers (e.g., "unit", "not slow")',
    )
    parser.add_argument("test_path", nargs="?", help="Path to specific test file or directory")

    args = parser.parse_args()

    result = run_tests(
        test_path=args.test_path,
        coverage=args.coverage,
        verbose=args.verbose,
        markers=args.markers,
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
