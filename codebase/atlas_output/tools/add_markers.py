#!/usr/bin/env python3
"""
add_markers.py - Transform markdown file to final form with project path

USAGE:
    python add_markers.py --md_file <md_file_path> --project_path <project_path>

ARGUMENTS:
    --md_file <md_file_path>      : Path to the markdown file to modify
    --project_path <project_path> : Path to add after '- **Project path:' marker

EXAMPLES:
    python add_markers.py --md_file code_atlas.md --project_path "/home/user/myproject"
    python add_markers.py --md_file /path/to/code_atlas.md --project_path "/home/user/myproject"

DESCRIPTION:
    Transforms markdown file by:
    1. Replacing 'Overview:' line with '## Codebase size' and '## End Codebase size'
    2. Adding directory structure with project path

NOTES:
    - File is modified in place
    - Use --dry-run to preview changes
"""

import argparse
import sys


def transform_markdown_file(md_file_path, project_path):
    """
    Transform a markdown file to final form by replacing Overview and adding project path.

    Args:
        md_file_path: Path to the markdown file
        project_path: Path to add after '- **Project path:' marker

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read the file
        with open(md_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {md_file_path}")
        return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

    # Replace Overview line with fixed markers
    # Find the line starting with 'Overview:'
    overview_line_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith('Overview:'):
            overview_line_index = i
            break

    if overview_line_index is None:
        print("Error: No line starting with 'Overview:' found in the file.")
        return False

    # Remove the Overview line
    lines.pop(overview_line_index)

    # Insert the fixed markers in its place
    markers = ["## Codebase size", "## End Codebase size"]
    for i, marker in enumerate(markers):
        insert_index = overview_line_index + i
        lines.insert(insert_index, f"{marker}\n")

    # Add directory structure with project path
    # Find the last line with content
    last_content_index = len(lines) - 1
    while last_content_index >= 0 and not lines[last_content_index].strip():
        last_content_index -= 1

    # Add directory structure markers and project path
    insert_index = last_content_index + 1
    lines.insert(insert_index, "\n")
    lines.insert(insert_index + 1, "## Directory Structure \n")
    lines.insert(insert_index + 2, f"- **Project path:** `{project_path}`\n")
    lines.insert(insert_index + 3, "### FILE_MAP Tree\n")
    lines.insert(insert_index + 4, "### End Tree\n")

    # Write the modified content back to the file
    try:
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Successfully updated: {md_file_path}")
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Transform markdown file to final form with project path',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python add_markers.py --md_file code_atlas.md --project_path "/home/user/myproject"
  python add_markers.py --md_file /path/to/code_atlas.md --project_path "/home/user/myproject"
        """
    )

    parser.add_argument(
        '--md_file',
        required=True,
        metavar='<md_file_path>',
        help='Path to the markdown file to modify'
    )

    parser.add_argument(
        '--project_path',
        required=True,
        metavar='<project_path>',
        help='Path to add after \'- **Project path:\' marker'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without actually modifying the file'
    )

    args = parser.parse_args()

    # Dry run mode - just show what would happen
    if args.dry_run:
        print(f"[DRY RUN] Would transform: {args.md_file}")
        print(f"  Project path: {args.project_path}")
        sys.exit(0)

    # Perform the transformation
    success = transform_markdown_file(args.md_file, args.project_path)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
