"""System tests for auto-indexing functionality.

These tests verify the auto-indexing system works correctly in real-world scenarios
with complex project structures and cross-project dependencies.
"""

import os
import shutil
import tempfile
import unittest
import json
import importlib.util
import msvcrt
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager
from multiprocessing import Value

from ai_toolkit.tools.auto_index import auto_index, auto_index_class
from ai_toolkit.tools.toolkit_indexer import ToolkitIndexer
from ai_toolkit.tests.test_base import LLMTestCase

def normalize_path(path: str) -> str:
    """Normalize path separators for consistent comparison."""
    return str(Path(path))

@contextmanager
def file_lock(path: Path):
    """Acquire an exclusive lock on a file using Windows file locking."""
    lock_file = path.parent / f"{path.name}.lock"
    f = None
    try:
        while True:
            try:
                # Try to create lock file
                f = open(lock_file, 'w')
                # Lock the file
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except IOError:
                # Another process has the lock
                time.sleep(0.1)
        yield
    finally:
        if f is not None:
            # Release the lock
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except IOError:
                pass
            f.close()
        if lock_file.exists():
            try:
                lock_file.unlink()
            except PermissionError:
                pass

def wrapped_update(project_root: str, count: Value):
    """Update project index and increment success counter."""
    try:
        update_project(project_root)
        with count.get_lock():
            count.value += 1
    except Exception as e:
        print(f"Update failed: {e}")

class ComplexProject:
    """Helper to create a complex project structure for system testing."""
    
    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
        # Main project structure
        self.src = self.root / "src"
        self.tests = self.root / "tests"
        self.docs = self.root / "docs"
        # Submodules
        self.core = self.src / "core"
        self.utils = self.src / "utils"
        self.plugins = self.src / "plugins"
        # Test directories
        self.unit_tests = self.tests / "unit"
        self.integration_tests = self.tests / "integration"
        self.system_tests = self.tests / "system"
        # Index files
        self.main_index = self.root / "codebase_index.json"
        self.plugin_indexes = []
        
    def setup(self):
        """Create a complex project structure with multiple components."""
        # Create directory structure
        for directory in [
            self.src, self.tests, self.docs,
            self.core, self.utils, self.plugins,
            self.unit_tests, self.integration_tests, self.system_tests
        ]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Create core modules
        self._create_module(self.core / "base.py", """
class BaseComponent:
    def __init__(self):
        self.initialized = True
        
    def setup(self):
        pass
""")
        
        self._create_module(self.core / "config.py", """
from .base import BaseComponent

class Config(BaseComponent):
    def __init__(self):
        super().__init__()
        self.settings = {}
""")
        
        # Create utility modules
        self._create_module(self.utils / "helpers.py", """
from ..core.base import BaseComponent

def initialize_component(component: BaseComponent):
    component.setup()
""")
        
        # Create plugins
        for i in range(3):
            plugin_dir = self.plugins / f"plugin_{i}"
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
            self._create_module(plugin_dir / "__init__.py", f"""
from ...core.base import BaseComponent

class Plugin{i}(BaseComponent):
    def setup(self):
        print("Setting up plugin {i}")
""")
            
            # Each plugin gets its own index
            plugin_index = plugin_dir / "plugin_index.json"
            self.plugin_indexes.append(plugin_index)
            self._create_index(plugin_index)
            
        # Create test files
        self._create_module(self.unit_tests / "test_core.py", """
from src.core.base import BaseComponent
from src.core.config import Config

def test_base_component():
    component = BaseComponent()
    assert component.initialized
""")
        
        self._create_module(self.integration_tests / "test_plugins.py", """
import pytest
from src.core.base import BaseComponent
from src.plugins.plugin_0 import Plugin0

def test_plugin_inheritance():
    plugin = Plugin0()
    assert isinstance(plugin, BaseComponent)
""")
        
        # Create main index
        self._create_index(self.main_index)
        
    def _create_module(self, path: Path, content: str):
        """Create a Python module with the given content."""
        path.write_text(content.lstrip())
        
    def _create_index(self, path: Path):
        """Create an empty index file."""
        index_data = {
            "metadata": {
                "last_updated": "2024-01-01 00:00:00",
                "update_counter": 0,
                "version": "0.1.0"
            },
            "components": {},
            "dependencies": {},
            "test_coverage": {}
        }
        path.write_text(json.dumps(index_data, indent=4))
        
    def get_index_data(self, index_file: Path = None) -> Dict[str, Any]:
        """Read index data from the specified index file."""
        if index_file is None:
            index_file = self.main_index
        return json.loads(index_file.read_text())

class TestAutoIndexSystem(LLMTestCase):
    """System tests for auto-indexing functionality."""
    
    def setUp(self):
        """Create a complex project structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Set up complex project
        self.project = ComplexProject(self.temp_dir)
        self.project.setup()
        
    def test_cross_module_dependencies(self):
        """Test that dependencies across different modules are properly tracked."""
        # Index the entire project
        indexer = ToolkitIndexer(self.temp_dir)
        indexer.update_index()
        
        # Check dependencies
        index_data = self.project.get_index_data()
        dependencies = {normalize_path(k): v for k, v in index_data["dependencies"].items()}
        
        # Utils should depend on core
        utils_helpers = normalize_path("src/utils/helpers.py")
        self.assertIn(utils_helpers, dependencies)
        self.assertIn("core.base", str(dependencies[utils_helpers]))
        
        # Config should depend on base
        core_config = normalize_path("src/core/config.py")
        self.assertIn(core_config, dependencies)
        self.assertIn("base", str(dependencies[core_config]))
        
    def test_plugin_system_indexing(self):
        """Test that plugin system with multiple indexes works correctly."""
        # Add temp directory to Python path for imports
        sys.path.insert(0, str(self.temp_dir))
        self.addCleanup(lambda: sys.path.remove(str(self.temp_dir)))
        
        # Create test files in each plugin
        for i in range(3):
            plugin_dir = self.project.plugins / f"plugin_{i}"
            test_file = self.project.unit_tests / f"test_plugin_{i}.py"
            
            # Use raw string for Windows path
            plugin_dir_str = str(plugin_dir).replace("\\", "\\\\")
            self._create_module(test_file, f"""
from src.plugins.plugin_{i} import Plugin{i}

@auto_index(toolkit_root=r"{plugin_dir_str}")
def test_plugin():
    plugin = Plugin{i}()
    assert plugin.initialized
""")
            
        # Run tests for each plugin
        for i in range(3):
            test_file = self.project.unit_tests / f"test_plugin_{i}.py"
            plugin_index = self.project.plugin_indexes[i]
            
            # Import and run test
            spec = importlib.util.spec_from_file_location(f"test_plugin_{i}", test_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.test_plugin()
            
            # Verify plugin index was updated
            index_data = self.project.get_index_data(plugin_index)
            self.assertGreater(index_data["metadata"]["update_counter"], 0)
            
    def test_concurrent_project_updates(self):
        """Test that multiple processes can update indexes concurrently."""
        import multiprocessing
        
        # Shared counter to track successful updates
        success_count = Value('i', 0)
        
        # Start multiple processes to update the index
        processes = []
        for _ in range(3):
            p = multiprocessing.Process(
                target=wrapped_update, 
                args=(self.temp_dir, success_count)
            )
            p.start()
            processes.append(p)
            
        # Wait for all processes to complete
        for p in processes:
            p.join()
            
        # Verify all processes succeeded
        self.assertEqual(success_count.value, 3)
            
        # Verify index integrity
        index_data = self.project.get_index_data()
        self.assertGreaterEqual(index_data["metadata"]["update_counter"], 3)
        self.assertGreater(len(index_data["components"]), 0)
        
    def test_large_codebase_performance(self):
        """Test indexer performance with a large number of files."""
        # Create many additional modules
        for i in range(100):
            module_path = self.project.src / f"module_{i}.py"
            self._create_module(module_path, f"""
# Module {i}
def function_{i}():
    pass

class Class_{i}:
    pass
""")
            
            test_path = self.project.unit_tests / f"test_module_{i}.py"
            self._create_module(test_path, f"""
from src.module_{i} import function_{i}, Class_{i}

def test_function_{i}():
    function_{i}()
    
def test_class_{i}():
    obj = Class_{i}()
""")
            
        # Time the indexing operation
        import time
        start_time = time.time()
        
        indexer = ToolkitIndexer(self.temp_dir)
        indexer.update_index()
        
        duration = time.time() - start_time
        
        # Verify performance
        self.assertLess(duration, 5.0)  # Should complete in under 5 seconds
        
        # Verify all modules were indexed
        index_data = self.project.get_index_data()
        self.assertGreaterEqual(len(index_data["components"]), 100)
        
    def _create_module(self, path: Path, content: str):
        """Helper to create a Python module during tests."""
        path.write_text(content.lstrip())

if __name__ == '__main__':
    unittest.main() 