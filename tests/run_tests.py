"""Test runner for AI Toolkit."""
import unittest
import sys
import os
from pathlib import Path

def run_tests():
    """Discover and run all tests."""
    # Get the absolute path to the toolkit root
    toolkit_root = Path(__file__).parent.parent
    project_root = toolkit_root.parent
    
    # Add both to Python path
    sys.path.insert(0, str(toolkit_root))
    sys.path.insert(0, str(project_root))
    
    # Change to the tests directory
    os.chdir(Path(__file__).parent)
    
    # Find all test files in the tests directory
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if all tests passed, 1 otherwise
    return 0 if result.wasSuccessful() else 1
    
if __name__ == '__main__':
    sys.exit(run_tests()) 