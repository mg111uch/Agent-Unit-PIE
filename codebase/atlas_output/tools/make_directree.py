"""
This script can operate in two modes:

1. Create directory structure: Reads a Markdown file, scans for a specific section between start and end markers,parses the directory tree structure from that section, and creates the corresponding directories and empty files in the specified base path. It only creates files that do not already exist.

2. Generate directory tree in MD file: Scans a given directory and generates the directory tree structure
in the specified MD file between the start and end markers, including for each file the lines of code (LOC) and token count in brackets.

Usage:
- **Create structure:** 
python make_directree.py --md_file <path> --start_marker <line> --end_marker <line> --base_path <path>

- **Generate tree:** 
python make_directree.py --reverse --base_path <path> --md_file <path> --start_marker <line> --end_marker <line>
"""

import os
import argparse

my_start_marker = '# START'
my_end_marker = '# END'
ignore_dir = ['.git','.pytest_cache','assets']
ignore_files = ['__init__.py']

def parse_args():
    parser = argparse.ArgumentParser(description="Create directory structure from MD file")
    parser.add_argument('--md_file', help='Path to the MD file')
    parser.add_argument('--start_marker', default=my_start_marker, help='Start marker line content')
    parser.add_argument('--end_marker', default=my_end_marker, help='End marker line content')
    parser.add_argument('--base_path', help='Base path for operation')
    parser.add_argument('--reverse', action='store_true', help='Generate tree from directory instead of creating structure')
    parser.add_argument('--ignore_dir', nargs='*', default=ignore_dir, help='List of directory names to ignore')
    parser.add_argument('--ignore_files', nargs='*', default=ignore_files, help='List of file names to ignore')
    return parser.parse_args()

def read_structure(md_file, start_marker, end_marker):
    with open(md_file, 'r') as f:
        lines = f.readlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == start_marker:
            start_idx = i
            break
    if start_idx is None:
        raise ValueError("Start marker not found")
    structure_lines = []
    for line in lines[start_idx + 1:]:
        if line.strip() == end_marker:
            break
        structure_lines.append(line)
    return structure_lines

def parse_tree(lines):
    root = {}
    current_path = []
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        # Replace tree characters with spaces for consistent indent
        line = line.replace('├── ', '  ').replace('└── ', '  ').replace('│   ', '  ')
        indent = len(line) - len(line.lstrip())
        name = line.strip().split('#')[0].strip()
        if not name:
            continue
        level = indent // 2
        current_path = current_path[:level]
        is_dir = name.endswith('/')
        name = name.rstrip('/')
        node = root
        for p in current_path:
            node = node[p]
        if is_dir:
            node[name] = {}
        else:
            node[name] = None
        if is_dir:
            current_path.append(name)
    return root

def create_structure(base_path, tree):
    for name, subtree in tree.items():
        path = os.path.join(base_path, name)
        if subtree is None:
            # file
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    pass
        else:
            # dir
            os.makedirs(path, exist_ok=True)
            create_structure(path, subtree)

def generate_tree(directory, ignored_dirs=[], ignored_files=[]):
    from token_count import count_tokens

    def count_lines(path):
        try:
            with open(path, 'r') as f:
                return len(f.readlines())
        except:
            return 0

    tree = {}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignored_dirs and d != "__pycache__"]
        files = [f for f in files if f not in ignored_files]
        rel_root = os.path.relpath(root, directory)
        if rel_root == '.':
            current = tree
        else:
            parts = rel_root.split(os.sep)
            current = tree
            for part in parts:
                current = current[part]
        for d in dirs:
            current[d] = {}
        for f in files:
            full_path = os.path.join(root, f)
            loc = count_lines(full_path)
            tokens = count_tokens(full_path)
            current[f] = {'loc': loc, 'tokens': tokens}
    return tree

def prune_tree(tree, ignored_dirs):
    for name in list(tree.keys()):
        if name in ignored_dirs:
            del tree[name]
        elif isinstance(tree[name], dict):
            prune_tree(tree[name], ignored_dirs)

def write_tree_to_md(md_file, start_marker, end_marker, tree, directory):
    lines = []
    if os.path.exists(md_file):
        with open(md_file, 'r') as f:
            lines = f.readlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == start_marker:
            start_idx = i
            break
    if start_idx is None:
        lines.append(start_marker + '\n')
        start_idx = len(lines) - 1
    end_idx = None
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip() == end_marker:
            end_idx = i
            break
    if end_idx is None:
        lines.insert(start_idx + 1, end_marker + '\n')
        end_idx = start_idx + 1
    tree_lines = []
    def build_tree_lines(node, prefix='', is_last=True):
        items = list(node.items())
        for i, (name, subtree) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            if isinstance(subtree, dict) and 'loc' in subtree:
                tree_lines.append(f"{prefix}{'└── ' if is_last_item else '├── '}[] {name} [{subtree['loc']} LOC, {subtree['tokens']} tokens]\n")
            else:
                tree_lines.append(f"{prefix}{'└── ' if is_last_item else '├── '}{name}/\n")
                new_prefix = prefix + ('    ' if is_last_item else '│   ')
                build_tree_lines(subtree, new_prefix, is_last_item)
    build_tree_lines(tree)
    lines[start_idx + 1:end_idx] = tree_lines
    with open(md_file, 'w') as f:
        f.writelines(lines)

if __name__ == '__main__':
    args = parse_args()
    if args.reverse:
        if not args.base_path:
            raise ValueError("--base_path is required when using --reverse")
        tree = generate_tree(args.base_path, args.ignore_dir, args.ignore_files)
        prune_tree(tree, args.ignore_dir)
        write_tree_to_md(args.md_file, args.start_marker, args.end_marker, tree, args.base_path)
        print("Directory tree written to MD file.")
    else:
        structure_lines = read_structure(args.md_file, args.start_marker, args.end_marker)
        tree = parse_tree(structure_lines)
        prune_tree(tree, args.ignore_dir)
        create_structure(args.base_path, tree)
        print("Directory structure created.")