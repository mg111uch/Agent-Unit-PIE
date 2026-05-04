"""
Tool to Count total Lines of Code (LOC), Total token size and Number of files in a codebase

Usage:
    python codebase_size.py --directory <directory> [--extensions .py .js .ts] [--output-file <file>] [--start-marker <start-marker>] [--end-marker <end-marker>] [--ignore-dir <dir1> <dir2>]

    - --directory: The root directory to scan for files.
    - --extensions: Optional list of file extensions to include (e.g., .py .js .ts).
                    Defaults to ['.py'] if not specified.
    - --output-file: Optional path to output file to write the results between the start and end markers.
    - --start-marker: Optional start marker string (default: "### Codebase Size ###").
    - --end-marker: Optional end marker string (default: "### End Codebase Size ###").
    - --ignore-dir: Optional list of directory names to ignore during scanning.

Example:
    python codebase_size.py --directory /path/to/project --extensions .py .js --output-file report.txt --start-marker "### Codebase Size ###" --end-marker "### End Codebase Size ###" --ignore-dir node_modules .git
"""

import os
import argparse
from typing import Callable, List
from token_count import count_tokens

def count_lines_of_code(file_path: str) -> int:
    """
    Counts the number of non-empty lines in a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        int: The number of non-empty lines.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0
        
def scan_and_process_files(directory: str, extensions: List[str], process_func: Callable[[str], None], ignore_dir: List[str] = None, ignored_files: List[str] = None) -> None:
    """
    Iteratively scans a directory for files with specified extensions and runs a given function on each file path.

    Args:
        directory (str): The root directory to scan.
        extensions (List[str]): List of file extensions to look for (e.g., ['.py', '.js']).
        process_func (Callable[[str], None]): A function to run on each matching file path.
        ignore_dir (List[str], optional): List of directory names to ignore during scanning.
        ignored_files (List[str], optional): List of file names to ignore during scanning.
    """
    if ignore_dir is None:
        ignore_dir = []
    if ignored_files is None:
        ignored_files = []
    
    if not os.path.isdir(directory):
        raise ValueError(f"Directory '{directory}' does not exist or is not a directory.")

    for root, dirs, files in os.walk(directory):
        # Filter out ignored directories in-place to prevent os.walk from descending into them
        dirs[:] = [d for d in dirs if d not in ignore_dir]
        for file in files:
            if file in ignored_files:
                continue
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                process_func(file_path)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool to Count total Lines of Code (LOC), Total token size and Number of files in a codebase")
    parser.add_argument('--directory', required=True, help='The root directory to scan for files.')
    parser.add_argument('--extensions', nargs='+', default=['.py'], help='List of file extensions to include (e.g., .py .js .ts).')
    parser.add_argument('--output-file', help='Optional path to output file to write the results between the start and end markers.')
    parser.add_argument('--start-marker', default='### Codebase Size ###', help='Optional start marker string.')
    parser.add_argument('--end-marker', default='### End Codebase Size ###', help='Optional end marker string.')
    parser.add_argument('--ignore-dir', nargs='+', default=[], help='Optional list of directory names to ignore during scanning.')
    parser.add_argument('--ignore-files', nargs='+', default=[], help='Optional list of file names to ignore during scanning.')
    args = parser.parse_args()

    directory = args.directory
    extensions = args.extensions

    total_loc = [0]
    total_tokens = [0]
    total_files = [0]

    def process_file(file_path: str) -> None:
        total_loc[0] += count_lines_of_code(file_path)
        total_tokens[0] += count_tokens(file_path)
        total_files[0] += 1

    scan_and_process_files(directory, extensions, process_file, args.ignore_dir, args.ignore_files)
    print(f"Total files processed: {total_files[0]}")
    print(f"Total lines of code: {total_loc[0]}")
    print(f"Total tokens: {total_tokens[0]}")

    if args.output_file:
        output = f"Total files processed: {total_files[0]}\nTotal lines of code: {total_loc[0]}\nTotal tokens: {total_tokens[0]}\n"
        try:
            with open(args.output_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = ""
        start_marker_line = f"{args.start_marker}\n"
        end_marker_line = f"{args.end_marker}\n"
        if start_marker_line in content:
            before_start, after_start = content.split(start_marker_line, 1)
            if end_marker_line in after_start:
                _, after_end = after_start.split(end_marker_line, 1)
                new_content = before_start + start_marker_line + output + end_marker_line + after_end
            else:
                new_content = before_start + start_marker_line + output + end_marker_line
        else:
            new_content = content + ("\n" if content else "") + start_marker_line + output + end_marker_line
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)


