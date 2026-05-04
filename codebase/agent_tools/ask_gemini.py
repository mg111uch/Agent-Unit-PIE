"""
Text/Video/Image Reasoning Script

Analyzes a video file, image file, or text query using Google's Gemini model
and writes the analysis results to a predefined answer file.

Usage:
    # Text-only query:
    python ask_gemini.py
    
    # Image analysis:
    python ask_gemini.py --img_file <path_to_image>

    # Video analysis:
    python ask_gemini.py --video_file <path_to_video>
    
    # With custom model:
    python ask_gemini.py --model gemini-2.5-flash

Arguments:
    --video_file    (optional) Path to the video file to analyze
    --img_file      (optional) Path to the image file to analyze
    --model         (optional) Gemini model to use (default: models/gemini-2.5-flash-lite)

Note: Either --video_file or --img_file can be provided, but not both.
      If neither is provided, a text-only query is performed.
      Question is read from: QUESTION_FILE constant
      Answer is written to: ANSWER_FILE constant
"""

from google import genai
from google.genai import types
import argparse
import json
import os
import time
from dotenv import load_dotenv

# Rate limiting configuration
RATE_LIMIT_INTERVAL = 20  # seconds between API calls
STATE_FILE = "gemini_api_state.json"

load_dotenv(dotenv_path="/home/manigupt/Hello/python/Agentic_Unit_PIE/codebase") 

my_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=my_api_key)

QUESTION_FILE = '/home/manigupt/Hello/python/ai_agent/utils/gemini_question.md'

ANSWER_FILE = '/home/manigupt/Hello/python/ai_agent/utils/gemini_answer.md'

def get_last_call_time() -> float:
    """Load last API call timestamp from state file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return float(data.get("last_call_time", 0))
        except (json.JSONDecodeError, IOError):
            return 0.0
    return 0.0


def save_last_call_time():
    """Save current timestamp to state file."""
    with open(STATE_FILE, 'w') as f:
        json.dump({"last_call_time": time.time()}, f)


def enforce_rate_limit():
    """Block if called before rate limit interval has passed."""
    last_call = get_last_call_time()
    elapsed = time.time() - last_call
    if elapsed < RATE_LIMIT_INTERVAL:
        wait = RATE_LIMIT_INTERVAL - elapsed
        print(f"Rate limit: waiting {wait:.1f} seconds...")
        time.sleep(wait)
    save_last_call_time()

def main():
    parser = argparse.ArgumentParser(
        description="Analyze video/image with Gemini and write response to file"
    )
    parser.add_argument("--video_file", type=str, required=False, default=None,
                        help="Path to the video file to analyze")
    parser.add_argument("--img_file", type=str, required=False, default=None,
                        help="Path to the image file to analyze")
    parser.add_argument("--model", type=str, default='models/gemini-2.5-flash-lite',
                        help="Gemini model to use (default: models/gemini-2.5-flash-lite)")
    
    args = parser.parse_args()
    
    if args.video_file and args.img_file:
        print("Error: Only one of --video_file or --img_file can be provided.")
        return
    
    if args.video_file and not os.path.exists(args.video_file):
        print(f"Error: Video file not found: {args.video_file}")
        return
    
    if args.img_file and not os.path.exists(args.img_file):
        print(f"Error: Image file not found: {args.img_file}")
        return
    
    if not os.path.exists(QUESTION_FILE):
        print(f"Error: Question file not found: {QUESTION_FILE}")
        return
    
    if not my_api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return
    
    if not args.video_file and not args.img_file:
        print("Text-only mode: No video or image file provided.")
    
    try:
        with open(QUESTION_FILE, 'r') as f:
            question_content = f.read()
    except IOError as e:
        print(f"Error reading question file: {e}")
        return
    
    if not question_content.strip():
        print("Error: Question file is empty.")
        return
    
    response = None
    
    if args.img_file:
        img_file = args.img_file
        print(f"Reading image from: {img_file}")
        try:
            img_bytes = open(img_file, 'rb').read()
        except IOError as e:
            print(f"Error reading image file: {e}")
            return
        
        if img_file.lower().endswith('.png'):
            mime_type = 'image/png'
        elif img_file.lower().endswith('.jpg') or img_file.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif img_file.lower().endswith('.gif'):
            mime_type = 'image/gif'
        elif img_file.lower().endswith('.webp'):
            mime_type = 'image/webp'
        else:
            mime_type = 'image/jpeg'
        
        enforce_rate_limit()
        try:
            response = client.models.generate_content(
                model=args.model,
                contents=types.Content(
                    parts=[
                        types.Part(
                            inline_data=types.Blob(data=img_bytes, mime_type=mime_type)
                        ),
                        types.Part(text=question_content)
                    ]
                )
            )
        except Exception as e:
            print(f"Error during image analysis: {e}")
            return
    elif args.video_file:
        video_file = args.video_file
        print(f"Reading video from: {video_file}")
        try:
            video_bytes = open(video_file, 'rb').read()
        except IOError as e:
            print(f"Error reading video file: {e}")
            return

        enforce_rate_limit()
        try:
            response = client.models.generate_content(
                model=args.model,
                contents=types.Content(
                    parts=[
                        types.Part(
                            inline_data=types.Blob(data=video_bytes, mime_type='video/mp4')
                        ),
                        types.Part(text=question_content)
                    ]
                )
            )
        except Exception as e:
            print(f"Error during video analysis: {e}")
            return
    else:
        enforce_rate_limit()
        try:
            response = client.models.generate_content(
                model=args.model,
                contents=question_content
            )
        except Exception as e:
            print(f"Error during text analysis: {e}")
            return
    
    if not response or not hasattr(response, 'text') or not response.text:
        print("Error: No response received from Gemini API.")
        return
    
    try:
        with open(ANSWER_FILE, 'w') as f:
            f.write(response.text)
    except IOError as e:
        print(f"Error writing answer file: {e}")
        return
    
    print(f"\nReasoning answer written to: {ANSWER_FILE}")

if __name__ == "__main__":
    main()
