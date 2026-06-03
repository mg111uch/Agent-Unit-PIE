#!/usr/bin/env python3
"""
Token Count Tool

Usage: python3 token_count.py <file_path>

Counts the number of tokens in a text file using OpenAI's tiktoken library.
Supports various tokenizer encodings (default: cl100k_base for GPT-4).

Arguments:
    <file_path>: Path to the text file to analyze

Example:
    python3 token_count.py /path/to/your/file.txt
"""
import os
import argparse
import json

# Directory to store encoding files locally (using tiktoken's cache)
ENCODING_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "encoding_cache")

# Set tiktoken's cache directory BEFORE importing tiktoken
os.environ["TIKTOKEN_CACHE_DIR"] = ENCODING_CACHE_DIR

# Now import tiktoken after setting the environment variable
import tiktoken

def download_encoding(encoding_name):
    """
    Download and save encoding files locally to tiktoken's cache.
    
    Args:
        encoding_name (str): Name of the tokenizer encoding.
    
    Returns:
        tuple: Paths to the vocab.json and merges.txt files, or None on failure.
    """
    try:
        # Ensure cache directory exists
        os.makedirs(ENCODING_CACHE_DIR, exist_ok=True)
        
        # Set the environment variable to use our cache directory
        os.environ["TIKTOKEN_CACHE_DIR"] = ENCODING_CACHE_DIR
        
        # Get the encoding - this will download to our cache dir if not already there
        encoding = tiktoken.get_encoding(encoding_name)
        
        print(f"Encoding '{encoding_name}' ready in cache: {ENCODING_CACHE_DIR}")
        return True
        
    except Exception as e:
        print(f"Error downloading encoding: {str(e)}")
        return False

def load_encoding_locally(encoding_name):
    """
    Load encoding from local cache or download if not available.
    Uses tiktoken's built-in caching mechanism.
    
    Args:
        encoding_name (str): Name of the tokenizer encoding.
    
    Returns:
        tiktoken.Encoding: The loaded encoding object.
    """
    # Ensure cache directory exists and is properly set
    os.makedirs(ENCODING_CACHE_DIR, exist_ok=True)
    os.environ["TIKTOKEN_CACHE_DIR"] = ENCODING_CACHE_DIR
    
    # Check if cache directory has any files with content (tiktoken uses hash-named files)
    cache_files = []
    if os.path.exists(ENCODING_CACHE_DIR):
        cache_files = [f for f in os.listdir(ENCODING_CACHE_DIR) 
                       if os.path.isfile(os.path.join(ENCODING_CACHE_DIR, f))]
    
    # Check if cache is valid (has files with non-zero size)
    has_valid_cache = False
    for f in cache_files:
        fpath = os.path.join(ENCODING_CACHE_DIR, f)
        if os.path.getsize(fpath) > 1000:  # Real tiktoken cache files are > 1KB
            has_valid_cache = True
            break
    
    if has_valid_cache:
        # Cache exists and has valid files - use local cache
        # print(f"Loading encoding '{encoding_name}' from local cache: {ENCODING_CACHE_DIR}")
        return tiktoken.get_encoding(encoding_name)
    else:
        # No valid cache - download and cache locally
        print(f"Local encoding cache not found or invalid. Downloading '{encoding_name}'...")
        encoding = tiktoken.get_encoding(encoding_name)
        print(f"Encoding '{encoding_name}' cached locally at {ENCODING_CACHE_DIR}")
        return encoding

def count_tokens(file_path, encoding_name="cl100k_base"):
    """
    Count the number of tokens in a text file using a specified tokenizer encoding.
    
    Args:
        file_path (str): Path to the text file to analyze.
        encoding_name (str): Name of the tokenizer encoding (e.g., 'cl100k_base' for GPT-4).
    
    Returns:
        int: Number of tokens in the file.
    """
    try:
        # Check if the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist or is not a file.")
        
        # Initialize the tokenizer (checks local cache first)
        encoding = load_encoding_locally(encoding_name)
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
        
        # Tokenize the content and count tokens
        tokens = encoding.encode(content)
        token_count = len(tokens)
        
        return token_count
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 0

# Main entry point when script is executed directly
if __name__ == "__main__":
    # Set up command line argument parser
    parser = argparse.ArgumentParser(
        description="Count tokens in a text file using OpenAI's tiktoken library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 token_count.py /path/to/your/file.txt
  token_count.py /path/to/your/file.txt  # If script is executable

Note: Requires tiktoken library. Install with: pip install tiktoken
"""
    )
    
    parser.add_argument("file_path", help="Path to the text file to analyze")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Count tokens
    tokens = count_tokens(args.file_path)
    print(f"Total tokens: {tokens}")
        