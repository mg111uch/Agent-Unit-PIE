#!/usr/bin/env python3
"""
Wrapper script to run application and record video simultaneously.
Runs application and video recording as separate subprocesses with timing control.
Recording automatically stops when the application completes.

Usage:
    python run_and_record.py --tools_file_path <path> --app_cmd_name <name> --record_cmd_name <name> --record_init_delay <seconds>

Example:
    python run_and_record.py \
        --tools_file_path /home/manigupt/Hello/React/reddit-clone/project_tools.md \
        --app_cmd_name "Run Combined Project App" \
        --record_cmd_name "Record screen" \
        --record_init_delay 2
        
Note:
    - Recording starts FIRST, then app starts after record_init_delay seconds
    - Recording will automatically stop when the app command completes
    - The video file is saved properly using SIGINT for graceful shutdown
"""

import subprocess
import threading
import time
import argparse
import os
import re
import signal


def extract_command_from_tools(tools_file_path: str, command_name: str) -> str:
    """
    Extract command string from tools file by command name.
    
    The tools file format is:
    - **Command Name:** `actual command string`
    
    Returns the command string (without backticks).
    """
    with open(tools_file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match: - **Command Name:** `command string`
    # The command name can contain spaces
    pattern = rf'- \*\*{re.escape(command_name)}:\*\* `([^`]+)`'
    
    match = re.search(pattern, content)
    if match:
        return match.group(1).strip()
    
    raise ValueError(f"Command '{command_name}' not found in {tools_file_path}")


def run_app_command(app_cmd: str, app_done_event):
    """Run the application command and signal when done."""
    print(f"Starting application: {app_cmd}")
    # Use shell=True to handle complex commands with cd, conda, etc.
    subprocess.run(app_cmd, shell=True)
    print("Application completed.")
    app_done_event.set()  # Signal that app is done


def record_video_before_app(record_cmd: str, init_delay: int, app_done_event):
    """Start recording first, then wait for app to complete."""
    # Wait for recording to initialize
    print(f"Waiting {init_delay} seconds for recording to initialize...")
    time.sleep(init_delay)
    
    # Start recording
    print(f"Starting recording: {record_cmd}")
    record_process = subprocess.Popen(record_cmd, shell=True)
    
    # Wait for app to complete
    print("Recording started. Waiting for application to complete...")
    app_done_event.wait()
    
    # Stop recording when app is done
    print("Application done, stopping recording...")
    record_process.send_signal(signal.SIGINT)
    
    try:
        # Wait for graceful shutdown (up to 5 seconds)
        record_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        # Force terminate if SIGINT fails
        print("Recording didn't stop gracefully, forcing...")
        record_process.terminate()
        record_process.wait()
    
    print("Recording stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Run app command and record video simultaneously"
    )
    parser.add_argument(
        "--tools_file_path",
        type=str,
        required=True,
        help="Path to the project_tools.md file containing command definitions"
    )
    parser.add_argument(
        "--app_cmd_name",
        type=str,
        required=True,
        help="Name of the application command in tools file (e.g., 'Run Combined Project App')"
    )
    parser.add_argument(
        "--record_cmd_name",
        type=str,
        required=True,
        help="Name of the record command in tools file (e.g., 'Record screen')"
    )
    parser.add_argument(
        "--record_init_delay",
        type=int,
        default=2,
        help="Delay before starting recording (to let it initialize) before app starts"
    )
    
    args = parser.parse_args()
    
    # Extract commands from tools file
    print(f"Reading commands from: {args.tools_file_path}")
    
    app_cmd = extract_command_from_tools(args.tools_file_path, args.app_cmd_name)
    record_cmd = extract_command_from_tools(args.tools_file_path, args.record_cmd_name)
    
    print(f"=" * 50)
    print(f"Application command: {args.app_cmd_name}")
    print(f"Recording command: {args.record_cmd_name}")
    print(f"Record init delay: {args.record_init_delay} seconds")
    print(f"=" * 50)
    
    # Create event to coordinate between app and recording
    app_done_event = threading.Event()
    
    # Start recording FIRST (in separate thread)
    recording_thread = threading.Thread(
        target=record_video_before_app,
        args=(record_cmd, args.record_init_delay, app_done_event)
    )
    
    # Start application (in separate thread)
    application_thread = threading.Thread(
        target=run_app_command,
        args=(app_cmd, app_done_event)
    )
    
    # Start recording first, then app
    recording_thread.start()
    
    # Small delay to let recording start first
    time.sleep(0.5)
    
    application_thread.start()
    
    # Wait for both to complete
    application_thread.join()
    recording_thread.join()
    
    print(f"=" * 50)
    print(f"Application and recording complete!")
    print(f"=" * 50)


if __name__ == "__main__":
    main()
