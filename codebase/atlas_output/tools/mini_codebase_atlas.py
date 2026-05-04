import os
import ast
import re
import json
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

PROJECT_DIR = "/home/manigupt/Hello/python/dota2/claudeSonnet4_5/dota2_gym"
OUTPUT_FILE = "/home/manigupt/Hello/python/dota2/claudeSonnet4_5/codebase_atlas.md"
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'node_modules', '.ipynb_checkpoints', 'dist', 'build', '.next'}
IGNORE_FILES = {'.gitignore', '.env', '.DS_Store'}

class FileInfo:
    """Container for file analysis information."""
    def __init__(self, path: Path, root: Path, counter: int, ext: str):
        self.path = path
        self.rel_path = str(path.relative_to(root))
        self.ref_id = f"F{counter:03d}"
        self.ext = ext

        # Metadata
        self.loc = 0
        self.docstring = None
        self.error = None

        # Code structure
        self.imports = set()
        self.exports = set()
        self.classes = []
        self.functions = []
        self.config_keys = []

        # Special markers
        self.entry_point = False
        self.is_react_component = False
        self.react_components = []
        self.template_engine = None
        self.html_analyzed = False

class CodebaseAtlas:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.files = []  # List of FileInfo objects
        self.file_map = {}  # path -> FileInfo
        self.dependencies = defaultdict(lambda: {'internal': set(), 'external': set()})
        self.reverse_deps = defaultdict(set)
        self.entry_points = []
        self.file_counter = 0

    def generate(self):
        print(f"🔍 Scanning {self.root_dir}...")
        self._scan_files()
        print(f"📊 Found {len(self.files)} files")

        print("🔬 Analyzing code structure...")
        self._analyze_files()

        print("🔗 Building dependency graph...")
        self._build_dependency_graph()

        print("📝 Generating atlas...")
        self._write_atlas()

        print(f"✅ Atlas generated at {OUTPUT_FILE}")

    def _scan_files(self):
        """Scan directory and collect all relevant files."""
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                if file in IGNORE_FILES:
                    continue

                file_path = Path(root) / file
                ext = file_path.suffix.lower()

                if ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.json', '.yaml', '.yml']:
                    self.file_counter += 1
                    file_info = FileInfo(file_path, self.root_dir, self.file_counter, ext)
                    self.files.append(file_info)
                    self.file_map[str(file_path.relative_to(self.root_dir))] = file_info

    def _analyze_files(self):
        """Analyze each file based on its type."""
        for file_info in self.files:
            try:
                if file_info.ext == '.py':
                    self._analyze_python(file_info)
                elif file_info.ext in ['.js', '.jsx', '.ts', '.tsx']:
                    self._analyze_javascript(file_info)
                elif file_info.ext == '.html':
                    self._analyze_html(file_info)
                elif file_info.ext in ['.json', '.yaml', '.yml']:
                    self._analyze_config(file_info)
            except Exception as e:
                file_info.error = f"Parse error: {str(e)}"

    def _analyze_python(self, file_info: FileInfo):
        """Analyze Python file using AST."""
        with open(file_info.path, 'r', encoding='utf-8') as f:
            content = f.read()
            file_info.loc = len([l for l in content.split('\n') if l.strip()])

        try:
            tree = ast.parse(content)
        except:
            file_info.error = "AST parse failed"
            return

        # Extract module docstring
        file_info.docstring = ast.get_docstring(tree)

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_info.imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    file_info.imports.add(node.module.split('.')[0])

        # Extract classes, functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                cls_info = self._parse_python_class(node)
                file_info.classes.append(cls_info)
            elif isinstance(node, ast.FunctionDef):
                func_info = self._parse_python_function(node)
                file_info.functions.append(func_info)
            elif isinstance(node, ast.If):
                # Check for if __name__ == "__main__"
                if self._is_main_guard(node):
                    file_info.entry_point = True
                    self.entry_points.append((file_info.ref_id, "main guard"))

    def _parse_python_class(self, node: ast.ClassDef) -> Dict:
        """Parse Python class definition."""
        bases = [self._get_name(b) for b in node.bases]
        methods = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._parse_python_function(item, is_method=True)
                methods.append(method_info)

        return {
            'name': node.name,
            'bases': bases,
            'methods': methods,
            'docstring': ast.get_docstring(node)
        }

    def _parse_python_function(self, node: ast.FunctionDef, is_method: bool = False) -> Dict:
        """Parse Python function/method definition."""
        # Get parameters
        args = []
        for arg in node.args.args:
            annotation = self._get_annotation(arg.annotation) if arg.annotation else None
            args.append((arg.arg, annotation))

        # Get return type
        returns = self._get_annotation(node.returns) if node.returns else None

        # Check if it's an entry point
        is_entry = node.name in ['main', 'run', 'start', 'app', 'execute']

        # Check for decorators (Flask routes, Click commands, etc.)
        decorators = [self._get_name(d) for d in node.decorator_list]
        if any(d in ['route', 'app.route', 'command', 'click.command'] for d in decorators):
            is_entry = True

        return {
            'name': node.name,
            'args': args,
            'returns': returns,
            'docstring': ast.get_docstring(node),
            'is_entry': is_entry,
            'decorators': decorators,
            'is_method': is_method
        }

    def _get_annotation(self, node) -> str:
        """Get type annotation as string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        return "Any"

    def _get_name(self, node) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "Unknown"

    def _is_main_guard(self, node: ast.If) -> bool:
        """Check if this is if __name__ == '__main__'."""
        if isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == '__name__':
                return True
        return False

    def _analyze_javascript(self, file_info: FileInfo):
        """Analyze JavaScript/TypeScript file using regex patterns."""
        with open(file_info.path, 'r', encoding='utf-8') as f:
            content = f.read()
            file_info.loc = len([l for l in content.split('\n') if l.strip()])

        # Extract imports
        # import X from 'module'
        imports = re.findall(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", content)
        # const X = require('module')
        imports += re.findall(r"require\(['\"]([^'\"]+)[\"\']", content)

        for imp in imports:
            if imp.startswith('.'):
                file_info.imports.add(imp)  # Relative import
            else:
                file_info.imports.add(imp.split('/')[0])  # Package name

        # Extract exports
        # export default, export function, export const, etc.
        exports = re.findall(r"export\s+(?:default\s+)?(?:function|const|class|let|var)\s+(\w+)", content)
        file_info.exports = set(exports)

        # Extract functions
        # function name(...) { }
        funcs = re.findall(r"(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)", content)
        for name, params in funcs:
            file_info.functions.append({
                'name': name,
                'args': [p.strip() for p in params.split(',') if p.strip()],
                'is_async': 'async' in content[:content.find(f'function {name}')][-10:] if content.find(f'function {name}') != -1 else False
            })

        # Arrow functions: const name = (...) => { }
        arrow_funcs = re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>", content)
        for name, params in arrow_funcs:
            file_info.functions.append({
                'name': name,
                'args': [p.strip() for p in params.split(',') if p.strip()],
                'is_async': 'async' in content[:content.find(name)][-20:] if content.find(name) != -1 else False
            })

        # Extract classes
        classes = re.findall(r"class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{", content)
        for cls_name, base in classes:
            # Find methods in class
            class_start = content.find(f'class {cls_name}')
            # Simple heuristic: find methods until next class or EOF
            class_content = content[class_start:class_start+5000]  # Limit search
            methods = re.findall(r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*{", class_content)

            file_info.classes.append({
                'name': cls_name,
                'bases': [base] if base else [],
                'methods': [{'name': m} for m in methods[:20]]  # Limit methods
            })

        # Detect React components (JSX/TSX)
        if file_info.ext in ['.jsx', '.tsx']:
            # Function components: export default function ComponentName
            react_comps = re.findall(r"export\s+default\s+function\s+(\w+)", content)
            # const Component = () => ( ... JSX ...
            react_comps += re.findall(r"(?:const|let)\s+([A-Z]\w+)\s*=\s*\([^)]*\)\s*=>", content)

            if react_comps:
                file_info.is_react_component = True
                file_info.react_components = react_comps

        # Entry points
        if re.search(r"ReactDOM\.render|createRoot|app\.listen|server\.listen", content):
            file_info.entry_point = True
            self.entry_points.append((file_info.ref_id, "detected entry"))

    def _analyze_html(self, file_info: FileInfo):
        """Analyze HTML file (basic detection)."""
        with open(file_info.path, 'r', encoding='utf-8') as f:
            content = f.read()
            file_info.loc = len([l for l in content.split('\n') if l.strip()])

        # Detect template engine
        if '{%' in content or '{{' in content:
            file_info.template_engine = 'Jinja2/Django'
        elif '<%=' in content:
            file_info.template_engine = 'ERB'

        file_info.html_analyzed = True

    def _analyze_config(self, file_info: FileInfo):
        """Analyze JSON/YAML config file."""
        try:
            with open(file_info.path, 'r', encoding='utf-8') as f:
                if file_info.ext == '.json':
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)

            if isinstance(data, dict):
                file_info.config_keys = list(data.keys())
            elif isinstance(data, list):
                file_info.config_keys = [f"List[{len(data)} items]"]
        except Exception as e:
            file_info.error = f"Config parse error: {str(e)}"

    def _build_dependency_graph(self):
        """Build internal and external dependency relationships."""
        # Resolve all Python internal imports
        python_modules = {f.path.stem: f for f in self.files if f.ext == '.py'}

        for file_info in self.files:
            for imp in file_info.imports:
                # Check if it's an internal module
                if imp in python_modules and python_modules[imp] != file_info:
                    target = python_modules[imp]
                    rel_path = str(target.path.relative_to(self.root_dir))
                    self.dependencies[file_info.rel_path]['internal'].add(target.ref_id)
                    self.reverse_deps[target.ref_id].add(file_info.ref_id)
                elif imp.startswith('.'):
                    # Relative import - try to resolve
                    resolved = self._resolve_relative_import(file_info, imp)
                    if resolved:
                        self.dependencies[file_info.rel_path]['internal'].add(resolved)
                        self.reverse_deps[resolved].add(file_info.ref_id)
                else:
                    # External package
                    self.dependencies[file_info.rel_path]['external'].add(imp)

    def _resolve_relative_import(self, file_info: FileInfo, rel_import: str) -> str:
        """Resolve relative import to file reference ID."""
        # Simple resolution: ./module.js or ../module.js
        current_dir = file_info.path.parent

        # Count the ../ levels
        parts = rel_import.split('/')
        for part in parts:
            if part == '..':
                current_dir = current_dir.parent
            elif part == '.':
                continue
            else:
                # This is the module name
                module_name = part
                break

        # Try different extensions
        for ext in ['.js', '.jsx', '.ts', '.tsx', '.py']:
            potential_path = current_dir / f"{module_name}{ext}"
            if potential_path.exists():
                rel_path = str(potential_path.relative_to(self.root_dir))
                if rel_path in self.file_map:
                    return self.file_map[rel_path].ref_id

        return None

    def _write_atlas(self):
        """Write the complete atlas to markdown file."""
        lines = []

        # Header
        lines.append("# 🗺️ CODEBASE ATLAS\n")
        lines.append(f"**Project:** `{self.root_dir}`\n")
        lines.append(f"**Generated:** {self._get_timestamp()}\n")
        lines.append("---\n")

        # Legend
        lines.append("## 📖 Legend\n")
        lines.append("- **Cls** = Class | **Fn** = Function | **Meth** = Method\n")
        lines.append("- **Dep** = Dependency | **Ext** = External Library\n")
        lines.append("- **⚡** = Entry Point | **⚛️** = React Component\n")
        lines.append("- **[FXXX]** = File Reference ID\n")
        lines.append("---\n")

        # Overview
        lines.append("## 📊 Overview\n")
        total_loc = sum(f.loc for f in self.files if f.loc)
        lang_stats = self._get_language_stats()
        lines.append(f"- **Total Files:** {len(self.files)}\n")
        lines.append(f"- **Total LOC:** ~{total_loc:,}\n")
        lines.append(f"- **Languages:** {lang_stats}\n")
        if self.entry_points:
            entry_list = ', '.join([f"[{ref}]" for ref, _ in self.entry_points])
            lines.append(f"- **Entry Points:** {entry_list}\n")
        lines.append("\n")

        # Dependency Graph
        lines.append("## 🔗 Dependency Graph\n")
        lines.append("### Internal Dependencies\n")
        for file_path, deps in sorted(self.dependencies.items()):
            if deps['internal']:
                file_info = self.file_map[file_path]
                internal_list = ', '.join(sorted(deps['internal']))
                lines.append(f"- **{file_info.ref_id}** → [{internal_list}]\n")

        lines.append("\n### External Libraries\n")
        all_external = defaultdict(set)
        for file_path, deps in self.dependencies.items():
            file_info = self.file_map[file_path]
            lang = 'Python' if file_info.ext == '.py' else 'JavaScript'
            all_external[lang].update(deps['external'])

        for lang, libs in sorted(all_external.items()):
            if libs:
                libs_str = ', '.join(sorted(libs))
                lines.append(f"- **{lang}:** [{libs_str}]\n")
        lines.append("\n")

        # Quick Reference
        lines.append("## 🔍 Quick Reference\n")

        # Classes index
        class_index = {}
        for f in self.files:
            for cls in f.classes:
                class_index[cls['name']] = f.ref_id

        if class_index:
            lines.append("### Classes Defined\n")
            for cls_name, ref in sorted(class_index.items())[:20]:  # Top 20
                lines.append(f"- `{cls_name}` → [{ref}]\n")

        # What uses what
        lines.append("\n### Reverse Dependencies (Top Referenced)\n")
        top_referenced = sorted(self.reverse_deps.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for ref_id, dependents in top_referenced:
            dep_list = ', '.join(sorted(dependents))
            lines.append(f"- **{ref_id}** ← [{dep_list}]\n")

        lines.append("\n---\n")

        # Detailed Breakdown
        lines.append("## 📦 Detailed Breakdown\n\n")

        # Group files by directory
        by_directory = defaultdict(list)
        for f in self.files:
            dir_name = str(f.path.parent.relative_to(self.root_dir))
            if dir_name == '.':
                dir_name = 'Root'
            by_directory[dir_name].append(f)

        for dir_name, files in sorted(by_directory.items()):
            lines.append(f"### 📂 {dir_name}\n\n")

            for file_info in sorted(files, key=lambda x: x.path.name):
                lines.extend(self._format_file_info(file_info))

            lines.append("\n")

        # Write to file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(''.join(lines))

    def _format_file_info(self, f: FileInfo) -> List[str]:
        """Format a single file's information."""
        lines = []

        # File header
        icon = self._get_file_icon(f.ext)
        lines.append(f"#### {f.ref_id} {icon} `{f.path.name}`")
        if f.loc:
            lines.append(f" ({f.loc} LOC)")
        lines.append("\n")

        # Purpose/Docstring
        if f.docstring:
            lines.append(f"**Purpose:** \"{f.docstring.split(chr(10))[0][:100]}\"\n\n")

        # Dependencies
        deps = self.dependencies[f.rel_path]
        if deps['internal'] or deps['external']:
            dep_parts = []
            if deps['internal']:
                dep_parts.append(f"Internal: [{', '.join(sorted(deps['internal']))}]")
            if deps['external']:
                ext_list = ', '.join(sorted(list(deps['external'])[:5]))
                if len(deps['external']) > 5:
                    ext_list += f", +{len(deps['external'])-5} more"
                dep_parts.append(f"Ext: [{ext_list}]")
            lines.append(f"**Deps:** {' | '.join(dep_parts)}\n\n")

        # Entry point marker
        if f.entry_point:
            lines.append("⚡ **ENTRY POINT**\n\n")

        # React component marker
        if f.is_react_component:
            comp_list = ', '.join(f.react_components)
            lines.append(f"⚛️ **React Components:** `{comp_list}`\n\n")

        # Error
        if f.error:
            lines.append(f"⚠️ *{f.error}*\n\n")
            return lines

        # Classes
        if f.classes:
            lines.append("**Classes:**\n")
            for cls in f.classes:
                base_str = f" extends {', '.join(cls['bases'])}" if cls['bases'] else ""
                lines.append(f"- **Cls:** `{cls['name']}`{base_str}\n")
                if cls.get('docstring'):
                    lines.append(f"  - *{cls['docstring'].split(chr(10))[0][:80]}*\n")
                if cls.get('methods'):
                    method_names = [m['name'] if isinstance(m, dict) else m for m in cls['methods']]
                    lines.append(f"  - Methods: [{', '.join(method_names)}]\n")
            lines.append("\n")

        # Functions
        if f.functions:
            lines.append("**Functions:**\n")
            for func in f.functions:
                if isinstance(func, dict):
                    # Python function with full signature
                    args_str = ', '.join([f"{arg}: {typ}" if typ else arg for arg, typ in func.get('args', [])])
                    ret_str = f" -> {func['returns']}" if func.get('returns') else ""
                    entry_marker = " ⚡" if func.get('is_entry') else ""
                    lines.append(f"- **Fn:** `{func['name']}({args_str}){ret_str}`{entry_marker}\n")
                    if func.get('docstring'):
                        lines.append(f"  - *{func['docstring'].split(chr(10))[0][:80]}*\n")
                else:
                    # JavaScript function (simpler)
                    lines.append(f"- **Fn:** `{func}`\n")
            lines.append("\n")

        # Config keys
        if f.config_keys:
            keys_str = ', '.join(f.config_keys[:15])
            if len(f.config_keys) > 15:
                keys_str += f", +{len(f.config_keys)-15} more"
            lines.append(f"**Config Keys:** `{keys_str}`\n\n")

        # HTML info
        if f.html_analyzed:
            if f.template_engine:
                lines.append(f"**Template Engine:** {f.template_engine}\n\n")
            else:
                lines.append("*Static HTML file*\n\n")

        lines.append("---\n\n")
        return lines

    def _get_language_stats(self) -> str:
        """Get language distribution statistics."""
        lang_count = defaultdict(int)
        for f in self.files:
            if f.ext == '.py':
                lang_count['Python'] += 1
            elif f.ext in ['.js', '.jsx', '.ts', '.tsx']:
                lang_count['JavaScript/TypeScript'] += 1
            elif f.ext in ['.json', '.yaml', '.yml']:
                lang_count['Config'] += 1
            elif f.ext == '.html':
                lang_count['HTML'] += 1

        total = sum(lang_count.values())
        stats = []
        for lang, count in sorted(lang_count.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            stats.append(f"{lang} ({pct:.0f}%)")

        return ', '.join(stats)

    def _get_file_icon(self, ext: str) -> str:
        """Get emoji icon for file type."""
        icons = {
            '.py': '🐍',
            '.js': '📜',
            '.jsx': '⚛️',
            '.ts': '📘',
            '.tsx': '⚛️',
            '.html': '🌐',
            '.json': '📋',
            '.yaml': '📋',
            '.yml': '📋'
        }
        return icons.get(ext, '📄')

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """Main entry point."""
    if not os.path.exists(PROJECT_DIR):
        print(f"❌ Error: Directory '{PROJECT_DIR}' not found.")
        print("Please update PROJECT_DIR in the script configuration.")
        return

    atlas = CodebaseAtlas(PROJECT_DIR)
    atlas.generate()


if __name__ == "__main__":
    main()