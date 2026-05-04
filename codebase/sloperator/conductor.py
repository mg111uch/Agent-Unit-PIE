#!/usr/bin/env python3
"""
Conductor - Programmable Mouse Controller
===========================================

A script to programmatically control mouse movements and clicks on screen.
Acts like a conductor directing mouse actions.

Usage:
------
    python conductor.py move <x> <y>
        Move mouse to absolute coordinates (x, y)
    
    python conductor.py click <x> <y>
        Left click at absolute coordinates
    
    python conductor.py double_click <x> <y>
        Left double click at coordinates
    
    python conductor.py right_click <x> <y>
        Right click at coordinates
    
    python conductor.py click_and_hold <x> <y>
        Click and hold at coordinates
    
    python conductor.py release
        Release mouse button
    
    python conductor.py drag <x1> <y1> <x2> <y2>
        Click and drag from (x1, y1) to (x2, y2)
    
    python conductor.py scroll <clicks>
        Scroll up (positive) or down (negative)
    
    python conductor.py position
        Get current mouse position
    
    python conductor.py screen_size
        Get screen resolution
    
    python conductor.py is_on_screen <x> <y>
        Check if coordinates are on screen

Examples:
---------
    # Click at specific position (1920x1080 screen)
    python conductor.py click 960 540
    
    # Move mouse to position then click
    python conductor.py move 100 100
    python conductor.py click 200 200
    
    # Double click to open a file
    python conductor.py double_click 500 300
    
    # Right click for context menu
    python conductor.py right_click 400 400
    
    # Drag to select or move items
    python conductor.py drag 100 200 400 200
    
    # Scroll down
    python conductor.py scroll -5
    
    # Get current position
    python conductor.py position
    
    # Check if position is valid
    python conductor.py is_on_screen 1920 1080

Requirements:
-------------
    pip install pyautogui

Notes:
------
    - On Linux, you may need to install xdotool:
      sudo apt-get install xdotool
    
    - On macOS, you may need to grant Accessibility permissions
      in System Preferences > Security & Privacy > Privacy > Accessibility
    
    - Move mouse to screen corner (0,0) to trigger failsafe abort
    
    - All coordinates are absolute screen coordinates

Author: AI Agent
"""

import sys
import argparse
import pyautogui

# Safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1      # Small pause between actions


def cmd_move(x: int, y: int) -> None:
    """Move mouse to absolute position."""
    pyautogui.moveTo(x, y, duration=0.2)
    print(f"Moved mouse to ({x}, {y})")


def cmd_click(x: int, y: int, clicks: int = 1) -> None:
    """Click at absolute position."""
    pyautogui.click(x, y, clicks=clicks)
    print(f"Clicked at ({x}, {y})")


def cmd_double_click(x: int, y: int) -> None:
    """Double click at absolute position."""
    pyautogui.doubleClick(x, y)
    print(f"Double-clicked at ({x}, {y})")


def cmd_right_click(x: int, y: int) -> None:
    """Right click at absolute position."""
    pyautogui.rightClick(x, y)
    print(f"Right-clicked at ({x}, {y})")


def cmd_click_and_hold(x: int, y: int) -> None:
    """Click and hold at absolute position."""
    pyautogui.mouseDown(x, y)
    print(f"Click and hold at ({x}, {y})")


def cmd_release() -> None:
    """Release mouse button."""
    pyautogui.mouseUp()
    print("Mouse button released")


def cmd_drag(x1: int, y1: int, x2: int, y2: int, duration: float = 1.0) -> None:
    """Drag from (x1, y1) to (x2, y2)."""
    pyautogui.moveTo(x1, y1)
    pyautogui.mouseDown()
    pyautogui.moveTo(x2, y2, duration=duration)
    pyautogui.mouseUp()
    print(f"Dragged from ({x1}, {y1}) to ({x2}, {y2})")


def cmd_scroll(clicks: int) -> None:
    """Scroll up (positive) or down (negative)."""
    pyautogui.scroll(clicks)
    direction = "up" if clicks > 0 else "down"
    print(f"Scrolled {direction} {abs(clicks)} clicks")


def cmd_position() -> None:
    """Get current mouse position."""
    x, y = pyautogui.position()
    print(f"Current position: ({x}, {y})")
    return (x, y)


def cmd_screen_size() -> None:
    """Get screen resolution."""
    width, height = pyautogui.size()
    print(f"Screen size: {width} x {height}")
    return (width, height)


def cmd_is_on_screen(x: int, y: int) -> None:
    """Check if coordinates are on screen."""
    width, height = pyautogui.size()
    on_screen = 0 <= x < width and 0 <= y < height
    print(f"Position ({x}, {y}) is {'on' if on_screen else 'off'} screen")
    print(f"Screen bounds: (0, 0) to ({width-1}, {height-1})")
    return on_screen


def main():
    """Main entry point for conductor."""
    parser = argparse.ArgumentParser(
        description="Conductor - Programmable Mouse Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python conductor.py move 100 200
  python conductor.py click 500 300
  python conductor.py double_click 400 200
  python conductor.py right_click 300 400
  python conductor.py drag 100 100 500 500
  python conductor.py scroll -3
  python conductor.py position
  python conductor.py screen_size
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # move command
    parser_move = subparsers.add_parser("move", help="Move mouse to position")
    parser_move.add_argument("x", type=int, help="X coordinate")
    parser_move.add_argument("y", type=int, help="Y coordinate")
    
    # click command
    parser_click = subparsers.add_parser("click", help="Left click at position")
    parser_click.add_argument("x", type=int, help="X coordinate")
    parser_click.add_argument("y", type=int, help="Y coordinate")
    parser_click.add_argument("--clicks", "-c", type=int, default=1, help="Number of clicks")
    
    # double_click command
    parser_dbl = subparsers.add_parser("double_click", help="Double click at position")
    parser_dbl.add_argument("x", type=int, help="X coordinate")
    parser_dbl.add_argument("y", type=int, help="Y coordinate")
    
    # right_click command
    parser_right = subparsers.add_parser("right_click", help="Right click at position")
    parser_right.add_argument("x", type=int, help="X coordinate")
    parser_right.add_argument("y", type=int, help="Y coordinate")
    
    # click_and_hold command
    parser_hold = subparsers.add_parser("click_and_hold", help="Click and hold at position")
    parser_hold.add_argument("x", type=int, help="X coordinate")
    parser_hold.add_argument("y", type=int, help="Y coordinate")
    
    # release command
    subparsers.add_parser("release", help="Release mouse button")
    
    # drag command
    parser_drag = subparsers.add_parser("drag", help="Drag from one position to another")
    parser_drag.add_argument("x1", type=int, help="Starting X coordinate")
    parser_drag.add_argument("y1", type=int, help="Starting Y coordinate")
    parser_drag.add_argument("x2", type=int, help="Ending X coordinate")
    parser_drag.add_argument("y2", type=int, help="Ending Y coordinate")
    parser_drag.add_argument("--duration", "-d", type=float, default=1.0, help="Drag duration in seconds")
    
    # scroll command
    parser_scroll = subparsers.add_parser("scroll", help="Scroll up or down")
    parser_scroll.add_argument("clicks", type=int, help="Number of clicks (positive=up, negative=down)")
    
    # position command
    subparsers.add_parser("position", help="Get current mouse position")
    
    # screen_size command
    subparsers.add_parser("screen_size", help="Get screen resolution")
    
    # is_on_screen command
    parser_ios = subparsers.add_parser("is_on_screen", help="Check if position is on screen")
    parser_ios.add_argument("x", type=int, help="X coordinate")
    parser_ios.add_argument("y", type=int, help="Y coordinate")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == "move":
            cmd_move(args.x, args.y)
        elif args.command == "click":
            cmd_click(args.x, args.y, args.clicks)
        elif args.command == "double_click":
            cmd_double_click(args.x, args.y)
        elif args.command == "right_click":
            cmd_right_click(args.x, args.y)
        elif args.command == "click_and_hold":
            cmd_click_and_hold(args.x, args.y)
        elif args.command == "release":
            cmd_release()
        elif args.command == "drag":
            cmd_drag(args.x1, args.y1, args.x2, args.y2, args.duration)
        elif args.command == "scroll":
            cmd_scroll(args.clicks)
        elif args.command == "position":
            cmd_position()
        elif args.command == "screen_size":
            cmd_screen_size()
        elif args.command == "is_on_screen":
            cmd_is_on_screen(args.x, args.y)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
