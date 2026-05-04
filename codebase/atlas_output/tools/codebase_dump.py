import os
from pathlib import Path

def dump_codebase_to_text(root_dir, output_filename="codebase_dump2.txt", excluded_dirs=None):
    """
    Recursively finds all files in a directory and appends their contents to a single text file.

    Args:
        root_dir (str): The root directory of the codebase to scan.
        output_filename (str): The name of the output text file.
        excluded_dirs (list): A list of directory names to exclude (e.g., ['.git', '__pycache__']).
    """
    if excluded_dirs is None:
        excluded_dirs = ['.git', '__pycache__', '.venv', 'env'] # Common exclusions

    root_path = Path(root_dir)
    if not root_path.is_dir():
        print(f"Error: {root_dir} is not a valid directory.")
        return

    # Open the output file in write mode
    with open(output_filename, 'w', encoding='utf-8', errors='ignore') as outfile:
        # Use rglob('*') to find all files and folders recursively
        for file_path in root_path.rglob('*'):
            if file_path.is_file():
                # Check if the file is in an excluded directory
                if any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                    continue

                try:
                    # Write a separator and the file path
                    outfile.write(f"\n\n--- Start of file: {file_path.relative_to(root_path)} ---\n\n")
                    
                    # Open the current file and write its content to the output file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        outfile.write(infile.read())
                        
                except IOError as e:
                    print(f"Could not read file {file_path}: {e}")

    print(f"\nSuccessfully dumped codebase contents to {output_filename}")

if __name__ == "__main__":
    # Specify the root directory of your codebase (e.g., current directory '.')
    # You can change '.' to any other path like '/path/to/your/project'
    codebase_directory = '/home/manigupt/Hello/python/dota2/claudeSonnet4_5/dota2_gym' 
    dump_codebase_to_text(codebase_directory)
