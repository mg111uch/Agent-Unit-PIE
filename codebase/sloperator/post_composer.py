"""
Post on X Composer - AI-Powered Automated Post Generator and Quick Post using Conductor

=================================================

Uses Google Gemini AI to generate post content and automatically posts to X  using the conductor.
Runs indefinitely, making posts at random intervals.
Assumes X is already open in the browser.

Usage:
------
    python post_composer.py

Configuration:
--------------
    Edit the constants below to customize behavior:
    - WAIT_MIN_HOURS / WAIT_MAX_HOURS: Random wait between posts
    - DEFAULT_PROMPT: Prompt to generate content
    - PROMPT_FILE: File to read prompts from (one per line)

Environment:
------------
    Create .env file with:
    GEMINI_API_KEY=your_api_key_here

Notes:
------
    - No command line arguments needed
    - Script runs indefinitely
    - Posts at random times within the configured window
"""

import os
import sys
import subprocess
import time
import random
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION CONSTANTS - Edit these to customize behavior
# ============================================================================

# Time window for random wait between posts 
WAIT_MIN_MINUTES = 2
WAIT_MAX_MINUTES = 3

PROMPT_FAIL_WAIT_MINUTES = 5
# Default prompt to generate content (used if PROMPT_FILE doesn't exist)
DEFAULT_PROMPT = "Write a short, engaging and trending social media post about technology and AI within 280 words"

# File to read prompts from (one random prompt per line, leave empty to use DEFAULT_PROMPT)
PROMPT_FILE = "post_prompt.md"

# Gemini model to use
GEMINI_MODEL = "gemini-2.5-flash-lite"

# X posting - set to True to actually post, False to just generate
ENABLE_POSTING = True

# Screen size for X posting (if enabled)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Coordinate mappings for different screen resolutions
# Format: (x, y) for each action
# These coordinates are tuned for 1920x1080
COORDINATES = {
    # Main X interface - left sidebar compose
    "compose_area": (35, 800),           # Where to click to start composing
    "post_input": (195, 250),             # Text input area
    "post_button_compose": (607, 310),    # Post button in compose modal
    
    # Alternative - top right compose button (home page)
    "compose_button_top": (35, 240),      # Small "Post" button in sidebar
}

# ============================================================================
# LOAD ENVIRONMENT
# ============================================================================

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env file from script directory
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
load_dotenv(ENV_FILE)

# Get API key
API_KEY = os.getenv("GOOGLE_API_KEY")

# ============================================================================
# FUNCTIONS
# ============================================================================

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
    print(f"\nQuick posting now..!!")
    
    try:
        # Move to compose area and click
        move_mouse(*COORDINATES["compose_area"])
        time.sleep(1)
        click(*COORDINATES["compose_area"])
        time.sleep(3)
        
        # Type message
        type_text(message)
        time.sleep(1)
        
        # Click post button
        click(*COORDINATES["post_button_compose"])
        time.sleep(2)
        
        print("Post published successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_random_wait_time() -> float:
    """Get random wait time in hours between WAIT_MIN_HOURS and WAIT_MAX_HOURS."""
    return random.uniform(WAIT_MIN_MINUTES, WAIT_MAX_MINUTES)


def get_prompt() -> str:
    """Get a prompt to generate content from."""
    prompt_file_path = os.path.join(SCRIPT_DIR, PROMPT_FILE)
    
    # Try to read from prompts file
    # if os.path.exists(prompt_file_path):
    #     try:
    #         with open(prompt_file_path, 'r') as f:
    #             prompts = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    #         if prompts:
    #             return random.choice(prompts)
    #     except Exception as e:
    #         print(f"Warning: Could not read prompts file: {e}")
    
    # Fall back to default prompt
    return DEFAULT_PROMPT


def generate_content(prompt: str) -> str:
    """Generate content using Gemini AI."""
   
    client = genai.Client(api_key=API_KEY)
    
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text    

def log(message: str) -> None:
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def main():
    """Main loop - runs indefinitely."""
    
    log("Post Composer Started")
    log(f"  - Prompt file: {PROMPT_FILE}")
    log(f"  - Posting enabled: {ENABLE_POSTING}")
    log("-" * 50)
    
    post_count = 0
    
    try:
        while True:
            post_count += 1
            log(f"Starting post #{post_count}")
            
            # Get prompt
            prompt = get_prompt()
            log(f"Using prompt: {prompt[:50]}...")
            
            # Generate content
            try:
                content = generate_content(prompt)
                log(f"Generated content: {content[:100]}...")
            except Exception as e:
                log(f"Error generating content: {e}")
                log("Waiting before retry...")
                time.sleep(PROMPT_FAIL_WAIT_MINUTES*60)  
                continue
            
            # Post to X
            if ENABLE_POSTING:
                success = quick_post(content)
                if success:
                    log("Post published successfully!")
                else:
                    log("Failed to publish post")
            
            # Then wait random time before next cycle
            random_wait = int(get_random_wait_time() * 60)
            log(f"Waiting random {random_wait} seconds before next post...")
            time.sleep(random_wait)
            
    except KeyboardInterrupt:
        log("Interrupted by user")
        log(f"Total posts made: {post_count}")
        sys.exit(0)


if __name__ == "__main__":
    main()
