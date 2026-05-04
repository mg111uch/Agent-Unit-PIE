#!/usr/bin/env python3
"""
Standalone SQLite-Based RAG Pipeline (No Chunking, No Embeddings, No Generation)
===============================================================

This script implements a lightweight RAG pipeline for codebase querying using
SQLite FTS5 for keyword search. Treats full modular files as atomic units.

- Ingestion: Load files from a directory into DB, extracting metadata from embedded
  YAML in Python module docstrings (summary, dependencies, tags, hierarchy_mapping,
  graph_methods). Content is cleaned by removing metadata docstrings, all docstrings,
  comments, and blank lines to focus search on core code.
- Retrieval: Keyword search, returns top-k full docs with ranks.

Usage:
  python sqlrag.py ingest --dir /path/to/codebase --db rag.db
  python sqlrag.py query --query "authentication logic" --top_k 3 --db rag.db
"""

import argparse
import ast
import json
import os
import sqlite3
import glob
import re
import yaml
from typing import List, Tuple, Dict, Any

# Config (inline, simple)
DB_PATH = 'rag.db'
TOP_K_DEFAULT = 3
SUPPORTED_EXTS = ['.py', '.ts', '.tsx', '.js', '.jsx', '.html']  # Extend as needed

def remove_docstrings(node):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
    for child in ast.iter_child_nodes(node):
        remove_docstrings(child)

def init_schema(conn: sqlite3.Connection):
    """Initialize SQLite schema with FTS5 table."""
    cursor = conn.cursor()
    # Drop existing tables to recreate with new schema
    cursor.execute('DROP TABLE IF EXISTS doc_contents')
    cursor.execute('DROP TABLE IF EXISTS docs')
    # Core FTS5 table for full-file indexing
    cursor.execute('''
        CREATE VIRTUAL TABLE docs USING fts5(
            content, metadata UNINDEXED, title UNINDEXED,
            tokenize='porter'
        )
    ''')
    # Optional: Backup table with detailed columns
    cursor.execute('''
        CREATE TABLE doc_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            summary TEXT,
            dependencies TEXT,
            language TEXT,
            line_count INTEGER,
            tags TEXT,
            hierarchy_mapping TEXT,
            graph_methods TEXT,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_modified REAL
        )
    ''')
    cursor.execute('CREATE INDEX idx_doc_contents_path ON doc_contents(path)')
    conn.commit()

def load_files(dir_path: str) -> List[Tuple[str, str]]:
    """Recursively load supported files from directory."""
    patterns = [f'**/*{ext}' for ext in SUPPORTED_EXTS]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(dir_path, pattern), recursive=True))

    loaded = []
    for file_path in files:
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                loaded.append((file_path, content))
    return loaded

def extract_metadata(file_path: str, content: str) -> Dict[str, Any]:
    """Extract metadata from file content."""
    ext = os.path.splitext(file_path)[1]
    language = ext.lstrip('.') if ext else 'unknown'
    lines = content.splitlines()
    line_count = len(lines)
    # Defaults
    summary = '\n'.join(lines[:5]) if lines else ''
    dependencies = []
    tags = []
    hierarchy_mapping = {}
    graph_methods = {}
    # Try to parse metadata from docstring for Python or comment for HTML
    parsed = False
    if language == 'py':
        try:
            tree = ast.parse(content)
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
                docstring = tree.body[0].value.s
                if 'metadata:' in docstring:
                    meta_dict = yaml.safe_load(docstring)
                    if 'metadata' in meta_dict:
                        meta_data = meta_dict['metadata']
                        summary = meta_data.get('summary', summary)
                        dependencies = meta_data.get('dependencies', dependencies)
                        tags = meta_data.get('tags', tags)
                        hierarchy_mapping = meta_data.get('hierarchy_mapping', hierarchy_mapping)
                        graph_methods = meta_data.get('graph_methods', graph_methods)
                        parsed = True
        except:
            pass
    elif language == 'html':
        if 'metadata:' in content:
            comment_match = re.search(r'<!--(.*?)-->', content, re.DOTALL)
            if comment_match:
                comment_content = comment_match.group(1)
                if 'metadata:' in comment_content:
                    try:
                        meta_dict = yaml.safe_load(comment_content)
                        if 'metadata' in meta_dict:
                            meta_data = meta_dict['metadata']
                            summary = meta_data.get('summary', summary)
                            dependencies = meta_data.get('dependencies', dependencies)
                            tags = meta_data.get('tags', tags)
                            hierarchy_mapping = meta_data.get('hierarchy_mapping', hierarchy_mapping)
                            graph_methods = meta_data.get('graph_methods', graph_methods)
                            parsed = True
                            # Remove the metadata comment from content
                            content = content.replace(comment_match.group(0), '')
                    except:
                        pass
        # Fallback to title if no metadata
        if not parsed:
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            if title_match:
                summary = title_match.group(1).strip()
    elif language in ['js', 'ts', 'tsx', 'jsx']:
        if content.strip().startswith('/**'):
            jsdoc_match = re.search(r'/\*\*(.*?)\*/', content, re.DOTALL)
            if jsdoc_match:
                jsdoc_content = jsdoc_match.group(1)
                if 'metadata:' in jsdoc_content:
                    try:
                        meta_dict = yaml.safe_load(jsdoc_content)
                        if 'metadata' in meta_dict:
                            meta_data = meta_dict['metadata']
                            summary = meta_data.get('summary', summary)
                            dependencies = meta_data.get('dependencies', dependencies)
                            tags = meta_data.get('tags', tags)
                            hierarchy_mapping = meta_data.get('hierarchy_mapping', hierarchy_mapping)
                            graph_methods = meta_data.get('graph_methods', graph_methods)
                            parsed = True
                            # Remove the JSDoc from content
                            content = content.replace(jsdoc_match.group(0), '')
                    except:
                        pass
    # Try to parse metadata from docstring for Python
    parsed = False
    if language == 'py':
        try:
            tree = ast.parse(content)
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
                docstring = tree.body[0].value.s
                if 'metadata:' in docstring:
                    meta_dict = yaml.safe_load(docstring)
                    if 'metadata' in meta_dict:
                        meta_data = meta_dict['metadata']
                        summary = meta_data.get('summary', summary)
                        dependencies = meta_data.get('dependencies', dependencies)
                        tags = meta_data.get('tags', tags)
                        hierarchy_mapping = meta_data.get('hierarchy_mapping', hierarchy_mapping)
                        graph_methods = meta_data.get('graph_methods', graph_methods)
                        parsed = True
        except:
            pass
    # Exclude metadata docstring from content if parsed
    if parsed and language == 'py':
        pos1 = content.find('"""')
        if pos1 != -1:
            pos2 = content.find('"""', pos1 + 3)
            if pos2 != -1:
                content = content[pos2 + 3:].lstrip()
    # Extract dependencies if not set from metadata
    if not dependencies:
        if language == 'py':
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    dependencies.append(stripped)
        elif language in ['js', 'ts', 'tsx', 'jsx']:
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('const ') and 'require(' in stripped:
                    dependencies.append(stripped)
    # Clean content for all supported files
    if language in ['py', 'ts', 'tsx', 'js', 'jsx', 'html']:
        # Remove docstrings for Python
        if language == 'py':
            try:
                tree = ast.parse(content)
                remove_docstrings(tree)
                content = ast.unparse(tree)
            except:
                pass
        elif language == 'html':
            # Remove HTML comments
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        else:
            # Remove comment lines for JS/TS
            comment_prefix = '//'
            lines = content.splitlines()
            lines = [line for line in lines if not line.strip().startswith(comment_prefix)]
            content = '\n'.join(lines)
        # Remove blank lines for all
        lines = content.splitlines()
        lines = [line for line in lines if line.strip()]
        content = '\n'.join(lines)
    # Update line_count based on cleaned content
    line_count = len(content.splitlines())
    # JSON dumps
    dependencies = json.dumps(dependencies)
    tags = json.dumps(tags)
    hierarchy_mapping = json.dumps(hierarchy_mapping)
    graph_methods = json.dumps(graph_methods)
    last_modified = os.path.getmtime(file_path)
    return {
        'path': file_path,
        'summary': summary,
        'dependencies': dependencies,
        'language': language,
        'line_count': line_count,
        'tags': tags,
        'hierarchy_mapping': hierarchy_mapping,
        'graph_methods': graph_methods,
        'content': content,
        'last_modified': last_modified
    }

def ingest_files(files: List[Tuple[str, str]], conn: sqlite3.Connection):
    """Insert full files into DB."""
    cursor = conn.cursor()
    for file_path, content in files:
        meta = extract_metadata(file_path, content)
        print(f"File: {file_path}, Line count: {meta['line_count']}")
        meta_str = json.dumps(meta)
        title = os.path.basename(file_path)
        # Insert to FTS
        cursor.execute(
            'INSERT INTO docs (content, metadata, title) VALUES (?, ?, ?)',
            (content, meta_str, title)
        )
        # Sync to contents
        cursor.execute('''
            INSERT INTO doc_contents (path, summary, dependencies, language, line_count, tags, hierarchy_mapping, graph_methods, content, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            meta['path'], meta['summary'], meta['dependencies'], meta['language'], meta['line_count'],
            meta['tags'], meta['hierarchy_mapping'], meta['graph_methods'], meta['content'], meta['last_modified']
        ))
    conn.commit()

def search_docs(query: str, top_k: int, conn: sqlite3.Connection) -> List[Tuple[str, Dict[str, Any], float]]:
    """Retrieve top-k full docs matching query."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT content, metadata, rank FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?',
        (query, top_k)
    )
    results = []
    for row in cursor.fetchall():
        content, meta_str, rank = row
        meta = json.loads(meta_str)
        results.append((content, meta, rank))
    return results

def print_results(results: List[Tuple[str, Dict[str, Any], float]]):
    """Simple print of retrieved docs (no LLM generation)."""
    for i, (content, meta, rank) in enumerate(results, 1):
        print(f"\n--- Result {i} (Rank: {rank:.2f}) ---")
        print(f"Path: {meta['path']}")
        print(f"Content Preview: {content[:500]}...")  # Truncate for readability
        print("-" * 50)

def main():
    parser = argparse.ArgumentParser(description="SQLite RAG Pipeline CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Ingest subcommand
    ingest_parser = subparsers.add_parser('ingest', help='Ingest files from dir')
    ingest_parser.add_argument('--dir', required=True, help='Path to codebase dir')
    ingest_parser.add_argument('--db', default=DB_PATH, help='SQLite DB path')

    # Query subcommand
    query_parser = subparsers.add_parser('query', help='Search codebase')
    query_parser.add_argument('--query', required=True, help='Search query (e.g., "auth AND login")')
    query_parser.add_argument('--top_k', type=int, default=TOP_K_DEFAULT, help='Number of results')
    query_parser.add_argument('--db', default=DB_PATH, help='SQLite DB path')

    args = parser.parse_args()

    if args.command == 'ingest':
        # Remove old db file to create new one
        if os.path.exists(args.db):
            os.remove(args.db)
        conn = sqlite3.connect(args.db)
        init_schema(conn)
    else:
        # For query, connect to existing db
        if not os.path.exists(args.db):
            print(f"Database {args.db} does not exist. Run ingest first.")
            return
        conn = sqlite3.connect(args.db)

    if args.command == 'ingest':
        files = load_files(args.dir)
        print(f"Loading {len(files)} files...")
        ingest_files(files, conn)
        print("Ingestion complete.")
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(line_count) FROM doc_contents')
        total = cursor.fetchone()[0]
        print(f"Total lines in codebase: {total}")
    
    elif args.command == 'query':
        results = search_docs(args.query, args.top_k, conn)
        if results:
            print_results(results)
        else:
            print("No matches found.")

    conn.close()

if __name__ == "__main__":
    main()