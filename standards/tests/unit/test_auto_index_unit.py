# Unit tests for auto-indexing decorators
#
# These tests verify the core functionality of the auto_index and auto_index_class
# decorators, focusing on method wrapping, inheritance, and basic behavior.

import unittest
import time
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import Dict, Any

from ai_toolkit.tools.auto_index import auto_index, auto_index_class
from ai_toolkit.tests.test_base import LLMTestCase
from ai_toolkit.tools.performance_monitor import TestMetrics

logger = logging.getLogger(__name__)

class TestAutoIndexDecorator(LLMTestCase):
    """Unit tests for @auto_index decorator."""
    
    def setUp(self):
        """Initialize test environment and metrics."""
        super().setUp()
        self.metrics = TestMetrics()
        self.start_time = time.time()
        logger.info("Setting up test environment for auto_index decorator tests")
        
    def tearDown(self):
        """Clean up and record metrics."""
        duration = time.time() - self.start_time
        self.metrics.record_test_duration(self.id(), duration)
        logger.info(f"Test {self.id()} completed in {duration:.2f}s")
        super().tearDown()
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_decorator_successful_test_updates_index(self, mock_indexer_cls):
        """Test that index is updated after successful test execution."""
        # Arrange
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index
        def test_success():
            pass
            
        # Act
        test_success()
        
        # Assert
        mock_instance.update_index.assert_called_once()
        self.metrics.record_assertion("index_update_called")
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')    
    def test_decorator_failed_test_preserves_index(self, mock_indexer_cls):
        """Test that index remains unchanged after test failure."""
        # Arrange
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index
        def test_failure():
            raise ValueError("Expected test failure")
            
        # Act & Assert
        with self.assertRaises(ValueError):
            test_failure()
        mock_instance.update_index.assert_not_called()
        self.metrics.record_assertion("index_preserved_on_failure")
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_decorator_metadata_preservation_succeeds(self, mock_indexer_cls):
        """Test that function metadata is preserved after decoration."""
        # Arrange
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        test_doc = "Test docstring for metadata preservation."
        
        @auto_index
        def test_metadata():
            """Test docstring for metadata preservation."""
            pass
            
        # Act & Assert
        self.assertEqual(test_metadata.__doc__, test_doc)
        self.assertEqual(test_metadata.__name__, "test_metadata")
        self.metrics.record_assertion("metadata_preserved")

class TestAutoIndexClassDecorator(LLMTestCase):
    """Unit tests for @auto_index_class decorator."""
    
    def setUp(self):
        """Initialize test environment and metrics."""
        super().setUp()
        self.metrics = TestMetrics()
        self.start_time = time.time()
        logger.info("Setting up test environment for auto_index_class decorator tests")
        
    def tearDown(self):
        """Clean up and record metrics."""
        duration = time.time() - self.start_time
        self.metrics.record_test_duration(self.id(), duration)
        logger.info(f"Test {self.id()} completed in {duration:.2f}s")
        super().tearDown()
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_class_decorator_method_wrapping_succeeds(self, mock_indexer_cls):
        """Test that class decorator properly wraps all test methods."""
        # Arrange
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index_class
        class SampleTest:
            def test_one(self):
                pass
                
            def test_two(self):
                pass
                
            def not_a_test(self):
                pass
                
        # Act
        test = SampleTest()
        test.test_one()
        test.test_two()
        test.not_a_test()
        
        # Assert
        self.assertEqual(mock_instance.update_index.call_count, 2)
        self.metrics.record_assertion("test_methods_wrapped")
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_class_decorator_inheritance_preserves_indexing(self, mock_indexer_cls):
        """Test that inherited test methods maintain indexing functionality."""
        # Arrange
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        
        @auto_index_class
        class BaseTest:
            def test_base(self):
                pass
                
        class ChildTest(BaseTest):
            def test_child(self):
                pass
                
        # Act
        test = ChildTest()
        test.test_base()
        test.test_child()
        
        # Assert
        self.assertEqual(mock_instance.update_index.call_count, 2)
        self.metrics.record_assertion("inheritance_indexing_preserved")
        
    @patch('ai_toolkit.tools.auto_index.ToolkitIndexer')
    def test_class_decorator_metadata_preservation_succeeds(self, mock_indexer_cls):
        """Test that class metadata is preserved after decoration."""
        # Arrange
        mock_instance = MagicMock()
        mock_indexer_cls.return_value = mock_instance
        test_doc = "Test class docstring for metadata preservation."
        
        @auto_index_class
        class SampleTest:
            """Test class docstring for metadata preservation."""
            def test_method(self):
                pass
                
        # Act & Assert
        self.assertEqual(SampleTest.__doc__, test_doc)
        self.assertEqual(SampleTest.__name__, "SampleTest")
        self.metrics.record_assertion("class_metadata_preserved")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main() 