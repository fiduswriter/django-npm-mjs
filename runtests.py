#!/usr/bin/env python
"""
Test runner for django-npm-mjs package.

This script runs the test suite without requiring a full Django setup.
For integration tests with Django, use Django's test runner.
"""
import os
import sys
import unittest

# Add the package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    """Discover and run all tests."""
    # Discover tests in the npm_mjs/tests directory
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), "npm_mjs", "tests")
    suite = loader.discover(start_dir, pattern="test_*.py")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on success
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
