"""Tests for the AI Toolkit Self-Indexing System"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

from ai_toolkit.tools.toolkit_indexer import ToolkitIndexer, ComponentAnalyzer
from ai_toolkit.tests.test_base import LLMTestCase

class TestToolkitIndexer(LLMTestCase):
    """Test cases for ToolkitIndexer"""
    
    def setUp(self):
        """Create a temporary workspace with test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.indexer = ToolkitIndexer(self.temp_dir)
        
        # Create test files
        self.create_test_files()
        
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.temp_dir)
        
    def create_test_files(self):
        """Create a set of test Python files"""
        # Create a component file
        component_code = '''"""Test component."""
import os
from pathlib import Path

class MyComponent:
    """A test component."""
    def __init__(self):
        self.value = 0
        
    def process(self):
        """Process something."""
        return self.value * 2
'''
        self.write_file('src/component.py', component_code)
        
        # Create a test file
        test_code = '''"""Test for component."""
import unittest
from pathlib import Path

from src.component import MyComponent

class TestMyComponent(unittest.TestCase):
    """Test cases for MyComponent"""
    
    def test_process(self):
        """Test process method"""
        comp = MyComponent()
        self.assertEqual(comp.process(), 0)
'''
        self.write_file('tests/test_component.py', test_code)
        
    def write_file(self, rel_path: str, content: str):
        """Write a file in the temporary workspace"""
        full_path = Path(self.temp_dir) / rel_path
        os.makedirs(full_path.parent, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
            
    def test_analyze_file(self):
        """Test analyzing a single file"""
        file_path = Path(self.temp_dir) / 'src/component.py'
        analysis = self.indexer.analyze_file(file_path)
        
        # Check imports
        self.assertIn('os', analysis['imports'])
        self.assertIn('pathlib.Path', analysis['imports'])
        
        # Check classes
        self.assertIn('MyComponent', analysis['classes'])
        
        # Check functions
        self.assertIn('process', analysis['functions'])
        
    def test_update_index(self):
        """Test updating the entire toolkit index"""
        self.indexer.update_index()
        
        # Verify index file was created
        self.assertTrue(self.indexer.index_file.exists())
        
        # Parse and verify index contents
        tree = ET.parse(self.indexer.index_file)
        root = tree.getroot()
        
        # Check components
        components = root.find('Components')
        self.assertIsNotNone(components)
        
        # Verify component.py is indexed
        found_component = False
        for component in components.findall('Component'):
            if component.find('File').text == 'src/component.py':
                found_component = True
                # Check class was indexed
                classes = component.find('Classes')
                self.assertIsNotNone(classes)
                self.assertEqual(classes.find('Class').text, 'MyComponent')
                break
        self.assertTrue(found_component)
        
        # Check test coverage
        coverage = root.find('TestCoverage')
        self.assertIsNotNone(coverage)
        
        # Verify MyComponent is tested
        found_coverage = False
        for comp_coverage in coverage.findall('ComponentCoverage'):
            if comp_coverage.find('Component').text == 'MyComponent':
                found_coverage = True
                test_files = comp_coverage.find('TestFiles')
                self.assertIsNotNone(test_files)
                self.assertEqual(
                    test_files.find('TestFile').text,
                    'tests/test_component.py'
                )
                break
        self.assertTrue(found_coverage)
        
    def test_extract_tested_components(self):
        """Test extracting tested components from test file"""
        analysis = {
            'classes': {'TestMyComponent', 'TestOtherComponent'},
            'functions': {'test_process', 'helper_method'}
        }
        
        tested = self.indexer._extract_tested_components(analysis)
        self.assertEqual(tested, {'MyComponent', 'OtherComponent'})
        
class TestComponentAnalyzer(LLMTestCase):
    """Test cases for ComponentAnalyzer"""
    
    def test_analyze_imports(self):
        """Test analyzing import statements"""
        code = '''
import os
from pathlib import Path
from typing import Dict, List
'''
        tree = ast.parse(code)
        analyzer = ComponentAnalyzer('test_module')
        analyzer.visit(tree)
        
        self.assertIn('os', analyzer.imports)
        self.assertIn('pathlib.Path', analyzer.imports)
        self.assertIn('typing.Dict', analyzer.imports)
        self.assertIn('typing.List', analyzer.imports)
        
    def test_analyze_classes(self):
        """Test analyzing class definitions"""
        code = '''
class BaseClass:
    pass
    
class ChildClass(BaseClass):
    pass
'''
        tree = ast.parse(code)
        analyzer = ComponentAnalyzer('test_module')
        analyzer.visit(tree)
        
        self.assertEqual(analyzer.classes, {'BaseClass', 'ChildClass'})
        self.assertIn('BaseClass', analyzer.dependencies)
        
    def test_analyze_functions(self):
        """Test analyzing function definitions"""
        code = '''
def standalone_function():
    pass
    
class MyClass:
    def method(self):
        pass
'''
        tree = ast.parse(code)
        analyzer = ComponentAnalyzer('test_module')
        analyzer.visit(tree)
        
        self.assertEqual(
            analyzer.functions,
            {'standalone_function', 'method'}
        )

if __name__ == '__main__':
    unittest.main() 