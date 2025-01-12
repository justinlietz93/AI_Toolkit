# AI Toolkit - Code Analyzer
# Advanced code analysis capabilities for better context understanding

import ast
from pathlib import Path
from typing import List, Dict, Set, Optional, Union
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class CodeSymbol:
    """Represents a code symbol (function, class, variable)"""
    name: str
    type: str  # 'function', 'class', 'variable', etc.
    line_number: int
    end_line: int
    docstring: Optional[str]
    parent: Optional[str]  # Parent class/function name if any
    dependencies: frozenset[str]  # Other symbols this depends on

@dataclass
class CodeContext:
    """Represents the context around a code region"""
    symbols: Dict[str, CodeSymbol]
    imports: List[str]
    scope_stack: List[str]  # Stack of nested scopes
    docstring: Optional[str]
    file_path: str

class CodeAnalyzer:
    """Advanced code analyzer for understanding context"""
    
    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root)
        
    def analyze_file(self, file_path: str) -> CodeContext:
        """Analyze an entire file"""
        abs_path = self.workspace_root / file_path
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        symbols = {}
        imports = []
        
        # Extract file-level docstring
        docstring = ast.get_docstring(tree)
        
        class SymbolVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_parent = None
                self.scope_stack = []
                self.current_dependencies = set()
                
            def visit_ClassDef(self, node):
                name = node.name
                # Collect base class dependencies
                base_deps = set()
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_deps.add(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_deps.add(base.attr)
                        
                symbol = CodeSymbol(
                    name=name,
                    type='class',
                    line_number=node.lineno,
                    end_line=node.end_lineno,
                    docstring=ast.get_docstring(node),
                    parent=self.current_parent,
                    dependencies=frozenset(base_deps)
                )
                symbols[name] = symbol
                
                old_parent = self.current_parent
                old_deps = self.current_dependencies
                self.current_parent = name
                self.current_dependencies = set()
                self.scope_stack.append(name)
                
                self.generic_visit(node)
                
                self.scope_stack.pop()
                self.current_parent = old_parent
                self.current_dependencies = old_deps
                
            def visit_FunctionDef(self, node):
                name = node.name
                if self.current_parent:
                    full_name = f"{self.current_parent}.{name}"
                else:
                    full_name = name
                    
                # Analyze function body for dependencies
                deps = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                        deps.add(child.id)
                    elif isinstance(child, ast.Attribute):
                        if isinstance(child.value, ast.Name):
                            deps.add(child.value.id)
                        deps.add(child.attr)
                        
                # Add parent class dependencies for methods
                if self.current_parent:
                    parent_symbol = symbols.get(self.current_parent)
                    if parent_symbol:
                        deps.update(parent_symbol.dependencies)
                        
                symbol = CodeSymbol(
                    name=full_name,
                    type='function',
                    line_number=node.lineno,
                    end_line=node.end_lineno,
                    docstring=ast.get_docstring(node),
                    parent=self.current_parent,
                    dependencies=frozenset(deps)
                )
                symbols[full_name] = symbol
                
                old_deps = self.current_dependencies
                self.current_dependencies = deps
                self.scope_stack.append(full_name)
                
                self.generic_visit(node)
                
                self.scope_stack.pop()
                self.current_dependencies = old_deps
                
            def visit_Import(self, node):
                for name in node.names:
                    imports.append(name.name)
                    
            def visit_ImportFrom(self, node):
                module = node.module or ''
                for name in node.names:
                    imports.append(f"{module}.{name.name}")
                    
        visitor = SymbolVisitor()
        visitor.visit(tree)
        
        return CodeContext(
            symbols=symbols,
            imports=imports,
            scope_stack=visitor.scope_stack,
            docstring=docstring,
            file_path=file_path
        )
        
    def get_context_at_line(self, file_path: str, line_number: int) -> CodeContext:
        """Get the code context (symbols + scope stack) for a specific line.
        
        This method properly handles nested scopes by:
        1. Finding all symbols containing the target line
        2. Walking up parent chains while validating line ranges
        3. Sorting from outermost to innermost scope
        4. Building a properly ordered scope stack
        """
        context = self.analyze_file(file_path)
        
        # Debug: Print all symbols and their line ranges
        print(f"\nLooking for line {line_number} in symbols:")
        for name, sym in context.symbols.items():
            print(f"{name}: lines {sym.line_number}-{sym.end_line}")
        
        # We'll collect all symbols that contain line_number
        # plus all their parent symbols whose line range also contains line_number
        containing_symbols = set()
        relevant_symbols = {}  # All symbols that should be accessible

        def add_symbol_and_parents(sym: CodeSymbol):
            """Recursively add a symbol and its parents if they contain the line_number."""
            # Make sure sym's range actually includes this line
            if sym.line_number <= line_number <= sym.end_line:
                print(f"Found containing symbol: {sym.name} ({sym.line_number}-{sym.end_line})")
                containing_symbols.add(sym)
                # Add this symbol and any referenced symbols to the relevant set
                relevant_symbols[sym.name] = sym
                for dep in sym.dependencies:
                    if dep in context.symbols:
                        relevant_symbols[dep] = context.symbols[dep]
                
                if sym.parent and sym.parent in context.symbols:
                    parent_sym = context.symbols[sym.parent]
                    # Only follow the chain if the parent's lines also contain this line
                    if parent_sym.line_number <= line_number <= parent_sym.end_line:
                        print(f"Following parent: {parent_sym.name} ({parent_sym.line_number}-{parent_sym.end_line})")
                        add_symbol_and_parents(parent_sym)

        # 1. Find direct matches
        for sym in context.symbols.values():
            if sym.line_number <= line_number <= sym.end_line:
                add_symbol_and_parents(sym)

        # Now we have a set of symbols (including parents) that truly enclose line_number
        # 2. Sort them from outermost to innermost (lowest line_number first)
        sorted_symbols = sorted(containing_symbols, key=lambda s: s.line_number)
        
        # 3. Build the scope stack in sorted order
        scope_stack = [sym.name for sym in sorted_symbols]
        print(f"\nFinal scope stack: {scope_stack}")

        return CodeContext(
            symbols=relevant_symbols,  # Use the complete set of relevant symbols
            imports=context.imports,
            scope_stack=scope_stack,
            docstring=context.docstring,
            file_path=file_path
        )
        
    def find_symbol_references(self, file_path: str, symbol_name: str) -> List[int]:
        """Find all references to a symbol in a file"""
        abs_path = self.workspace_root / file_path
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Use regex to find all references
        # This is a simple approach - for more accuracy, use the ast
        pattern = r'\b' + re.escape(symbol_name) + r'\b'
        references = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(pattern, line):
                references.append(i)
                
        return references
        
    def get_symbol_dependencies(self, file_path: str, symbol_name: str) -> Set[str]:
        """Get all symbols that the given symbol depends on.
        
        This method:
        1. Gets the direct dependencies of the symbol from its frozenset
        2. If it's a method, includes the parent class's dependencies
        3. Returns a mutable set for the caller to use
        
        Args:
            file_path: Path to the file containing the symbol
            symbol_name: Name of the symbol to analyze (e.g. 'TestClass.test_method')
            
        Returns:
            Set of symbol names that this symbol depends on
        """
        context = self.analyze_file(file_path)
        if symbol_name not in context.symbols:
            return set()
            
        symbol = context.symbols[symbol_name]
        
        # Start with a mutable copy of the symbol's dependencies
        dependencies = set(symbol.dependencies)
        
        # Also add parent class dependencies if this is a method
        if '.' in symbol_name:
            class_name = symbol_name.split('.')[0]
            if class_name in context.symbols:
                # Union with parent's dependencies
                dependencies.update(context.symbols[class_name].dependencies)
                
        return dependencies 