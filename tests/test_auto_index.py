"""Tests for auto-indexing decorators"""

import os
import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_toolkit.tools.auto_index import auto_index, auto_index_class
from ai_toolkit.tests.test_base import LLMTestCase

class TestAutoIndex(LLMTestCase):
    """Test cases for auto-indexing decorators"""
    
    def setUp(self):
        """Create a temporary workspace for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Create a mock index file
        self.index_path = Path(self.temp_dir) / "codebase_index.json"
        self.mock_index = {
            "metadata": {"last_updated": "2025-01-12"},
            "components": {}
        }
        with open(self.index_path, 'w') as f:
            json.dump(self.mock_index, f)
            
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_successful_test(self, mock_indexer_cls):
        """Test that index is updated after successful test."""
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index(toolkit_root=self.temp_dir)
        def test_success():
            pass
            
        test_success()
        mock_instance.update_index.assert_called_once()
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')    
    def test_auto_index_failed_test(self, mock_indexer_cls):
        """Test that index is not updated after failed test."""
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index(toolkit_root=self.temp_dir)
        def test_failure():
            raise ValueError("Test failure")
            
        with self.assertRaises(ValueError):
            test_failure()
        mock_instance.update_index.assert_not_called()
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_no_args(self, mock_indexer_cls):
        """Test auto_index decorator without arguments."""
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index
        def test_no_args():
            pass
            
        test_no_args()
        mock_instance.update_index.assert_called_once()
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_invalid_root(self, mock_indexer_cls):
        """Test handling of invalid toolkit root."""
        mock_instance = MagicMock()
        mock_indexer_cls.side_effect = ValueError("Invalid root")
        
        @auto_index(toolkit_root="/invalid/path")
        def test_invalid():
            pass
            
        test_invalid()  # Should not raise exception
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_preserves_function_metadata(self, mock_indexer_cls):
        """Test that decorator preserves function metadata."""
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index(toolkit_root=self.temp_dir)
        def test_metadata():
            """Test docstring."""
            pass
            
        self.assertEqual(test_metadata.__doc__, "Test docstring.")
        self.assertEqual(test_metadata.__name__, "test_metadata")
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_class_all_methods(self, mock_indexer_cls):
        """Test that class decorator wraps all test methods."""
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index_class(toolkit_root=self.temp_dir)
        class SampleTest:
            def test_one(self):
                pass
                
            def test_two(self):
                pass
                
            def not_a_test(self):
                pass
                
        test = SampleTest()
        test.test_one()
        test.test_two()
        test.not_a_test()
        
        self.assertEqual(mock_instance.update_index.call_count, 2)
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_class_no_args(self, mock_indexer_cls):
        """Test class decorator without arguments."""
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index_class
        class SampleTest:
            def test_method(self):
                pass
                
        test = SampleTest()
        test.test_method()
        mock_instance.update_index.assert_called_once()
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_class_preserves_class_metadata(self, mock_indexer_cls):
        """Test that class decorator preserves class metadata."""
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index_class(toolkit_root=self.temp_dir)
        class SampleTest:
            """Test class docstring."""
            def test_method(self):
                pass
                
        self.assertEqual(SampleTest.__doc__, "Test class docstring.")
        self.assertEqual(SampleTest.__name__, "SampleTest")
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_exception_handling(self, mock_indexer_cls):
        """Test that indexer exceptions are caught and logged."""
        mock_instance = MagicMock()
        mock_instance.update_index.side_effect = Exception("Update failed")
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index(toolkit_root=self.temp_dir)
        def test_exception():
            pass
            
        test_exception()  # Should not raise exception
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_auto_index_class_inheritance(self, mock_indexer_cls):
        """Test that class decorator works with inheritance."""
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index_class(toolkit_root=self.temp_dir)
        class BaseTest:
            def test_base(self):
                pass
                
        class ChildTest(BaseTest):
            def test_child(self):
                pass
                
        test = ChildTest()
        test.test_base()
        test.test_child()
        self.assertEqual(mock_instance.update_index.call_count, 2)

if __name__ == '__main__':
    unittest.main() 