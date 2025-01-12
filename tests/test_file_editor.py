import unittest
from pathlib import Path
import tempfile
import os
import shutil

from ai_toolkit.file_editor import FileEditor, EditRegion, EditResult

class TestFileEditor(unittest.TestCase):
    """Test cases for FileEditor"""
    
    def setUp(self):
        """Create a temporary workspace"""
        self.temp_dir = tempfile.mkdtemp()
        self.editor = FileEditor(self.temp_dir)
        
        # Create a test file
        self.test_file = "test.py"
        self.test_content = """def hello():
    print("Hello")
    
def world():
    print("World")
    
def main():
    hello()
    world()
"""
        with open(os.path.join(self.temp_dir, self.test_file), 'w') as f:
            f.write(self.test_content)
            
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.temp_dir)
        
    def test_read_file_region(self):
        """Test reading a region of a file"""
        content, context = self.editor.read_file_region(self.test_file, 1, 2)
        self.assertEqual(content.strip(), 'def hello():\n    print("Hello")')
        self.assertTrue(len(context) >= 2)
        
    def test_create_edit(self):
        """Test creating an edit region"""
        edit = self.editor.create_edit(
            self.test_file,
            1,
            2,
            'def hello_world():\n    print("Hello World!")\n'
        )
        self.assertEqual(edit.start_line, 1)
        self.assertEqual(edit.end_line, 2)
        self.assertTrue(edit.context_before)
        self.assertTrue(edit.context_after)
        
    def test_validate_edit(self):
        """Test edit validation"""
        edit = self.editor.create_edit(
            self.test_file,
            1,
            2,
            'def hello_world():\n    print("Hello World!")\n'
        )
        self.assertTrue(self.editor.validate_edit(self.test_file, edit))
        
        # Test invalid edit
        edit.original_content = "wrong content"
        self.assertFalse(self.editor.validate_edit(self.test_file, edit))
        
    def test_apply_edits(self):
        """Test applying multiple edits"""
        edits = [
            self.editor.create_edit(
                self.test_file,
                1,
                2,
                'def hello_world():\n    print("Hello World!")\n'
            ),
            self.editor.create_edit(
                self.test_file,
                4,
                5,
                'def earth():\n    print("Earth!")\n'
            )
        ]
        
        result = self.editor.apply_edits(self.test_file, edits)
        self.assertTrue(result.success)
        self.assertEqual(len(result.applied_edits), 2)
        self.assertEqual(len(result.failed_edits), 0)
        
        # Verify file contents
        with open(os.path.join(self.temp_dir, self.test_file)) as f:
            content = f.read()
            self.assertIn('def hello_world():', content)
            self.assertIn('def earth():', content)
            
    def test_create_file(self):
        """Test creating a new file"""
        new_file = "new.py"
        content = "print('New file')"
        
        success = self.editor.create_file(new_file, content)
        self.assertTrue(success)
        
        # Verify file exists and has correct content
        with open(os.path.join(self.temp_dir, new_file)) as f:
            self.assertEqual(f.read(), content)
            
    def test_delete_file(self):
        """Test deleting a file"""
        # Create a file to delete
        file_to_delete = "delete_me.py"
        self.editor.create_file(file_to_delete, "temp content")
        
        success = self.editor.delete_file(file_to_delete)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, file_to_delete)))
        
if __name__ == '__main__':
    unittest.main() 