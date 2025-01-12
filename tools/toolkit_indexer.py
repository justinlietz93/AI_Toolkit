#AI Toolkit Self-Indexing System
#
#This module provides self-indexing capabilities for the AI toolkit,
#maintaining a map of dependencies and relationships between toolkit components
#without affecting the parent codebase.
#
#Version: 0.1.0
#Created: 2025-01-12
#

import os
import ast
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional

class ToolkitIndexer:
    """Maintains an index of AI toolkit components and their relationships."""
    
    def __init__(self, toolkit_root: str):
        """Initialize the indexer with the toolkit root directory.
        
        Args:
            toolkit_root: Path to the AI toolkit root directory
        """
        self.root = Path(toolkit_root)
        self.index_file = self.root / "codebase_index.json"
        self.components: Dict[str, Dict] = {}
        self.dependencies: Dict[str, Set[str]] = {}
        self.test_coverage: Dict[str, List[str]] = {}
        self.update_counter = 0
        
        # Load existing index if it exists
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                data = json.load(f)
                self.components = data.get('components', {})
                self.dependencies = {k: set(v) for k, v in data.get('dependencies', {}).items()}
                self.test_coverage = data.get('test_coverage', {})
                self.update_counter = data.get('metadata', {}).get('update_counter', 0)
        
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a Python file for components and dependencies.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Dict containing file analysis results
        """
        with open(file_path, 'r') as f:
            content = f.read()
            
        tree = ast.parse(content)
        analyzer = ComponentAnalyzer(file_path.stem)
        analyzer.visit(tree)
        
        return {
            'imports': analyzer.imports,
            'classes': analyzer.classes,
            'functions': analyzer.functions,
            'dependencies': analyzer.dependencies
        }
        
    def update_index(self):
        """Update the toolkit index by analyzing all Python files."""
        # Increment update counter
        self.update_counter += 1
        
        # Keep track of seen files to remove stale entries
        seen_files = set()
        
        # Analyze all Python files in toolkit
        for file_path in self.root.rglob('*.py'):
            if file_path.is_file() and not str(file_path).endswith('__init__.py'):
                rel_path = str(file_path.relative_to(self.root))
                seen_files.add(rel_path)
                analysis = self.analyze_file(file_path)
                
                # Record components
                self.components[rel_path] = {
                    'classes': list(analysis['classes']),
                    'functions': list(analysis['functions']),
                    'last_update': self.update_counter
                }
                
                # Record dependencies
                self.dependencies[rel_path] = analysis['dependencies']
                
                # Record test coverage if this is a test file
                if 'test_' in file_path.stem:
                    covered_components = self._extract_tested_components(analysis)
                    for component in covered_components:
                        if component not in self.test_coverage:
                            self.test_coverage[component] = []
                        if rel_path not in self.test_coverage[component]:
                            self.test_coverage[component].append(rel_path)
        
        # Remove stale entries
        self.components = {k: v for k, v in self.components.items() if k in seen_files}
        self.dependencies = {k: v for k, v in self.dependencies.items() if k in seen_files}
        self.test_coverage = {k: [f for f in v if f in seen_files] 
                            for k, v in self.test_coverage.items()}
        
        self._save_index_json()
        
    def _extract_tested_components(self, analysis: Dict) -> Set[str]:
        """Extract components being tested from test file analysis."""
        tested = set()
        
        # Look for test class names that match component names
        for class_name in analysis['classes']:
            if class_name.startswith('Test'):
                tested_name = class_name[4:]  # Remove 'Test' prefix
                if tested_name:
                    tested.add(tested_name)
                    
        # Also add the file being tested as a component
        tested.add(self.root.stem)
                    
        return tested
        
    def _save_index_json(self):
        """Save the current index state to JSON."""
        index_data = {
            'metadata': {
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'update_counter': self.update_counter,
                'version': '0.1.0'
            },
            'components': self.components,
            'dependencies': {k: list(v) for k, v in self.dependencies.items()},
            'test_coverage': self.test_coverage
        }
        
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        with open(self.index_file, 'w') as f:
            json.dump(index_data, f, indent=4)

class ComponentAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze Python file components and dependencies."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.imports: Set[str] = set()
        self.classes: Set[str] = set()
        self.functions: Set[str] = set()
        self.dependencies: Set[str] = set()
        
    def visit_Import(self, node):
        """Record import statements."""
        for name in node.names:
            self.imports.add(name.name)
            if not name.name.startswith('__'):
                self.dependencies.add(name.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Record from-import statements."""
        if node.module:
            self.imports.add(node.module)
            if not node.module.startswith('__'):
                self.dependencies.add(node.module)
        for name in node.names:
            full_name = f"{node.module}.{name.name}" if node.module else name.name
            self.imports.add(full_name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        """Record class definitions."""
        self.classes.add(node.name)
        # Record base classes as dependencies
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.dependencies.add(base.id)
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        """Record function definitions."""
        self.functions.add(node.name)
        self.generic_visit(node)

def update_toolkit_index(toolkit_root: Optional[str] = None):
    """Update the AI toolkit index.
    
    Args:
        toolkit_root: Optional path to toolkit root. If not provided,
                     will attempt to detect from current file location.
    """
    if toolkit_root is None:
        # Try to detect toolkit root from this file's location
        current_file = Path(__file__)
        toolkit_root = current_file.parent.parent
        
    indexer = ToolkitIndexer(toolkit_root)
    indexer.update_index()
    
if __name__ == '__main__':
    update_toolkit_index() 