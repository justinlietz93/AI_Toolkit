# AI Toolkit - File Editor
# Advanced file editing capabilities for AI operations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Union
import difflib

@dataclass
class EditRegion:
    """Represents a region of code to be edited"""
    start_line: int  # 1-indexed
    end_line: int    # 1-indexed
    original_content: str
    new_content: str
    context_before: str = ""  # Lines before for context
    context_after: str = ""   # Lines after for context

@dataclass
class EditResult:
    """Result of an edit operation"""
    success: bool
    message: str
    diff: str
    applied_edits: List[EditRegion]
    failed_edits: List[EditRegion]

class FileEditor:
    """Advanced file editor with support for multi-point edits"""
    
    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root)
        self.context_lines = 3  # Number of context lines to keep
        
    def read_file_region(self, file_path: str, start_line: int, end_line: int) -> Tuple[str, List[str]]:
        """Read a specific region of a file with context"""
        abs_path = self.workspace_root / file_path
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Calculate context ranges
        context_start = max(0, start_line - 1 - self.context_lines)
        context_end = min(len(lines), end_line + self.context_lines)
        
        # Extract main content and context
        main_content = ''.join(lines[start_line-1:end_line])
        context_lines = lines[context_start:context_end]
        
        return main_content, context_lines
        
    def create_edit(self, file_path: str, start_line: int, end_line: int, new_content: str) -> EditRegion:
        """Create an edit region with proper context"""
        content, context = self.read_file_region(file_path, start_line, end_line)
        
        # Split context into before and after
        context_before = ''.join(context[:self.context_lines])
        context_after = ''.join(context[-self.context_lines:])
        
        return EditRegion(
            start_line=start_line,
            end_line=end_line,
            original_content=content,
            new_content=new_content,
            context_before=context_before,
            context_after=context_after
        )
        
    def validate_edit(self, file_path: str, edit: EditRegion) -> bool:
        """Validate that an edit can be applied"""
        try:
            content, _ = self.read_file_region(file_path, edit.start_line, edit.end_line)
            # Check if the content matches what we expect
            return content.strip() == edit.original_content.strip()
        except Exception:
            return False
            
    def apply_edits(self, file_path: str, edits: List[EditRegion]) -> EditResult:
        """Apply multiple edits to a file"""
        abs_path = self.workspace_root / file_path
        if not abs_path.exists():
            return EditResult(False, f"File not found: {file_path}", "", [], edits)
            
        # Sort edits by start line in reverse order
        edits = sorted(edits, key=lambda e: e.start_line, reverse=True)
        
        # Validate all edits first
        for edit in edits:
            if not self.validate_edit(file_path, edit):
                return EditResult(
                    False,
                    f"Edit validation failed for lines {edit.start_line}-{edit.end_line}",
                    "",
                    [],
                    edits
                )
        
        # Read the entire file
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Apply edits
        applied = []
        failed = []
        for edit in edits:
            try:
                # Replace the lines
                new_lines = edit.new_content.splitlines(keepends=True)
                lines[edit.start_line-1:edit.end_line] = new_lines
                applied.append(edit)
            except Exception as e:
                failed.append(edit)
                return EditResult(
                    False,
                    f"Failed to apply edit: {str(e)}",
                    "",
                    applied,
                    failed
                )
        
        # Generate diff
        old_content = ''.join(lines)
        new_content = ''.join(lines)
        diff = ''.join(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=file_path,
            tofile=file_path
        ))
        
        # Write back to file
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        return EditResult(
            True,
            "All edits applied successfully",
            diff,
            applied,
            failed
        )
        
    def create_file(self, file_path: str, content: str) -> bool:
        """Create a new file with content"""
        abs_path = self.workspace_root / file_path
        
        # Ensure directory exists
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
            
    def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        abs_path = self.workspace_root / file_path
        try:
            abs_path.unlink()
            return True
        except Exception:
            return False 