# Auto-indexing decorator for AI toolkit tests.
#
# This module provides a decorator that automatically updates the toolkit index
# whenever tests are run, ensuring the dependency map stays current.
#

import functools
import os
import logging
from pathlib import Path
from typing import Optional, Callable, Union

from ai_toolkit.tools.toolkit_indexer import ToolkitIndexer

logger = logging.getLogger(__name__)

def auto_index(func: Optional[Callable] = None, *, toolkit_root: Optional[Union[str, Path]] = None):
    """Decorator that updates the toolkit index after running tests.
    
    Can be used with or without arguments:
    
    @auto_index  # Uses current directory as toolkit root
    def test_something():
        pass
        
    @auto_index(toolkit_root='/path/to/toolkit')  # Specifies toolkit root
    def test_something():
        pass
    
    Args:
        func: The function to wrap (when used without arguments)
        toolkit_root: Optional path to toolkit root directory. If not provided,
                     uses current working directory.
    """
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            try:
                result = test_func(*args, **kwargs)
                # Only update index if test passes
                root = toolkit_root or os.getcwd()
                try:
                    indexer = ToolkitIndexer(root)
                    indexer.update_index()
                    logger.info(f"Updated codebase index for {root}")
                except Exception as e:
                    logger.warning(f"Failed to update codebase index: {e}")
                return result
            except:
                # Don't update index if test fails
                raise
        return wrapper
        
    if func is None:
        return decorator
    return decorator(func)
    
def auto_index_class(cls: Optional[type] = None, *, toolkit_root: Optional[Union[str, Path]] = None):
    """Class decorator that adds auto-indexing to all test methods.
    
    Can be used with or without arguments:
    
    @auto_index_class  # Uses current directory as toolkit root
    class TestSomething:
        pass
        
    @auto_index_class(toolkit_root='/path/to/toolkit')  # Specifies toolkit root
    class TestSomething:
        pass
    """
    def decorator(test_cls):
        # Create a descriptor class for method binding
        class BoundMethodDescriptor:
            def __init__(self, wrapped_method):
                self.wrapped_method = wrapped_method
                
            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self.wrapped_method
                return self.wrapped_method.__get__(obj, objtype)
                
        # Track original methods to avoid double wrapping
        wrapped_methods = set()
        
        # Wrap all test methods, including inherited ones
        for name in dir(test_cls):
            if name.startswith('test_'):
                # Get the attribute descriptor
                attr = test_cls.__dict__.get(name)
                if attr is None:  # Method from parent class
                    attr = getattr(test_cls, name)
                
                # Only wrap if callable and not already wrapped
                if callable(attr) and not hasattr(attr, '_auto_index_wrapped'):
                    wrapped = auto_index(attr, toolkit_root=toolkit_root)
                    wrapped._auto_index_wrapped = True
                    
                    # Use descriptor for proper method binding
                    setattr(test_cls, name, BoundMethodDescriptor(wrapped))
                    wrapped_methods.add(name)
        
        # Store the wrapped methods on the class for child classes to check
        test_cls._auto_index_wrapped_methods = wrapped_methods
        
        # Create a new __init_subclass__ to handle child class methods
        original_init_subclass = getattr(test_cls, '__init_subclass__', lambda *args, **kwargs: None)
        def __init_subclass__(cls, **kwargs):
            original_init_subclass(**kwargs)
            # Wrap any new test methods in the child class
            for name, attr in cls.__dict__.items():
                if name.startswith('test_') and callable(attr):
                    if not hasattr(attr, '_auto_index_wrapped'):
                        wrapped = auto_index(attr, toolkit_root=toolkit_root)
                        wrapped._auto_index_wrapped = True
                        setattr(cls, name, BoundMethodDescriptor(wrapped))
        
        test_cls.__init_subclass__ = classmethod(__init_subclass__)
        return test_cls
        
    if cls is None:
        return decorator
    return decorator(cls) 