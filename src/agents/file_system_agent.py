"""
File System Agent

This agent handles local file system operations including:
- Listing files and directories
- Reading file contents
- Writing and updating files
- Deleting files with safety checks
"""

import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import fnmatch

logger = logging.getLogger(__name__)


class FileSystemAgent:
    """
    Agent responsible for local file system operations.
    
    Implements safety checks and validation for all file operations.
    """
    
    def __init__(self, base_directory: Optional[str] = None):
        """
        Initialize the File System Agent.
        
        Args:
            base_directory: Base directory for file operations (optional)
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        logger.info(f"FileSystemAgent initialized with base: {self.base_directory}")
    
    def list_files(
        self,
        directory: Optional[str] = None,
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List files in a directory.
        
        Args:
            directory: Directory to list (relative to base or absolute)
            pattern: File pattern to match (e.g., "*.py", "test_*")
            recursive: If True, search recursively
        
        Returns:
            List of file information dictionaries
        """
        target_dir = self._resolve_path(directory or ".")
        
        logger.info(f"Listing files in: {target_dir} (pattern: {pattern}, recursive: {recursive})")
        
        if not target_dir.exists():
            logger.error(f"Directory not found: {target_dir}")
            return []
        
        if not target_dir.is_dir():
            logger.error(f"Not a directory: {target_dir}")
            return []
        
        files = []
        
        if recursive:
            # Recursive search
            for file_path in target_dir.rglob(pattern):
                if file_path.is_file():
                    files.append(self._get_file_info(file_path))
        else:
            # Non-recursive search
            for file_path in target_dir.glob(pattern):
                if file_path.is_file():
                    files.append(self._get_file_info(file_path))
        
        logger.info(f"Found {len(files)} files")
        return files
    
    def read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read file contents.
        
        Args:
            file_path: Path to file (relative to base or absolute)
            encoding: File encoding (default: utf-8)
        
        Returns:
            Dictionary with file contents and metadata
        """
        target_path = self._resolve_path(file_path)
        
        logger.info(f"Reading file: {target_path}")
        
        if not target_path.exists():
            return {
                "success": False,
                "error": f"File not found: {target_path}"
            }
        
        if not target_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {target_path}"
            }
        
        try:
            with open(target_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                "success": True,
                "file_path": str(target_path),
                "content": content,
                "size_bytes": target_path.stat().st_size,
                "modified": datetime.fromtimestamp(target_path.stat().st_mtime).isoformat()
            }
        except Exception as e:
            logger.error(f"Error reading file {target_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True
    ) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            file_path: Path to file (relative to base or absolute)
            content: Content to write
            encoding: File encoding (default: utf-8)
            create_dirs: Create parent directories if they don't exist
        
        Returns:
            Dictionary with operation result
        """
        target_path = self._resolve_path(file_path)
        
        logger.info(f"Writing file: {target_path}")
        
        # Create parent directories if needed
        if create_dirs:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(target_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": str(target_path),
                "bytes_written": len(content.encode(encoding)),
                "message": f"File written successfully: {target_path.name}"
            }
        except Exception as e:
            logger.error(f"Error writing file {target_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, file_path: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            file_path: Path to file (relative to base or absolute)
            confirm: Must be True to actually delete (safety check)
        
        Returns:
            Dictionary with operation result
        """
        target_path = self._resolve_path(file_path)
        
        logger.info(f"Delete file request: {target_path} (confirmed: {confirm})")
        
        if not target_path.exists():
            return {
                "success": False,
                "error": f"File not found: {target_path}"
            }
        
        if not target_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {target_path}"
            }
        
        # Safety check - require explicit confirmation
        if not confirm:
            return {
                "success": False,
                "requires_confirmation": True,
                "file_path": str(target_path),
                "message": "Deletion requires explicit confirmation (confirm=True)"
            }
        
        try:
            target_path.unlink()
            logger.info(f"File deleted: {target_path}")
            return {
                "success": True,
                "file_path": str(target_path),
                "message": f"File deleted: {target_path.name}"
            }
        except Exception as e:
            logger.error(f"Error deleting file {target_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def find_files(
        self,
        pattern: str,
        start_directory: Optional[str] = None,
        max_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find files matching a pattern.
        
        Args:
            pattern: File pattern (supports wildcards)
            start_directory: Where to start searching
            max_depth: Maximum directory depth to search
        
        Returns:
            List of matching files
        """
        start_dir = self._resolve_path(start_directory or ".")
        
        logger.info(f"Finding files: pattern={pattern}, start={start_dir}")
        
        if not start_dir.exists():
            logger.error(f"Directory not found: {start_dir}")
            return []
        
        matching_files = []
        
        for file_path in start_dir.rglob(pattern):
            # Check depth
            try:
                relative_path = file_path.relative_to(start_dir)
                depth = len(relative_path.parts)
                
                if depth <= max_depth and file_path.is_file():
                    matching_files.append(self._get_file_info(file_path))
            except ValueError:
                # File is outside start_dir
                continue
        
        logger.info(f"Found {len(matching_files)} matching files")
        return matching_files
    
    def get_directory_size(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate total size of a directory.
        
        Args:
            directory: Directory path (relative to base or absolute)
        
        Returns:
            Dictionary with size information
        """
        target_dir = self._resolve_path(directory or ".")
        
        logger.info(f"Calculating directory size: {target_dir}")
        
        if not target_dir.exists() or not target_dir.is_dir():
            return {
                "success": False,
                "error": "Directory not found or not a directory"
            }
        
        total_size = 0
        file_count = 0
        dir_count = 0
        
        for item in target_dir.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
            elif item.is_dir():
                dir_count += 1
        
        return {
            "success": True,
            "directory": str(target_dir),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "directory_count": dir_count
        }
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to base directory or as absolute"""
        path_obj = Path(path)
        
        if path_obj.is_absolute():
            return path_obj
        else:
            return self.base_directory / path_obj
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file information"""
        stat = file_path.stat()
        
        return {
            "name": file_path.name,
            "path": str(file_path),
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "extension": file_path.suffix
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize agent with project root
    project_root = Path(__file__).parent.parent.parent
    agent = FileSystemAgent(base_directory=str(project_root))
    
    # Example 1: List Python files
    print("\n=== Example 1: List Python Files ===")
    python_files = agent.list_files(directory="src", pattern="*.py", recursive=True)
    print(f"Found {len(python_files)} Python files")
    for file in python_files[:5]:  # Show first 5
        print(f"  {file['name']} ({file['size_kb']} KB)")
    
    # Example 2: Read configuration file
    print("\n=== Example 2: Read Configuration File ===")
    result = agent.read_file("config/azure_resources.yaml")
    if result["success"]:
        print(f"  File: {result['file_path']}")
        print(f"  Size: {result['size_bytes']} bytes")
        print(f"  First 200 chars: {result['content'][:200]}...")
    
    # Example 3: Find all YAML files
    print("\n=== Example 3: Find All YAML Files ===")
    yaml_files = agent.find_files(pattern="*.yaml", start_directory="config")
    print(f"Found {len(yaml_files)} YAML files:")
    for file in yaml_files:
        print(f"  {file['name']}")
    
    # Example 4: Get directory size
    print("\n=== Example 4: Get Directory Size ===")
    size_info = agent.get_directory_size("config")
    if size_info["success"]:
        print(f"  Directory: {size_info['directory']}")
        print(f"  Total size: {size_info['total_size_mb']} MB")
        print(f"  Files: {size_info['file_count']}")
        print(f"  Subdirectories: {size_info['directory_count']}")
