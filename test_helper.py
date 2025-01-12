# AI Toolkit - Test Helper
# Assists in test creation and validation

import ast
from pathlib import Path
from typing import List, Dict, Set, Optional, Union, Tuple
from dataclasses import dataclass
import inspect
import re

@dataclass
class TestCase:
    """Represents a test case to be generated"""
    function_name: str
    description: str
    assertions: List[str]
    setup_code: str = ""
    teardown_code: str = ""
    dependencies: Set[str] = None

@dataclass
class TestAnalysis:
    """Analysis of existing tests"""
    coverage: float
    missing_assertions: List[str]
    unused_setup: List[str]
    suggestions: List[str]

class TestHelper:
    """Helper for test creation and analysis"""
    
    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root)
        
    def analyze_test_file(self, test_file: str) -> TestAnalysis:
        """Analyze a test file for completeness and quality"""
        abs_path = self.workspace_root / test_file
        if not abs_path.exists():
            raise FileNotFoundError(f"Test file not found: {test_file}")
            
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        
        # Track various metrics
        total_functions = 0
        tested_functions = 0
        assertions = []
        setup_vars = set()
        used_vars = set()
        suggestions = []
        has_setup = False
        in_setup = False
        
        class TestVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                nonlocal total_functions, tested_functions, has_setup, in_setup
                
                if node.name == 'setUp':
                    has_setup = True
                    in_setup = True
                    # Process setup function body
                    for child in ast.walk(node):
                        if isinstance(child, ast.Assign):
                            for target in child.targets:
                                if isinstance(target, ast.Attribute):
                                    if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                        setup_vars.add(target.attr)
                                elif isinstance(target, ast.Name):
                                    setup_vars.add(target.id)
                    self.generic_visit(node)
                    in_setup = False
                elif node.name.startswith('test_'):
                    total_functions += 1
                    
                    # Check if function has assertions
                    has_assertions = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Attribute):
                                if child.func.attr.startswith('assert'):
                                    has_assertions = True
                                    assertions.append(child)
                        elif isinstance(child, ast.Name):
                            if isinstance(child.ctx, ast.Load):
                                used_vars.add(child.id)
                        elif isinstance(child, ast.Attribute):
                            if isinstance(child.value, ast.Name) and child.value.id == 'self':
                                used_vars.add(child.attr)
                                    
                    if has_assertions:
                        tested_functions += 1
                    else:
                        suggestions.append(f"Test function {node.name} has no assertions")
                        
                    self.generic_visit(node)
                else:
                    self.generic_visit(node)
                
        visitor = TestVisitor()
        visitor.visit(tree)
        
        # Calculate coverage
        coverage = (tested_functions / total_functions * 100) if total_functions > 0 else 0
        
        # Find unused setup
        unused_setup = setup_vars - used_vars
        
        # Generate additional suggestions
        if len(assertions) < total_functions * 2:
            suggestions.append("Consider adding more assertions per test")
            
        if not has_setup:
            suggestions.append("Consider adding setUp method for common initialization")
            
        if unused_setup:
            suggestions.append(f"Remove unused setup variables: {', '.join(unused_setup)}")
            
        return TestAnalysis(
            coverage=coverage,
            missing_assertions=[],  # Would need source code to determine missing assertions
            unused_setup=list(unused_setup),
            suggestions=suggestions
        )
        
    def generate_test_case(self, source_file: str, function_name: str) -> TestCase:
        """Generate a test case for a function"""
        abs_path = self.workspace_root / source_file
        if not abs_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
            
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        
        # Find the function and its class (if any)
        class FunctionFinder(ast.NodeVisitor):
            def __init__(self):
                self.found_function = None
                self.parent_class = None
                self.current_class = None
                self.dependencies = set()
                
            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node
                self.generic_visit(node)
                self.current_class = old_class
                
            def visit_FunctionDef(self, node):
                if node.name == function_name:
                    self.found_function = node
                    self.parent_class = self.current_class
                    # Collect dependencies
                    for child in ast.walk(node):
                        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                            self.dependencies.add(child.id)
                            
        finder = FunctionFinder()
        finder.visit(tree)
        
        if not finder.found_function:
            raise ValueError(f"Function {function_name} not found in {source_file}")
            
        # Generate test case
        func_node = finder.found_function
        
        # Extract docstring for description
        description = ast.get_docstring(func_node) or f"Test {function_name} functionality"
        
        # Generate assertions based on return type hints
        assertions = []
        returns = None
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                returns = node
                break
                
        # Generate setup code
        setup_code = ""
        if finder.parent_class:
            class_name = finder.parent_class.name
            setup_code = f"instance = {class_name}()"
            
        if returns:
            if setup_code:
                assertions.append(f"result = instance.{function_name}()")
            else:
                assertions.append(f"result = {function_name}()")
            assertions.append(f"self.assertIsNotNone(result)")
            
        # Add type checking if return annotation exists
        if hasattr(func_node, 'returns') and func_node.returns:
            type_name = func_node.returns.id if isinstance(func_node.returns, ast.Name) else 'object'
            assertions.append(f"self.assertIsInstance(result, {type_name})")
            
        return TestCase(
            function_name=f"test_{function_name}",
            description=description,
            assertions=assertions or ["self.assertTrue(True)  # Add specific assertions"],
            setup_code=setup_code,
            teardown_code="# Add teardown code if needed",
            dependencies=finder.dependencies
        )
        
    def suggest_test_improvements(self, test_file: str) -> List[str]:
        """Suggest improvements for a test file"""
        analysis = self.analyze_test_file(test_file)
        
        suggestions = analysis.suggestions.copy()
        
        # Add suggestions based on analysis
        if analysis.coverage < 80:
            suggestions.append(f"Increase test coverage (currently {analysis.coverage:.1f}%)")
            
        if analysis.unused_setup:
            suggestions.append(f"Remove unused setup variables: {', '.join(analysis.unused_setup)}")
            
        return suggestions
        
    def generate_test_file(self, source_file: str) -> Tuple[str, List[TestCase]]:
        """Generate a complete test file for a source file"""
        abs_path = self.workspace_root / source_file
        if not abs_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
            
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        
        # Collect all functions and classes
        test_cases = []
        
        class Collector(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None
                
            def visit_ClassDef(self, node):
                # Add class-level test case
                test_cases.append(TestCase(
                    function_name=f"test_{node.name}_creation",
                    description=f"Test {node.name} class instantiation",
                    assertions=[f"self.assertIsInstance(instance, {node.name})"],
                    setup_code=f"instance = {node.name}()"
                ))
                
                old_class = self.current_class
                self.current_class = node
                self.generic_visit(node)
                self.current_class = old_class
                
            def visit_FunctionDef(self, node):
                if not node.name.startswith('_'):  # Skip private functions
                    try:
                        test_case = TestHelper(abs_path.parent).generate_test_case(
                            source_file,
                            node.name
                        )
                        test_cases.append(test_case)
                    except Exception:
                        pass
                self.generic_visit(node)
                
        collector = Collector()
        collector.visit(tree)
        
        # Generate test file content
        file_content = f"""# Generated test file for {source_file}
import unittest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from {source_file.replace('/', '.')} import *

class Test{Path(source_file).stem.capitalize()}(unittest.TestCase):
    \"\"\"Test cases for {source_file}\"\"\"
    
    def setUp(self):
        \"\"\"Set up test fixtures\"\"\"
        pass
        
    def tearDown(self):
        \"\"\"Clean up after tests\"\"\"
        pass
        
"""
        
        # Add test cases
        for test_case in test_cases:
            file_content += f"""
    def {test_case.function_name}(self):
        \"\"\"{test_case.description}\"\"\"
        {test_case.setup_code}
        
        # Add test implementation here
        
        {chr(10).join(f'        {assertion}' for assertion in test_case.assertions)}
        
        {test_case.teardown_code}
"""
        
        return file_content, test_cases 