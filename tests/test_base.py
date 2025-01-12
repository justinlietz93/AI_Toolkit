"""Tests for the base test class with enhanced LLM-focused failure logging"""

import unittest
import io
import sys
import functools
import traceback
from contextlib import contextmanager

@contextmanager
def capture_stdout():
    """Capture stdout for testing print statements"""
    stdout = sys.stdout
    stream = io.StringIO()
    sys.stdout = stream
    try:
        yield stream
    finally:
        sys.stdout = stdout

class LLMTestCase(unittest.TestCase):
    """Base test class that provides enhanced failure logging for LLM assistants.
    
    This class wraps test methods to provide detailed guidance when tests fail,
    helping LLM assistants to maximize their analysis and problem-solving capabilities.
    """
    
    def llm_failure_wrapper(self, test_method):
        """Decorator that adds LLM-focused logging on test failures."""
        @functools.wraps(test_method)
        def wrapper(*args, **kwargs):
            try:
                # If this is a bound method, args[0] is self
                if len(args) > 0 and isinstance(args[0], LLMTestCase):
                    return test_method(*args[1:], **kwargs)
                return test_method(*args, **kwargs)
            except Exception as e:
                print("\n" + "!"*100)
                print("""
   ▄████████    ▄████████  ▄█      ███        ▄█    █▄       ▄████████    ▄████████ 
  ███    ███   ███    ███ ███  ▀█████████▄   ███    ███     ███    ███   ███    ███ 
  ███    █▀    ███    ███ ███▌    ▀███▀▀██   ███    ███     ███    █▀    ███    ███ 
  ███         ▄███▄▄▄▄██▀ ███▌     ███   ▀  ▄███▄▄▄▄███▄▄  ▄███▄▄▄      ▄███▄▄▄▄██▀ 
▀███████████ ▀▀███▀▀▀▀▀   ███▌     ███     ▀▀███▀▀▀▀███▀  ▀▀███▀▀▀     ▀▀███▀▀▀▀▀   
         ███ ▀███████████ ███      ███       ███    ███     ███    █▄  ▀███████████ 
   ▄█    ███   ███    ███ ███      ███       ███    ███     ███    ███   ███    ███ 
 ▄████████▀    ███    ███ █▀      ▄████▀     ███    █▀      ██████████   ███    ███ 
                ███    ███                                                 ███    ███ 
                """)
                print("\n" + "!"*100)
                print("\n[STACK TRACE - READ THIS FIRST]:")
                print(traceback.format_exc())
                print("\n" + "!"*100)
                print("\n[CRITICAL ERROR] TEST FAILURE DETECTED - IMMEDIATE ANALYSIS REQUIRED")
                print("!"*100)
                print("""
⚠️  DANGER: DO NOT PROCEED WITHOUT COMPLETING ALL ANALYSIS STEPS  ⚠️
---------------------------------------------------------
                """)
                print("🛑 PHASE 1: STOP AND ANALYZE")
                print("   ▶ Read the COMPLETE stack trace above")
                print("   ▶ Understand the FULL test structure")
                print("   ▶ Identify ALL relevant components")
                print("\n🔍 PHASE 2: DEEP INVESTIGATION")
                print(f"   ▶ Failed Test: {test_method.__name__}")
                print("   ▶ Analyze class relationships and inheritance")
                print("   ▶ Review data structures and constraints")
                print("   ▶ Consider edge cases and boundary conditions")
                print("\n⚠️  PHASE 3: PRE-IMPLEMENTATION VERIFICATION")
                print("   ▶ System architecture impact assessment")
                print("   ▶ Dependency chain verification")
                print("   ▶ Side effect analysis")
                print("""
---------------------------------------------------------
❌ CRITICAL WARNING: Changes without complete analysis will be REJECTED
❌ CRITICAL WARNING: Incomplete understanding leads to system damage
❌ CRITICAL WARNING: Take MAXIMUM time to analyze before proceeding
---------------------------------------------------------
                """)
                print("!"*100 + "\n")
                raise
        return wrapper
    
    def __getattribute__(self, name):
        """Automatically wrap test methods with the LLM failure logging."""
        attr = super().__getattribute__(name)
        if name.startswith('test_') and callable(attr):
            return self.llm_failure_wrapper(attr)
        return attr

class TestLLMTestCase(unittest.TestCase):
    """Tests for the LLMTestCase base class"""
    
    def test_successful_test_not_logged(self):
        """Verify that successful tests don't trigger logging"""
        
        class SampleTest(LLMTestCase):
            def test_success(self):
                self.assertTrue(True)
        
        with capture_stdout() as output:
            test = SampleTest('test_success')
            test.test_success()
            
        self.assertEqual(output.getvalue(), '')
    
    def test_failed_test_logged(self):
        """Verify that failed tests trigger detailed logging"""
        
        class SampleTest(LLMTestCase):
            def test_failure(self):
                raise ValueError("Test failure")
        
        with capture_stdout() as output:
            test = SampleTest('test_failure')
            with self.assertRaises(ValueError):
                test.test_failure()
            
        log_output = output.getvalue()
        
        # Verify key logging elements
        self.assertIn("CRITICAL REMINDER FOR LLM ASSISTANTS", log_output)
        self.assertIn("Use your FULL context window", log_output)
        self.assertIn("test_failure", log_output)
        self.assertIn("DO NOT RUSH", log_output)
        self.assertIn("ValueError: Test failure", log_output)
    
    def test_non_test_method_not_wrapped(self):
        """Verify that non-test methods aren't wrapped"""
        
        class SampleTest(LLMTestCase):
            def helper_method(self):
                raise ValueError("Helper failure")
        
        with capture_stdout() as output:
            test = SampleTest('helper_method')
            with self.assertRaises(ValueError):
                test.helper_method()
            
        self.assertEqual(output.getvalue(), '')

if __name__ == '__main__':
    unittest.main() 