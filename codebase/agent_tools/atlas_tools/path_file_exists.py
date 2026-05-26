import os
import argparse

def check_path_exists_os(path_string):
    """
    Checks if a file or directory exists using os.path.
    
    Args:
        path_string (str): The path to check.

    Returns:
        bool: True if the path exists, False otherwise.
    """
    if os.path.exists(path_string):
        print(f"The path '{path_string}' exists.")
        if os.path.isfile(path_string):
            print("It is a file.")
        elif os.path.isdir(path_string):
            print("It is a directory.")
        return True
    else:
        print(f"The path '{path_string}' does not exist.")
        return False

if __name__ == "__main__":
    # Set up command line argument parser
    parser = argparse.ArgumentParser(
        description="Check if file path exists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 path_file_exists.py /path/to/your/file.txt
"""
    )
    
    parser.add_argument("file_path", help="Path to the text file to analyze")
    
    # Parse arguments
    args = parser.parse_args()
    
    check_path_exists_os(args.file_path)

