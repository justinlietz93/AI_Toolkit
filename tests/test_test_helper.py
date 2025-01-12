import unittest
from pathlib import Path
import tempfile
import os
import shutil

from ai_toolkit.test_helper import TestHelper, TestCase, TestAnalysis

class TestTestHelper(unittest.TestCase):
    """Test cases for TestHelper"""
    
    def setUp(self):
        """Create a temporary workspace with test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.helper = TestHelper(self.temp_dir)
        
        # Create a source file to test
        self.source_file = "calculator.py"
        self.source_content = '''"""A simple calculator module."""

class Calculator:
    """A basic calculator class."""
    
    def __init__(self):
        self.result = 0
        
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        self.result = a + b
        return self.result
        
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        self.result = a - b
        return self.result
'''
        
        # Create a test file to analyze
        self.test_file = "test_calculator.py"
        self.test_content = '''"""Test cases for calculator."""
import unittest
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()
        self.unused_var = 10
        
    def test_add(self):
        result = self.calc.add(2, 3)
        self.assertEqual(result, 5)
        
    def test_empty(self):
        # Test with no assertions
        pass
'''
        
        # Write the files
        with open(os.path.join(self.temp_dir, self.source_file), 'w') as f:
            f.write(self.source_content)
        with open(os.path.join(self.temp_dir, self.test_file), 'w') as f:
            f.write(self.test_content)
            
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.temp_dir)
        
    def test_analyze_test_file(self):
        """Test analyzing a test file"""
        analysis = self.helper.analyze_test_file(self.test_file)
        
        # Check coverage
        self.assertLess(analysis.coverage, 100)  # Not all methods have assertions
        
        # Check unused setup
        self.assertIn('unused_var', analysis.unused_setup)
        
        # Check suggestions
        suggestions = set(analysis.suggestions)
        self.assertTrue(any('test_empty' in s for s in suggestions))  # Should suggest adding assertions
        
    def test_generate_test_case(self):
        """Test generating a test case for a function"""
        test_case = self.helper.generate_test_case(self.source_file, 'add')
        
        # Check basic properties
        self.assertEqual(test_case.function_name, 'test_add')
        self.assertIn('Add two numbers', test_case.description)
        
        # Should have type checking assertion for float return
        self.assertTrue(any('float' in a for a in test_case.assertions))
        
    def test_suggest_test_improvements(self):
        """Test suggesting improvements for tests"""
        suggestions = self.helper.suggest_test_improvements(self.test_file)
        
        # Should suggest improvements for empty test
        self.assertTrue(any('test_empty' in s for s in suggestions))
        
        # Should suggest removing unused setup
        self.assertTrue(any('unused_var' in s for s in suggestions))
        
    def test_generate_test_file(self):
        """Test generating a complete test file"""
        content, test_cases = self.helper.generate_test_file(self.source_file)
        
        # Should generate test cases for Calculator class and its methods
        self.assertTrue(any(tc.function_name == 'test_Calculator_creation' for tc in test_cases))
        self.assertTrue(any(tc.function_name == 'test_add' for tc in test_cases))
        self.assertTrue(any(tc.function_name == 'test_subtract' for tc in test_cases))
        
        # Content should include proper imports and class definition
        self.assertIn('import unittest', content)
        self.assertIn('class TestCalculator(unittest.TestCase):', content)
        self.assertIn('def setUp(self):', content)
        
if __name__ == '__main__':
    unittest.main() 