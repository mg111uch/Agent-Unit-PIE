import pyautogui
import argparse

# python ./tools/screenshot_region.py --x 100 --y 100 --width 400 --height 300 --output ./

def take_screenshot(x, y, width, height, output_file='screenshot.png'):
    """
    Takes a screenshot of a specified region of the screen.

    Args:
        x (int): X coordinate of the top-left corner
        y (int): Y coordinate of the top-left corner
        width (int): Width of the screenshot region
        height (int): Height of the screenshot region
        output_file (str): Output file path for the screenshot
    """
    try:
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        screenshot.save(output_file)
        print(f"Screenshot saved to {output_file}")
    except Exception as e:
        print(f"Error taking screenshot: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take a screenshot of a specific region of the screen.")
    parser.add_argument('--x', type=int, required=True, help='X coordinate of the top-left corner')
    parser.add_argument('--y', type=int, required=True, help='Y coordinate of the top-left corner')
    parser.add_argument('--width', type=int, required=True, help='Width of the screenshot region')
    parser.add_argument('--height', type=int, required=True, help='Height of the screenshot region')
    parser.add_argument('--output', type=str, default='screenshot.png', help='Output file name')

    args = parser.parse_args()

    take_screenshot(args.x, args.y, args.width, args.height, args.output)