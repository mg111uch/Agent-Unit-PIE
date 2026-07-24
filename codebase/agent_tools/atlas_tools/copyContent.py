#!/usr/bin/env python3
import os
import argparse
import re
"""
This script provides utilities for copying and dumping file contents.

Command line usage:

1. To copy content between start_marker and end_marker: Reads file paths from input_file and copies their contents (optionally between markers) to output_file.
   python copyContent.py --mode copy --input_file paths.txt --output_file file_dump.txt --start_marker "// y" --end_marker "// n"

2. To dump checked files from directory tree: Parses a directory tree from md_file, identifies files marked with [X], and dumps their full contents to output_file.
   python copyContent.py --mode dump --md_file agent_harness.md --base_path /path/to/base --output_file context_dump.txt --start_marker '# START' --end_marker '# END'
"""

def copy_contents(input_file, output_file, start_marker=None, end_marker=None):
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            with open(input_file, 'r', encoding='utf-8') as infile:
                should_process_path = (start_marker is None) # Start processing if no start_marker is given
                for line in infile:
                    file_path = line.strip()
                    if not file_path:
                        continue

                    if start_marker and start_marker in file_path:
                        should_process_path = True
                        continue # Don't treat the marker line as a file path
                    if end_marker and end_marker in file_path:
                        should_process_path = False
                        continue # Don't treat the marker line as a file path

                    if not should_process_path:
                        continue

                    if os.path.isfile(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as content_file:
                                outfile.write(f"\n=== Content of {file_path} ===\n")
                                inside_marker_block = False
                                content_written_for_file = False
                                if start_marker is None and end_marker is None:
                                    # If no markers are provided, copy everything
                                    inside_marker_block = True

                                for content_line in content_file:
                                    if start_marker and start_marker in content_line:
                                        inside_marker_block = True
                                        continue # Don't write the start marker line itself
                                    if end_marker and end_marker in content_line:
                                        inside_marker_block = False
                                        continue # Don't write the end marker line itself

                                    if inside_marker_block:
                                        outfile.write(content_line)
                                        content_written_for_file = True
                                
                                if not content_written_for_file:
                                    print(f"#### Not copied : {file_path}")
                                else:
                                    print(f"Copied : {file_path}")
                                outfile.write("\n")
                        except Exception as e:
                            print(f"Error reading {file_path}: {str(e)}")
                    else:
                        print(f"File {file_path} does not exist")
        print(f"Contents copied to {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

def dump_checked_files(md_file, start_marker, end_marker, base_path, output_file="context_dump.txt"):
    try:
        structure_lines = []
        with open(md_file, "r") as f:
            lines = f.readlines()
        start_idx = None
        for i, line in enumerate(lines):
            if line.strip() == start_marker:
                start_idx = i
                break
        if start_idx is None:
            raise ValueError("Start marker not found")
        for line in lines[start_idx + 1:]:
            if line.strip() == end_marker:
                break
            structure_lines.append(line)
        
        checked_files = []
        current_path = []
        for line in structure_lines:
            line = line.rstrip()
            if not line:
                continue
            line = line.replace("├── ", "").replace("└── ", "").replace("│   ", "    ")
            indent = len(line) - len(line.lstrip())
            name = line.strip()
            if not name:
                continue
            level = indent // 4
            current_path = current_path[:level]
            is_checked = "[X]" in name
            name = name.replace("[X] ", "").replace("[ ] ", "").strip()
            # Strip trailing bracket details (e.g., [53 LOC, 861 tokens])
            name = re.sub(r"\s*\[[^\]]*\]$", "", name)
            is_dir = name.endswith("/")
            name = name.rstrip("/")
            if is_dir:
                current_path.append(name)
            else:
                if is_checked:
                    full_path = os.path.join(base_path, *current_path, name)
                    checked_files.append(full_path)
        
        with open(output_file, "w", encoding="utf-8") as outfile:
            for file_path in checked_files:
                rel_path = os.path.relpath(file_path, base_path)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as content_file:
                            outfile.write(f"\n=== Content of {rel_path} ===\n")
                            outfile.write(content_file.read())
                            outfile.write("\n")
                            print(f"Copied: {file_path}")
                    except Exception as e:
                        print(f"Error reading {file_path}: {str(e)}")
                else:
                    print(f"File {file_path} does not exist")
        print(f"Checked files content dumped to {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy file contents or dump checked files from directory tree")
    parser.add_argument("--mode", choices=["copy", "dump"], required=True, help="Mode: copy contents or dump checked files")
    parser.add_argument("--input_file", help="Input file for copy mode")
    parser.add_argument("--output_file", default="output.txt", help="Output file")
    parser.add_argument("--start_marker", help="Start marker")
    parser.add_argument("--end_marker", help="End marker")
    parser.add_argument("--md_file", help="Markdown file for dump mode")
    parser.add_argument("--base_path", help="Base path for dump mode")
    
    args = parser.parse_args()
    
    if args.mode == "copy":
        if not args.input_file:
            parser.error("--input_file is required for copy mode")
        copy_contents(args.input_file, args.output_file, args.start_marker, args.end_marker)
    elif args.mode == "dump":
        if not args.md_file or not args.base_path:
            parser.error("--md_file and --base_path are required for dump mode")
        dump_checked_files(args.md_file, args.start_marker or "### START", args.end_marker or "### END", args.base_path, args.output_file)
