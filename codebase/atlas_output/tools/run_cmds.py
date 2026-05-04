#!/usr/bin/env python3
"""
run_cmds.py - Execute commands from a markdown file in user-defined order

USAGE:
    python run_cmds.py <md_file_path> <command_name1> <command_name2> ...

ARGUMENTS:
    md_file_path    : Path to the markdown file containing commands
    command_name(s) : One or more command names to execute (in order)

EXAMPLES:
    # Run a single command
    python run_cmds.py project_tools.md "Make Codebase_atlas"

    # Run multiple commands in specified order
    python run_cmds.py project_tools.md "Make Codebase_atlas" "Codebase size" "Make directory"

    # Run with absolute path
    python run_cmds.py /home/manigupt/Hello/python/ai_agent/atlas_output/project_tools.md "Make Codebase_atlas"

DESCRIPTION:
    This script reads a markdown file that contains commands in the format:
    - **Command Name:** `command to execute`

    It extracts all available commands and executes the ones specified by name
    in the order they are provided on the command line.

    The script will:
    1. Parse the markdown file to find all commands
    2. Validate that the requested command names exist
    3. Execute each command in the specified order
    4. Report success or failure for each command

NOTES:
    - Commands are executed using the system shell
    - Each command runs in the current working directory
    - If a command fails, execution continues with the next command
    - Command names are case-sensitive and must match exactly (including spaces)
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def parse_commands_from_md(md_file_path):
    """
    Parse commands from a markdown file.
    
    Expected format:
    - **Command Name:** `command to execute`
    
    Also handles:
    - **Command Name:** 
      `command to execute`
    - **Command Name:** Description text `command to execute`
    
    Args:
        md_file_path: Path to the markdown file
        
    Returns:
        dict: Mapping of command names to their commands
    """
    commands = {}
    
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {md_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Find all lines that start with "- **"
    command_starts = []
    for i, line in enumerate(lines):
        if line.strip().startswith('- **'):
            command_starts.append(i)
    
    # Extract each command block
    for idx, start_line in enumerate(command_starts):
        # Find the end of this command block (next command start or end of file)
        if idx < len(command_starts) - 1:
            end_line = command_starts[idx + 1]
        else:
            end_line = len(lines)
        
        # Extract the block
        block = ''.join(lines[start_line:end_line])
        
        # Extract the name from the first line
        # Pattern: **Name:** (colon is inside the bold markers)
        first_line = lines[start_line]
        pattern = r'\*{2}([^*]+)\*{2}'
        match = re.search(pattern, first_line)
        
        if match:
            name = match.group(1).strip()
            # Remove trailing colon if present
            if name.endswith(':'):
                name = name[:-1].strip()
        else:
            continue  # Skip if we can't parse the name
        
        # Find all backtick pairs in the block
        backtick_matches = re.findall(r'`([^`]+)`', block)
        
        # Use the last backtick pair as the command
        if backtick_matches:
            command = backtick_matches[-1].strip()
            commands[name] = command
    
    return commands


def list_available_commands(commands):
    """Print all available commands found in the markdown file."""
    print("\nAvailable commands:")
    print("-" * 60)
    for i, (name, cmd) in enumerate(commands.items(), 1):
        print(f"{i}. {name}")
        print(f"   Command: {cmd}")
        print()


def run_command(command_name, command_text):
    """
    Execute a single command.
    
    Args:
        command_name: Name of the command (for display)
        command_text: The actual command to execute
        
    Returns:
        bool: True if command succeeded, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Running: {command_name}")
    print(f"Command: {command_text}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command_text,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ Success: {command_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {command_name}")
        print(f"  Return code: {e.returncode}")
        return False
    except Exception as e:
        print(f"✗ Error executing {command_name}: {e}")
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Execute commands from a markdown file in user-defined order',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_cmds.py project_tools.md "Make Codebase_atlas"
  python run_cmds.py project_tools.md "Make Codebase_atlas" "Codebase size"
  python run_cmds.py project_tools.md --list
        """
    )
    
    parser.add_argument(
        'md_file',
        help='Path to the markdown file containing commands'
    )
    
    parser.add_argument(
        'commands',
        nargs='*',
        help='Command names to execute (in order)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available commands and exit'
    )
    
    parser.add_argument(
        '--continue-on-error',
        action='store_true',
        help='Continue executing remaining commands even if one fails'
    )
    
    args = parser.parse_args()
    
    # Parse commands from markdown file
    commands = parse_commands_from_md(args.md_file)
    
    if not commands:
        print("No commands found in the markdown file.")
        print("Expected format: - **Command Name:** `command to execute`")
        sys.exit(1)
    
    # List mode: just show available commands
    if args.list:
        list_available_commands(commands)
        sys.exit(0)
    
    # Validate that command names were provided
    if not args.commands:
        print("Error: No command names provided.")
        print("\nUse --list to see available commands.")
        print("Or provide command names as arguments:")
        print(f"  python {sys.argv[0]} {args.md_file} <command_name1> <command_name2> ...")
        sys.exit(1)
    
    # Validate that all requested commands exist
    invalid_commands = [cmd for cmd in args.commands if cmd not in commands]
    if invalid_commands:
        print("Error: The following command names were not found:")
        for cmd in invalid_commands:
            print(f"  - '{cmd}'")
        print("\nUse --list to see available commands.")
        sys.exit(1)
    
    # Execute commands in order
    print(f"\nExecuting {len(args.commands)} command(s) from: {args.md_file}")
    
    results = []
    for cmd_name in args.commands:
        cmd_text = commands[cmd_name]
        success = run_command(cmd_name, cmd_text)
        results.append((cmd_name, success))
        
        # Stop on error if --continue-on-error is not set
        if not success and not args.continue_on_error:
            print("\nStopping due to error. Use --continue-on-error to continue.")
            break
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    successful = sum(1 for _, success in results if success)
    failed = len(results) - successful
    
    print(f"Total commands: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed commands:")
        for cmd_name, success in results:
            if not success:
                print(f"  - {cmd_name}")
        sys.exit(1)
    else:
        print("\n✓ All commands executed successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main()
