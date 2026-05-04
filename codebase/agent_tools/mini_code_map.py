import os
import ast
import json
import yaml
from pathlib import Path

# --- CONFIGURATION ---
LEGACY_DIR = "/home/manigupt/Hello/python/control/dota2/grok4/dota2_gym"  # Point this to your legacy folder
OUTPUT_FILE = "/home/manigupt/Hello/python/control/dota2/grok4/legacy_atlas.md"
IGNORE_DIRS = {'.git', '__pycache__', 'venv', '.ipynb_checkpoints'}
# ---------------------

class AtlasGenerator:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.atlas_data = []

    def parse_python_file(self, file_path):
        """Extracts classes, functions, and methods using AST."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                node = ast.parse(f.read())
            
            info = {"classes": [], "functions": []}
            
            for item in node.body:
                if isinstance(item, ast.ClassDef):
                    methods = [n.name for n in item.body if isinstance(n, ast.FunctionDef)]
                    info["classes"].append({"name": item.name, "methods": methods})
                elif isinstance(item, ast.FunctionDef):
                    info["functions"].append(item.name)
            return info
        except Exception as e:
            return f"Error parsing: {str(e)}"

    def parse_config_file(self, file_path, file_type):
        """Summarizes keys in JSON/YAML files."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_type == '.json':
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    return list(data.keys())
                elif isinstance(data, list) and len(data) > 0:
                    return f"List of {len(data)} items"
                return "Empty or primitive data"
        except Exception as e:
            return f"Error reading: {str(e)}"

    def generate(self):
        markdown = ["# LEGACY CODE ATLAS\n", f"Generated from: `{self.root_dir}`\n"]
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            rel_path = os.path.relpath(root, self.root_dir)
            if rel_path == ".":
                rel_path = "Root"
            
            markdown.append(f"## 📂 Directory: {rel_path}")
            
            for file in sorted(files):
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                markdown.append(f"### 📄 `{file}`")
                
                if ext == '.py':
                    data = self.parse_python_file(file_path)
                    if isinstance(data, dict):
                        if data["classes"]:
                            for cls in data["classes"]:
                                markdown.append(f"- **Class:** `{cls['name']}`")
                                for m in cls['methods']:
                                    markdown.append(f"  - Method: `{m}()`")
                        if data["functions"]:
                            for func in data["functions"]:
                                markdown.append(f"- **Function:** `{func}()`")
                    else:
                        markdown.append(f"- ⚠️ {data}")
                
                elif ext in ['.json', '.yaml', '.yml']:
                    keys = self.parse_config_file(file_path, ext)
                    markdown.append(f"- **Config Keys:** `{', '.join(keys) if isinstance(keys, list) else keys}`")
                
                markdown.append("") # Spacer

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(markdown))
        print(f"Success! Atlas generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    if os.path.exists(LEGACY_DIR):
        generator = AtlasGenerator(LEGACY_DIR)
        generator.generate()
    else:
        print(f"Directory {LEGACY_DIR} not found. Please update LEGACY_DIR in the script.")