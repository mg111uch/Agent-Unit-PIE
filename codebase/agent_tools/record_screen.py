#!/usr/bin/env python3
"""
Screen Recording Script

Usage:
    python record_screen.py --x 0 --y 0 --width 1920 --height 1080 --duration 10 --output video.avi

Arguments:
    --x:         X coordinate of the top-left corner (default: 0)
    --y:         Y coordinate of the top-left corner (default: 0)
    --width:     Width of the recording area (required)
    --height:    Height of the recording area (required)
    --duration:  Recording duration in seconds (default: unlimited/ctrl+c to stop)
    --output:    Output file name (default: screen_record.avi)
    --fps:       Frames per second (default: 10)

Example:
    Record a 30-second video at 15 fps:
    python record_screen.py --width 1366 --height 768 --duration 30 --fps 15
"""

import cv2
import numpy as np
import mss
import mss.tools
import argparse
import time
import signal
import sys

# Global variable to hold video writer reference for signal handler
_video_writer = None
_output_file = None

def _signal_handler(signum, frame):
    """Handle termination signals to properly save video."""
    global _video_writer, _output_file
    print("\nRecording stopped by signal.")
    if _video_writer is not None:
        _video_writer.release()
        print(f"Video saved as {_output_file}")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, _signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, _signal_handler) # kill command


def record_screen(x, y, width, height, output_file='screen_record.avi', fps=10, duration=None):
    global _video_writer, _output_file
    
    # Store references for signal handler
    _output_file = output_file
    
    # Define the codec for AVI (MJPG - most compatible)
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    _video_writer = out

    print(f"Recording screen at ({x}, {y}) with size {width}x{height} to {output_file}")
    print(f"Duration: {'Unlimited (Ctrl+C to stop)' if duration is None else f'{duration} seconds'}")
    print("Press Ctrl+C to stop recording.")

    start_time = time.time()
    frame_interval = 1 / fps
    
    with mss.mss() as sct:
        # Define the region to capture
        monitor = {"left": x, "top": y, "width": width, "height": height}
        
        try:
            while True:
                # Check if duration has been reached
                if duration is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= duration:
                        print(f"Recording duration ({duration}s) completed.")
                        break
                
                # Capture screenshot of the specified region using MSS
                sct_img = sct.grab(monitor)
                # Convert MSS image (BGRA) to numpy array
                frame = np.array(sct_img)
                # Convert BGRA to BGR for OpenCV
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                # Write the frame to the video file
                out.write(frame)
                # Wait for the next frame
                time.sleep(frame_interval)
        except (KeyboardInterrupt, SystemExit):
            print("\nRecording stopped.")
        finally:
            # Release the video writer
            out.release()
            print(f"Video saved as {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record screen video.")
    parser.add_argument('--x', type=int, default=0, help='X coordinate of the top-left corner')
    parser.add_argument('--y', type=int, default=0, help='Y coordinate of the top-left corner')
    parser.add_argument('--width', type=int, required=True, help='Width of the recording area')
    parser.add_argument('--height', type=int, required=True, help='Height of the recording area')
    parser.add_argument('--duration', type=float, default=None, help='Recording duration in seconds')
    parser.add_argument('--output', type=str, default='screen_record.avi', help='Output file name')
    parser.add_argument('--fps', type=int, default=10, help='Frames per second')

    args = parser.parse_args()

    record_screen(args.x, args.y, args.width, args.height, args.output, args.fps, args.duration)
