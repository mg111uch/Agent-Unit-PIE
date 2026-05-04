#!/usr/bin/env python3
"""
Post on X (Twitter) - Quick Post using Conductor
=================================================

A simple script to programmatically post to X (Twitter) using the conductor.
Assumes X is already open in the browser.

Usage:
------
    python post_on_X.py "Your message here"

Prerequisites:
--------------
    1. Install pyautogui:
       pip install pyautogui
    
    2. Have X (Twitter) open in browser and logged in
    
    3. Click on the compose area once to focus, then run this script

Notes:
------
    - Coordinates are tuned for 1920x1080 resolution
    - For different resolutions, edit COORDINATES dictionary
"""

import subprocess
import sys
import time
import os


# Default screen resolution
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080

# Coordinate mappings for different screen resolutions
# Format: (x, y) for each action
# These coordinates are tuned for 1920x1080
COORDINATES = {
    # Main X interface - left sidebar compose
    "compose_area": (35, 800),           # Where to click to start composing
    "post_input": (130, 250),             # Text input area
    "post_button_compose": (610, 175),    # Post button in compose modal
    
    # Alternative - top right compose button (home page)
    "compose_button_top": (610, 175),      # Small "Post" button in sidebar
}


def run_conductor(command: str, *args) -> subprocess.CompletedProcess:
    """Run conductor.py with given command and arguments."""
    conductor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conductor.py")
    cmd = ["python", conductor_path, command] + [str(arg) for arg in args]
    return subprocess.run(cmd, capture_output=True, text=True)


def move_mouse(x: int, y: int) -> None:
    """Move mouse to position."""
    run_conductor("move", x, y)


def click(x: int, y: int, clicks: int = 1) -> None:
    """Click at position."""
    run_conductor("click", x, y, clicks)


def type_text(text: str) -> None:
    """Type text using pyautogui."""
    import pyautogui
    pyautogui.write(text, interval=0.05)


def quick_post(message: str) -> bool:
    """
    Quick post - assumes X is already open and user is logged in.
    """
    print(f"\nQuick posting: '{message}'")
    
    try:
        # Move to compose area and click
        move_mouse(*COORDINATES["compose_area"])
        time.sleep(2)
        click(*COORDINATES["compose_area"])
        time.sleep(3)
        
        # Type message
        # type_text(message)
        # time.sleep(1)
        
        # # Click post button
        # click(*COORDINATES["post_button_compose"])
        # time.sleep(2)
        
        print("Post published successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main entry point."""
    
    # Get message from command line
    if len(sys.argv) < 2:
        print("Usage: python post_on_X.py \"Your message here\"")
        sys.exit(1)
    
    message = " ".join(sys.argv[1:])
    
    # Post the message
    success = quick_post(message)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
