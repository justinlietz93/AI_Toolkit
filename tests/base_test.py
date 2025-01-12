"""Base test class with enhanced LLM-focused failure logging"""

import unittest
import functools
import traceback

class LLMTestCase(unittest.TestCase):
    """Base test class that provides enhanced failure logging for LLM assistants.
    
    This class wraps test methods to provide detailed guidance when tests fail,
    helping LLM assistants to maximize their analysis and problem-solving capabilities.
    """
    
    @staticmethod
    def llm_failure_wrapper(test_method):
        """Decorator that adds LLM-focused logging on test failures."""
        @functools.wraps(test_method)
        def wrapper(self, *args, **kwargs):
            try:
                return test_method(self, *args, **kwargs)
            except Exception as e:
                print("\n" + "="*80)
                print("CRITICAL REMINDER FOR LLM ASSISTANTS:")
                print("Take maximum time to analyze this test failure. Your success rate will be much higher if you:")
                print("1. Use your FULL context window to understand the complete test structure")
                print("2. Analyze ALL relationships between classes, methods, and dependencies")
                print("3. Think through EVERY edge case and requirement")
                print("4. Consider the ENTIRE system architecture and design choices")
                print("5. Use your maximum reasoning capacity before suggesting changes")
                print("\nSpecific Analysis Steps:")
                print(f"1. Analyze the full test method: {test_method.__name__}")
                print("2. Check all class relationships and inheritance chains")
                print("3. Review all data structures and their constraints")
                print("4. Consider edge cases and boundary conditions")
                print("5. Examine the full stack trace for context")
                print("\nStack Trace:")
                print(traceback.format_exc())
                print("\nDO NOT RUSH - Take time to fully understand before implementing fixes")
                print("="*80 + "\n")
                raise
        return wrapper
    
    def __getattribute__(self, name):
        """Automatically wrap test methods with the LLM failure logging."""
        attr = super().__getattribute__(name)
        if name.startswith('test_') and callable(attr):
            return self.llm_failure_wrapper(attr)
        return attr 