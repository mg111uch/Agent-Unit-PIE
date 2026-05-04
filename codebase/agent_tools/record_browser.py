import asyncio
import os
import shutil
import subprocess
import time
from pyppeteer import launch

# User-provided dimensions and time length for video recording
VIDEO_WIDTH = 720  # Width of the video in pixels
VIDEO_HEIGHT = 1280  # Height of the video in pixels
RECORD_DURATION_SECONDS = 10  # Duration of the video recording in seconds

# Scrolling parameters for automatic slow scrolling
SCROLL_STEP = 50  # Pixels to scroll down per interval
SCROLL_INTERVAL_MS = 200  # Milliseconds between scroll steps

# Directory to save the recorded video
VIDEO_DIR = "videos"

# Directory to save screenshots for video compilation
IMAGE_DIR = "images"

async def main():
    # Delete previous images and videos
    if os.path.exists(VIDEO_DIR):
        shutil.rmtree(VIDEO_DIR)
    if os.path.exists(IMAGE_DIR):
        shutil.rmtree(IMAGE_DIR)

    # Ensure the directories exist
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.setViewport({'width': VIDEO_WIDTH, 'height': VIDEO_HEIGHT})
    await page.goto("https://ai.google.dev/gemini-api/docs/document-processing")

    start_time = time.time()
    frame_count = 0
    while time.time() - start_time < RECORD_DURATION_SECONDS:
        screenshot_path = os.path.join(IMAGE_DIR, f"frame_{frame_count:04d}.png")
        await page.screenshot({'path': screenshot_path})
        frame_count += 1
        await page.evaluate(f"window.scrollBy(0, {SCROLL_STEP})")
        await asyncio.sleep(SCROLL_INTERVAL_MS / 1000)

    await browser.close()

    # Compile images into video using ffmpeg
    framerate = 1000 / SCROLL_INTERVAL_MS
    output_video = os.path.join(VIDEO_DIR, "recorded_video.mp4")
    cmd = [
        'ffmpeg',
        '-framerate', str(framerate),
        '-i', os.path.join(IMAGE_DIR, 'frame_%04d.png'),
        '-c:v', 'mpeg4',
        '-q:v', '2',
        output_video
    ]
    subprocess.run(cmd)

    print(f"Video recorded and saved in {VIDEO_DIR}")

if __name__ == "__main__":
    asyncio.run(main())