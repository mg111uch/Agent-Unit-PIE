# === Graph Database for Codebase Analysis ===
import sqlite3
import os
import ast
from typing import List, Dict, Any, Tuple

class CodeGraphDB:
    """SQLite-based graph database for codebase analysis and GraphRAG context retrieval."""

    def __init__(self, db_path: str = "code_graph.db"):
        """Initialize the graph database."""
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Nodes table: represents classes, functions, modules, etc.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,  -- 'class', 'function', 'module', 'variable', etc.
                    file_path TEXT NOT NULL,
                    line_start INTEGER,
                    line_end INTEGER,
                    content TEXT,
                    metadata TEXT  -- JSON string for additional info
                )
            ''')

            # Edges table: represents relationships between nodes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER,
                    target_id INTEGER,
                    relationship_type TEXT NOT NULL,  -- 'inherits', 'calls', 'imports', 'contains', etc.
                    metadata TEXT,  -- JSON string for additional info
                    FOREIGN KEY (source_id) REFERENCES nodes (id),
                    FOREIGN KEY (target_id) REFERENCES nodes (id)
                )
            ''')

            # Indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_file ON nodes(file_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(relationship_type)')

            conn.commit()

    def add_node(self, name: str, node_type: str, file_path: str,
                 line_start: int = None, line_end: int = None,
                 content: str = None, metadata: Dict[str, Any] = None) -> int:
        """Add a node to the graph."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            metadata_str = str(metadata) if metadata else None
            cursor.execute('''
                INSERT INTO nodes (name, type, file_path, line_start, line_end, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, node_type, file_path, line_start, line_end, content, metadata_str))
            node_id = cursor.lastrowid
            conn.commit()
            return node_id

    def add_edge(self, source_id: int, target_id: int, relationship_type: str,
                 metadata: Dict[str, Any] = None) -> int:
        """Add an edge between two nodes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            metadata_str = str(metadata) if metadata else None
            cursor.execute('''
                INSERT INTO edges (source_id, target_id, relationship_type, metadata)
                VALUES (?, ?, ?, ?)
            ''', (source_id, target_id, relationship_type, metadata_str))
            edge_id = cursor.lastrowid
            conn.commit()
            return edge_id

    def get_node_by_name(self, name: str, file_path: str = None) -> Dict[str, Any]:
        """Get a node by name and optionally file path."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if file_path:
                cursor.execute('SELECT * FROM nodes WHERE name = ? AND file_path = ?', (name, file_path))
            else:
                cursor.execute('SELECT * FROM nodes WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'file_path': row[3],
                    'line_start': row[4],
                    'line_end': row[5],
                    'content': row[6],
                    'metadata': row[7]
                }
            return None

    def get_neighbors(self, node_id: int, relationship_type: str = None) -> List[Dict[str, Any]]:
        """Get neighboring nodes connected by edges."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if relationship_type:
                cursor.execute('''
                    SELECT n.*, e.relationship_type, e.metadata as edge_metadata
                    FROM nodes n
                    JOIN edges e ON (n.id = e.source_id OR n.id = e.target_id)
                    WHERE (e.source_id = ? OR e.target_id = ?) AND e.relationship_type = ?
                    AND n.id != ?
                ''', (node_id, node_id, relationship_type, node_id))
            else:
                cursor.execute('''
                    SELECT n.*, e.relationship_type, e.metadata as edge_metadata
                    FROM nodes n
                    JOIN edges e ON (n.id = e.source_id OR n.id = e.target_id)
                    WHERE (e.source_id = ? OR e.target_id = ?) AND n.id != ?
                ''', (node_id, node_id, node_id))

            neighbors = []
            for row in cursor.fetchall():
                neighbors.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'file_path': row[3],
                    'line_start': row[4],
                    'line_end': row[5],
                    'content': row[6],
                    'metadata': row[7],
                    'relationship_type': row[8],
                    'edge_metadata': row[9]
                })
            return neighbors

    def search_nodes(self, query: str, node_type: str = None) -> List[Dict[str, Any]]:
        """Search nodes by name or content."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            sql = 'SELECT * FROM nodes WHERE (name LIKE ? OR content LIKE ?)'
            params = [f'%{query}%', f'%{query}%']
            if node_type:
                sql += ' AND type = ?'
                params.append(node_type)
            cursor.execute(sql, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'file_path': row[3],
                    'line_start': row[4],
                    'line_end': row[5],
                    'content': row[6],
                    'metadata': row[7]
                })
            return results

    def get_graph_context(self, node_name: str, depth: int = 2) -> Dict[str, Any]:
        """Get graph context around a node for RAG."""
        node = self.get_node_by_name(node_name)
        if not node:
            return None

        context = {
            'center_node': node,
            'neighbors': [],
            'relationships': []
        }

        # Get direct neighbors
        neighbors = self.get_neighbors(node['id'])
        context['neighbors'] = neighbors

        # For deeper context, recursively get neighbors of neighbors
        if depth > 1:
            visited = set([node['id']])
            current_level = [n['id'] for n in neighbors]
            for _ in range(depth - 1):
                next_level = []
                for nid in current_level:
                    if nid not in visited:
                        visited.add(nid)
                        level_neighbors = self.get_neighbors(nid)
                        context['neighbors'].extend(level_neighbors)
                        next_level.extend([n['id'] for n in level_neighbors if n['id'] not in visited])
                current_level = next_level

        return context

    def clear_db(self):
        """Clear all data from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM edges')
            cursor.execute('DELETE FROM nodes')
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="nodes"')
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="edges"')
            conn.commit()

# === Code Analysis Functions ===

def analyze_codebase(db: CodeGraphDB, directory: str = "."):
    """Analyze the codebase and populate the graph database."""
    import ast
    import inspect

    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    # Analyze each file
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content, filename=file_path)

            # Add module node
            module_name = os.path.basename(file_path).replace('.py', '')
            module_id = db.add_node(
                name=module_name,
                node_type='module',
                file_path=file_path,
                content=content[:500] + '...' if len(content) > 500 else content
            )

            # Analyze AST nodes
            analyzer = CodeAnalyzer(db, file_path, module_id)
            analyzer.visit(tree)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze code and build graph."""

    def __init__(self, db: CodeGraphDB, file_path: str, module_id: int):
        self.db = db
        self.file_path = file_path
        self.module_id = module_id
        self.current_class = None
        self.class_stack = []

    def visit_ClassDef(self, node):
        """Handle class definitions."""
        class_id = self.db.add_node(
            name=node.name,
            node_type='class',
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=getattr(node, 'end_lineno', node.lineno),
            content=ast.get_source_segment(open(self.file_path).read(), node) if hasattr(ast, 'get_source_segment') else None,
            metadata={'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]}
        )

        # Add inheritance relationships
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_node = self.db.get_node_by_name(base.id, self.file_path)
                if base_node:
                    self.db.add_edge(class_id, base_node['id'], 'inherits')

        # Add contains relationship with module
        self.db.add_edge(self.module_id, class_id, 'contains')

        # Set current class context
        self.current_class = class_id
        self.class_stack.append(class_id)

        # Visit class body
        self.generic_visit(node)

        # Restore context
        self.class_stack.pop()
        self.current_class = self.class_stack[-1] if self.class_stack else None

    def visit_FunctionDef(self, node):
        """Handle function definitions."""
        func_id = self.db.add_node(
            name=node.name,
            node_type='function',
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=getattr(node, 'end_lineno', node.lineno),
            content=ast.get_source_segment(open(self.file_path).read(), node) if hasattr(ast, 'get_source_segment') else None,
            metadata={'args': [arg.arg for arg in node.args.args]}
        )

        # Add relationship with current class or module
        parent_id = self.current_class if self.current_class else self.module_id
        self.db.add_edge(parent_id, func_id, 'contains')

        # Analyze function calls within this function
        self.generic_visit(node)

    def visit_Call(self, node):
        """Handle function calls."""
        if isinstance(node.func, ast.Name):
            # Simple function call
            caller_name = node.func.id
            # Note: This is a simplified analysis. In a full implementation,
            # you'd need to resolve the actual function being called.
            pass  # For now, skip detailed call analysis

    def visit_Import(self, node):
        """Handle import statements."""
        for alias in node.names:
            imported_name = alias.asname if alias.asname else alias.name
            imported_id = self.db.add_node(
                name=imported_name,
                node_type='import',
                file_path=self.file_path,
                line_start=node.lineno,
                metadata={'module': alias.name}
            )
            self.db.add_edge(self.module_id, imported_id, 'imports')

    def visit_ImportFrom(self, node):
        """Handle from import statements."""
        module_name = node.module if node.module else ''
        for alias in node.names:
            imported_name = alias.asname if alias.asname else alias.name
            imported_id = self.db.add_node(
                name=imported_name,
                node_type='import',
                file_path=self.file_path,
                line_start=node.lineno,
                metadata={'module': module_name, 'attribute': alias.name}
            )
            self.db.add_edge(self.module_id, imported_id, 'imports')

# === Usage Example ===
if __name__ == "__main__":
    # Initialize database
    db = CodeGraphDB()

    # Analyze codebase
    analyze_codebase(db, ".")

    # Example queries
    print("Classes in the codebase:")
    classes = db.search_nodes("", "class")
    for cls in classes:
        print(f"  {cls['name']} in {cls['file_path']}")

    print("\nFunctions in the codebase:")
    functions = db.search_nodes("", "function")
    for func in functions:
        print(f"  {func['name']} in {func['file_path']}")

    # Get context for a specific class
    agent_class = db.get_node_by_name("Agent")
    if agent_class:
        context = db.get_graph_context("Agent")
        print(f"\nContext for Agent class: {len(context['neighbors'])} neighbors")