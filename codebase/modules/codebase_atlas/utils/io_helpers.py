"""
I/O helper utilities for Codebase Atlas.

This module provides file I/O functions with error handling and convenience features.
"""

import os
import pickle
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


def ensure_directory(dir_path: str) -> Path:
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        dir_path: Path to directory
    
    Returns:
        Path object for the directory
    
    Raises:
        OSError: If directory cannot be created
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Write content to file with error handling.
    
    Args:
        file_path: Path to file
        content: Content to write
        encoding: File encoding
    
    Returns:
        True if successful
    
    Raises:
        IOError: If file cannot be written
    """
    try:
        path = Path(file_path)
        
        # Ensure parent directory exists
        ensure_directory(str(path.parent))
        
        # Write file
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return True
    except Exception as e:
        raise IOError(f"Failed to write {file_path}: {str(e)}")


def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Read file content with error handling.
    
    Args:
        file_path: Path to file
        encoding: File encoding
    
    Returns:
        File content as string, or None if file doesn't exist
    
    Raises:
        IOError: If file cannot be read
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to read {file_path}: {str(e)}")


def get_timestamp() -> str:
    """
    Get current timestamp in readable format.
    
    Returns:
        Timestamp string (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
    
    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        return Path(file_path).stat().st_size
    except:
        return 0


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 KB", "2.3 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def list_files_in_directory(dir_path: str, pattern: str = "*") -> list:
    """
    List all files in directory matching pattern.
    
    Args:
        dir_path: Directory path
        pattern: Glob pattern (default: all files)
    
    Returns:
        List of Path objects
    """
    path = Path(dir_path)
    if not path.exists():
        return []
    
    return list(path.glob(pattern))


def clean_directory(dir_path: str, keep_files: Optional[list] = None):
    """
    Remove all files and subdirectories in directory except specified ones.
    
    Args:
        dir_path: Directory to clean
        keep_files: List of filenames to keep
    """
    keep_files = keep_files or []
    path = Path(dir_path)
    
    if not path.exists():
        return
    
    for item in path.iterdir():
        if item.name in keep_files:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def save_atlas_data(atlas_data, dir_path: str):
    """Serialize atlas data to pickle file."""
    path = Path(dir_path) / "atlas_data.pkl"
    with open(path, 'wb') as f:
        pickle.dump(atlas_data, f)


def load_atlas_data(dir_path: str):
    """Load atlas data from pickle file."""
    path = Path(dir_path) / "atlas_data.pkl"
    if not path.exists():
        raise FileNotFoundError(f"No saved atlas data found at {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)


def append_to_file(file_path: str, content: str, encoding: str = 'utf-8'):
    """
    Append content to file.
    
    Args:
        file_path: Path to file
        content: Content to append
        encoding: File encoding
    """
    path = Path(file_path)
    ensure_directory(str(path.parent))
    
    with open(path, 'a', encoding=encoding) as f:
        f.write(content)