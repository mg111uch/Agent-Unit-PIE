"""
Navigation module for AI Agent.

Usage:
    python navigation.py --test_md_file <path_to_test_md_file>

"""
import subprocess
import sys
import time
import os
import argparse

def run_conductor(command: str, *args) -> subprocess.CompletedProcess:
    """Run conductor.py with given command and arguments."""
    conductor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conductor.py")
    cmd = ["python", conductor_path, command] + [str(arg) for arg in args]
    return subprocess.run(cmd, capture_output=True, text=True)

def type_text(text: str) -> None:
    """Type text using pyautogui."""
    import pyautogui
    pyautogui.write(text, interval=0.1)

def action_pause(seconds: int):
    time.sleep(seconds)

def run_test_sequence(md_file_path: str) -> None:
    """Read and execute commands sequentially from a markdown test file."""
    import pyautogui
    
    # Read the markdown file
    with open(md_file_path, 'r') as f:
        lines = f.readlines()
    
    # Process each line
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Strip markdown list markers (-, *, etc.)
        if line.startswith('-') or line.startswith('*'):
            line = line[1:].strip()
        
        # Parse command parts
        parts = line.split()
        if not parts:
            continue
        
        command = parts[0]
        
        if command == 'run_conductor':
            # Format: run_conductor <action> [arg1] [arg2] ...
            if len(parts) >= 2:
                action = parts[1]
                args = parts[2:] if len(parts) > 2 else []
                run_conductor(action, *args)
            else:
                print(f"Warning: run_conductor requires action: {line}")
        
        elif command == 'action_pause':
            # Format: action_pause <seconds>
            if len(parts) >= 2:
                seconds = int(parts[1])
                action_pause(seconds)
            else:
                print(f"Warning: action_pause requires seconds argument: {line}")
        
        elif command == 'type_text':
            # Format: type_text "<message>" or type_text <message>
            if len(parts) >= 2:
                # Join all parts after type_text and remove quotes if present
                text = ' '.join(parts[1:])
                text = text.strip('"').strip("'")
                type_text(text)
            else:
                print(f"Warning: type_text requires text argument: {line}")
        
        else:
            print(f"Warning: Unknown command: {command}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run navigation test sequence from a markdown file."
    )
    parser.add_argument(
        "--test_md_file",
        type=str,
        required=True,
        help="Path to the markdown test file containing commands to execute"
    )
    
    args = parser.parse_args()
    
    # Run the test sequence
    run_test_sequence(args.test_md_file)