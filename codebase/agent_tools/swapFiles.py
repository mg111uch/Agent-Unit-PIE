
import os
import shutil
import argparse

def swap_files_in_directories(dir1, dir2):
    """
    Swaps files with the same name and relative path between two directories.
    """
    if not os.path.isdir(dir1):
        print(f"Error: Directory not found: {dir1}")
        return
    if not os.path.isdir(dir2):
        print(f"Error: Directory not found: {dir2}")
        return

    for root1, _, files1 in os.walk(dir1):
        for filename in files1:
            relative_path = os.path.relpath(root1, dir1)
            file1_path = os.path.join(root1, filename)
            file2_path = os.path.join(dir2, relative_path, filename)

            if os.path.exists(file2_path) and os.path.isfile(file2_path):
                print(f"Swapping: {file1_path} <-> {file2_path}")
                
                # Create a temporary file to hold content of file1
                temp_file_path = file1_path + ".temp_swap"
                shutil.copy2(file1_path, temp_file_path)
                
                # Copy file2 to file1's location
                shutil.copy2(file2_path, file1_path)
                
                # Copy temp_file (original file1) to file2's location
                shutil.copy2(temp_file_path, file2_path)
                
                # Remove the temporary file
                os.remove(temp_file_path)
            else:
                print(f"No matching file found in {dir2} for {file1_path}. Skipping.")

def main():
    # parser = argparse.ArgumentParser(description="Swap files with the same name in corresponding nested directories.")
    # parser.add_argument("directory1", help="The path to the first parent directory.")
    # parser.add_argument("directory2", help="The path to the second parent directory.")
    
    # args = parser.parse_args()
    
    # swap_files_in_directories(args.directory1, args.directory2)

    swap_files_in_directories('./copied2', '../../reddit-clone')

if __name__ == "__main__":
    main()
