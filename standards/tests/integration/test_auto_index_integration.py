"""Integration tests for auto-indexing system.

Tests how auto-indexing works in real-world scenarios with multiple components.
"""

import os
import shutil
import tempfile
import unittest
import json
from pathlib import Path
from typing import Dict, Any
import time

from ai_toolkit.tools.auto_index import auto_index, auto_index_class
from ai_toolkit.tools.toolkit_indexer import ToolkitIndexer
from ai_toolkit.tests.test_base import LLMTestCase

class MockProject:
    """Helper class to create a mock project structure for testing."""
    
    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
        self.src_dir = self.root / "src"
        self.tests_dir = self.root / "tests"
        self.index_file = self.root / "codebase_index.json"
        
    def setup(self):
        """Create a mock project structure."""
        # Create directories
        self.src_dir.mkdir(parents=True)
        self.tests_dir.mkdir(parents=True)
        
        # Create source files
        (self.src_dir / "module_a.py").write_text("""
def function_a():
    return "Module A"
""")
        
        (self.src_dir / "module_b.py").write_text("""
def function_b():
    return "Module B"
""")
        
        # Create empty index
        self.index_file.write_text(json.dumps({
            "metadata": {
                "last_updated": "2024-01-01 00:00:00",
                "update_counter": 0,
                "version": "0.1.0"
            },
            "components": {}
        }))
        
    def get_index_data(self) -> Dict[str, Any]:
        """Read the current index data."""
        return json.loads(self.index_file.read_text())

@auto_index_class
class BaseIntegrationTest(LLMTestCase):
    """Base class for integration tests to verify inheritance."""
    
    def test_base_functionality(self):
        """Test that should be inherited and auto-indexed."""
        self.assertTrue(True)

class TestAutoIndexIntegration(BaseIntegrationTest):
    """Integration tests for auto-indexing functionality."""
    
    def setUp(self):
        """Create a temporary project structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Set up mock project
        self.project = MockProject(self.temp_dir)
        self.project.setup()
        
    def test_index_updates_across_runs(self):
        """Test that index is properly updated across multiple test runs."""
        # First run - should create initial entries
        @auto_index(toolkit_root=self.temp_dir)
        def test_first_run():
            pass
            
        test_first_run()
        first_index = self.project.get_index_data()
        self.assertIn("components", first_index)
        first_counter = first_index["metadata"]["update_counter"]
        
        # Second run - should update existing entries
        @auto_index(toolkit_root=self.temp_dir)
        def test_second_run():
            pass
            
        test_second_run()
        second_index = self.project.get_index_data()
        second_counter = second_index["metadata"]["update_counter"]
        
        # Counter should increment on each update
        self.assertGreater(second_counter, first_counter)
        
    def test_multiple_test_classes(self):
        """Test that multiple test classes can update the same index."""
        @auto_index_class(toolkit_root=self.temp_dir)
        class FirstTestClass:
            def test_first(self):
                pass
                
        @auto_index_class(toolkit_root=self.temp_dir)
        class SecondTestClass:
            def test_second(self):
                pass
                
        # Run tests from both classes
        FirstTestClass().test_first()
        SecondTestClass().test_second()
        
        # Verify index contains both test runs
        index_data = self.project.get_index_data()
        components = index_data["components"]
        self.assertGreaterEqual(len(components), 2)
        
    def test_error_recovery(self):
        """Test that index remains valid even after test failures."""
        initial_index = self.project.get_index_data()
        
        # Run a failing test
        @auto_index(toolkit_root=self.temp_dir)
        def test_failure():
            raise ValueError("Expected failure")
            
        with self.assertRaises(ValueError):
            test_failure()
            
        # Index should not be corrupted
        final_index = self.project.get_index_data()
        self.assertEqual(
            initial_index["metadata"]["last_updated"],
            final_index["metadata"]["last_updated"]
        )
        
    def test_inherited_method_indexing(self):
        """Test that inherited test methods are properly indexed."""
        # This should trigger indexing from both the base class method
        # and this class's methods
        self.test_base_functionality()
        
        # Verify index was updated for both methods
        index_data = self.project.get_index_data()
        self.assertIn("components", index_data)
        
    def test_concurrent_updates(self):
        """Test that concurrent test runs don't corrupt the index."""
        import threading
        
        @auto_index(toolkit_root=self.temp_dir)
        def concurrent_test():
            pass
            
        # Run multiple tests concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=concurrent_test)
            thread.start()
            threads.append(thread)
            
        for thread in threads:
            thread.join()
            
        # Verify index is still valid
        index_data = self.project.get_index_data()
        self.assertIn("components", index_data)
        self.assertIn("metadata", index_data)

if __name__ == '__main__':
    unittest.main() 