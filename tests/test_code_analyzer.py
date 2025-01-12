import unittest
from pathlib import Path
import tempfile
import os
import shutil

from ai_toolkit.code_analyzer import CodeAnalyzer, CodeSymbol, CodeContext
from ai_toolkit.tests.test_base import LLMTestCase

class TestCodeAnalyzer(LLMTestCase):
    """Test cases for CodeAnalyzer"""
    
    def setUp(self):
        """Create a temporary workspace with test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = CodeAnalyzer(self.temp_dir)
        
        # Create a test file with various Python constructs
        self.test_file = "sample.py"
        self.test_content = '''"""Module docstring."""
import os
from pathlib import Path
import sys

class BaseClass:
    """Base class docstring."""
    def __init__(self):
        self.value = 0
        
    def base_method(self):
        """Base method docstring."""
        return self.value
        
class TestClass(BaseClass):
    """Test class docstring."""
    
    def __init__(self):
        super().__init__()
        self.name = "test"
        
    def test_method(self):
        """Test method docstring."""
        value = self.base_method()
        return f"{self.name}: {value}"
        
def standalone_function():
    """Standalone function docstring."""
    test = TestClass()
    return test.test_method()
'''
        with open(os.path.join(self.temp_dir, self.test_file), 'w') as f:
            f.write(self.test_content)
            
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.temp_dir)
        
    def test_analyze_file(self):
        """Test analyzing an entire file"""
        context = self.analyzer.analyze_file(self.test_file)
        
        # Check imports
        self.assertIn('os', context.imports)
        self.assertIn('pathlib.Path', context.imports)
        
        # Check symbols
        self.assertIn('BaseClass', context.symbols)
        self.assertIn('TestClass', context.symbols)
        self.assertIn('standalone_function', context.symbols)
        
        # Check inheritance
        test_class = context.symbols['TestClass']
        self.assertIn('BaseClass', test_class.dependencies)
        
        # Check docstrings
        self.assertEqual(context.docstring, 'Module docstring.')
        self.assertEqual(
            context.symbols['BaseClass'].docstring,
            'Base class docstring.'
        )
        
    def test_get_context_at_line(self):
        """Test getting context at a specific line"""
        # Get context inside TestClass.test_method
        context = self.analyzer.get_context_at_line(self.test_file, 23)
        
        # Should be in TestClass and test_method scope
        self.assertEqual(len(context.scope_stack), 2)
        self.assertIn('TestClass', context.scope_stack)
        self.assertIn('TestClass.test_method', context.scope_stack)
        
        # Should have access to parent class symbols
        self.assertIn('BaseClass', context.symbols)
        
    def test_find_symbol_references(self):
        """Test finding references to a symbol"""
        refs = self.analyzer.find_symbol_references(self.test_file, 'TestClass')
        
        # TestClass is referenced in class definition and standalone_function
        self.assertGreaterEqual(len(refs), 2)
        
    def test_get_symbol_dependencies(self):
        """Test getting symbol dependencies"""
        deps = self.analyzer.get_symbol_dependencies(self.test_file, 'TestClass.test_method')
        
        # Should depend on base_method and name
        self.assertIn('base_method', deps)
        self.assertIn('name', deps)
        
if __name__ == '__main__':
    unittest.main() 