#!/usr/bin/env python3
"""
Run Process with Duration Limit

This script runs another Python script in a subprocess and automatically
terminates it after a specified duration.

Usage:
    python run_process.py --script "path/to/script.py --arg1 val1" --duration 10
    python run_process.py --script "python -c 'import time; print(\"Starting\"); time.sleep(10); print(\"Done\")'" --duration 3

Arguments:
    --script:   The script to run (either a .py file or a command string)
    --duration: Maximum duration in seconds before aborting (default: 60)
"""

import argparse
import os
import subprocess
import sys
import time
import signal


def run_script_with_timeout(script_cmd, duration):
    """
    Run a script command and terminate it after the specified duration.
    
    Args:
        script_cmd: Either a path to a .py file or a command string
        duration: Maximum duration in seconds before aborting
    
    Returns:
        int: Exit code of the process
    """
    import threading
    from queue import Queue, Empty
    
    start_time = time.time()
    process = None
    output_queue = Queue()
    
    def read_output(pipe, queue):
        """Read output from pipe and put in queue."""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    queue.put(line)
        except:
            pass
        finally:
            pipe.close()
    
    try:
        # Debug: print sys.executable
        print(f"DEBUG: sys.executable = {repr(sys.executable)}")
        
        # Check if script_cmd contains a Python script (has .py before any arguments)
        # If so, we need to explicitly invoke Python to run it
        # We need to check if the first token (before any arguments) ends with .py
        script_first_part = script_cmd.strip().split()[0] if script_cmd.strip() else ""
        if script_first_part.endswith('.py'):
            # It's a Python file, run with python interpreter
            # Use string concatenation instead of f-string to avoid potential issues
            print(f"DEBUG: sys.executable type={type(sys.executable)}, value={repr(sys.executable)}")
            print(f"DEBUG: script_cmd type={type(script_cmd)}, value={repr(script_cmd)}")
            python_path = sys.executable
            print(f"DEBUG: python_path = {repr(python_path)}")
            cmd = python_path + ' ' + script_cmd
            print(f"DEBUG: cmd after concat = {repr(cmd)}")
            use_shell = True
            print(f"DEBUG: cmd = {repr(cmd)}")
        else:
            # It's a command string, use shell
            cmd = script_cmd
            use_shell = True
            print(f"DEBUG: cmd = {repr(cmd)}")
        
        print(f"Starting process: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        print(f"Duration limit: {duration} seconds")
        print("-" * 50)
        
        if use_shell:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True  # Create new process group for proper cleanup
            )
        else:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
        
        # Start reading output in a separate thread
        output_thread = threading.Thread(target=read_output, args=(process.stdout, output_queue))
        output_thread.daemon = True
        output_thread.start()
        
        # Monitor the process
        while True:
            # Print any available output from queue
            try:
                while True:
                    line = output_queue.get_nowait()
                    print(line.rstrip())
            except Empty:
                pass
            
            # Check if process has finished
            exit_code = process.poll()
            if exit_code is not None:
                # Print any remaining output
                while True:
                    try:
                        line = output_queue.get_nowait()
                        print(line.rstrip())
                    except Empty:
                        break
                
                elapsed_time = time.time() - start_time
                print("-" * 50)
                print(f"Process completed with exit code: {exit_code}")
                print(f"Elapsed time: {elapsed_time:.2f} seconds")
                return exit_code
            
            # Check if duration has been exceeded
            elapsed_time = time.time() - start_time
            if elapsed_time >= duration:
                print("-" * 50)
                print(f"Duration limit ({duration}s) exceeded!")
                print(f"Elapsed time: {elapsed_time:.2f} seconds")
                print("Killing process...")
                
                # Kill the entire process group to ensure child processes (like pygame) are also killed
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Process already terminated
                print("Process killed.")
                
                # Print any remaining output
                while True:
                    try:
                        line = output_queue.get_nowait()
                        print(line.rstrip())
                    except Empty:
                        break
                
                return -1
            
            # Small sleep to prevent busy waiting
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user!")
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        return -1
    
    except Exception as e:
        print(f"Error running script: {e}")
        if process:
            process.kill()
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Run a script with a duration limit. Aborts the script when duration is exceeded.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_process.py --script my_script.py --duration 60
    python run_process.py --script "python -m pytest tests/" --duration 120
    python run_process.py --script training/train_nn.py --train_duration 300
        """
    )
    
    parser.add_argument(
        '--script',
        type=str,
        required=True,
        help='Path to the script to run (or a command string)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Maximum duration in seconds before aborting (default: 60)'
    )
    
    args = parser.parse_args()
    
    exit_code = run_script_with_timeout(args.script, args.duration)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
