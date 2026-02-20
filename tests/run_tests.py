"""
Test runner script for configuration management tests.

Usage:
    python tests/run_tests.py
    python tests/run_tests.py -v  # Verbose mode
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import test modules
from test_config_loader import TestConfigLoader, TestConfigLoaderWithTempFiles, TestPatternMatching


def run_tests(verbosity=2):
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestConfigLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigLoaderWithTempFiles))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternMatching))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    # Check for verbose flag
    verbosity = 2 if "-v" in sys.argv else 1
    
    print("=" * 70)
    print("Configuration Management Tests")
    print("=" * 70)
    print()
    
    exit_code = run_tests(verbosity=verbosity)
    
    print()
    print("=" * 70)
    print(f"Tests {'PASSED' if exit_code == 0 else 'FAILED'}")
    print("=" * 70)
    
    sys.exit(exit_code)
