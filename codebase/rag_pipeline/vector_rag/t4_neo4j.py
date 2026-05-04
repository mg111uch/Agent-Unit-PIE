import os
import dotenv
import uuid
from t2_embedding import generate_embedding
from t1_parseChunk import extract_python_chunks,parser,get_node_text,PY_LANGUAGE
from python.rag_pipeline.ChunkEmbedChroma import code_collection
# import networkx as nx # For in-memory graph building before pushing to Neo4j
from neo4j import GraphDatabase

# Load environment variables from your .env file
# Replace 'your-auradb-credentials.env' with the actual filename you downloaded
load_status = dotenv.load_dotenv("neo4j-auradb-auth.env")
if not load_status:
    print("Warning: .env file not found or could not be loaded. Ensure it's in the same directory and named correctly.")
    # Fallback for direct input if .env fails (not recommended for production)
    # URI = "neo4j+s://your_uri.databases.neo4j.io"
    # USERNAME = "neo4j"
    # PASSWORD = "your_strong_password"
else:
    URI = os.getenv("NEO4J_URI")
    USERNAME = os.getenv("NEO4J_USERNAME")
    PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([URI, USERNAME, PASSWORD]):
    print("Error: Missing Neo4j AuraDB credentials. Please check your .env file or environment variables.")
    exit(1)

class AuraDBCodeGraph:
    def __init__(self, uri, user, password):
        if not (uri and user and password):
            raise ValueError("Neo4j AuraDB credentials are not provided or loaded correctly.")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        try:
            self.driver.verify_connectivity()
            print("Successfully connected to AuraDB for graph operations!")
        except Exception as e:
            print(f"Error connecting to AuraDB: {e}")
            raise

    def close(self):
        self.driver.close()
        print("AuraDB connection closed for graph operations.")

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    def create_function_node(self, function_name, file_path, start_line, end_line, chroma_id=None, class_name=None):
        """Creates or updates a Function node in Neo4j."""
        query = """
        MERGE (f:Function {name: $function_name, file_path: $file_path})
        ON CREATE SET f.start_line = $start_line, f.end_line = $end_line, f.chroma_id = $chroma_id, f.class_name = $class_name
        ON MATCH SET f.start_line = $start_line, f.end_line = $end_line, f.chroma_id = $chroma_id, f.class_name = $class_name
        RETURN f
        """
        params = {
            "function_name": function_name,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "chroma_id": chroma_id,
            "class_name": class_name
        }
        return self.run_query(query, params)

    def create_class_node(self, class_name, file_path, chroma_id=None):
        """Creates or updates a Class node in Neo4j."""
        query = """
        MERGE (c:Class {name: $class_name, file_path: $file_path})
        ON CREATE SET c.chroma_id = $chroma_id
        ON MATCH SET c.chroma_id = $chroma_id
        RETURN c
        """
        params = {
            "class_name": class_name,
            "file_path": file_path,
            "chroma_id": chroma_id
        }
        return self.run_query(query, params)

    def create_defines_relationship(self, class_name, file_path, function_name):
        """Creates a (Class)-[:DEFINES]->(Function) relationship."""
        query = """
        MATCH (c:Class {name: $class_name, file_path: $file_path})
        MATCH (f:Function {name: $function_name, file_path: $file_path})
        MERGE (c)-[:DEFINES]->(f)
        RETURN c, f
        """
        params = {
            "class_name": class_name,
            "file_path": file_path,
            "function_name": function_name
        }
        return self.run_query(query, params)

    def create_calls_relationship(self, caller_name, caller_file, callee_name, callee_file):
        """Creates a (Function)-[:CALLS]->(Function) relationship."""
        # This is a simplified version; real call graph needs deeper AST analysis
        query = """
        MATCH (caller:Function {name: $caller_name, file_path: $caller_file})
        MATCH (callee:Function {name: $callee_name, file_path: $callee_file})
        MERGE (caller)-[:CALLS]->(callee)
        RETURN caller, callee
        """
        params = {
            "caller_name": caller_name, "caller_file": caller_file,
            "callee_name": callee_name, "callee_file": callee_file
        }
        return self.run_query(query, params)

    def create_imports_relationship(self, importing_file, imported_module):
        """Creates a (File)-[:IMPORTS]->(Module) relationship."""
        query = """
        MERGE (f:File {path: $importing_file})
        MERGE (m:Module {name: $imported_module})
        MERGE (f)-[:IMPORTS]->(m)
        RETURN f, m
        """
        params = {
            "importing_file": importing_file,
            "imported_module": imported_module
        }
        return self.run_query(query, params)


# Helper function to extract simple call relationships (needs improvement for robustness)
def extract_function_calls(source_code_bytes, file_path):
    """
    A simple (and somewhat naive) way to extract function calls for demonstration.
    Real-world call graph extraction requires more sophisticated AST traversal.
    """
    calls = []
    tree = parser.parse(source_code_bytes)
    root_node = tree.root_node
    
    # Find all function definitions in the current file
    functions_in_file = set()
    cursor = root_node.walk()
    if cursor.goto_first_child():
        while True:
            if cursor.node.type == 'function_definition':
                func_name_node = cursor.node.child_by_field_name('name')
                if func_name_node:
                    functions_in_file.add(get_node_text(func_name_node, source_code_bytes))
            if not cursor.goto_next_sibling():
                break

    # Traverse the tree to find 'call' nodes
    # This is a simplified approach, a real call graph needs to resolve scopes etc.
    q_calls = PY_LANGUAGE.query("""
        (call function: (identifier) @function_name)
    """)

    captures = q_calls.captures(root_node)

    for capture, name in captures:
        if name == 'function_name':
            called_function = get_node_text(capture, source_code_bytes)
            # Find the enclosing function/class for the current 'call'
            parent_func = None
            parent_class = None
            current_node = capture
            while current_node:
                if current_node.type == 'function_definition':
                    parent_func_name_node = current_node.child_by_field_name('name')
                    if parent_func_name_node:
                        parent_func = get_node_text(parent_func_name_node, source_code_bytes)
                    break # Stop at the first enclosing function
                if current_node.type == 'class_definition':
                    parent_class_name_node = current_node.child_by_field_name('name')
                    if parent_class_name_node:
                        parent_class = get_node_text(parent_class_name_node, source_code_bytes)
                    # Don't break, keep looking for enclosing function within the class
                current_node = current_node.parent

            # Only record if caller is from current file's defined functions
            if parent_func and parent_func in functions_in_file:
                 calls.append({
                    "caller": parent_func,
                    "callee": called_function,
                    "caller_file": file_path,
                    "callee_file": None # This would need more sophisticated resolution
                })
    return calls


if __name__ == "__main__":
    auradb_connector = None
    try:
        auradb_connector = AuraDBCodeGraph(URI, USERNAME, PASSWORD)

        print("\n--- Populating AuraDB Knowledge Graph ---")
        all_parsed_chunks = []
        project_root = "./dummy_project"

        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith(".py") and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as f:
                        source_code_bytes = f.read()

                    # 1. Add File Node
                    auradb_connector.run_query("MERGE (f:File {path: $file_path}) RETURN f", {"file_path": file_path})

                    # 2. Extract and Store Chunks in ChromaDB and get their IDs
                    # (This part is conceptually integrated for data flow,
                    # but index_codebase_to_chromadb handles the actual ChromaDB calls)
                    chunks = extract_python_chunks(file_path)
                    
                    documents_to_add_to_chroma = []
                    metadatas_to_add_to_chroma = []
                    ids_to_add_to_chroma = []

                    for chunk in chunks:
                        chunk_id = str(uuid.uuid4())
                        chunk["metadata"]["chroma_id"] = chunk_id # Attach Chroma ID to chunk metadata
                        all_parsed_chunks.append(chunk) # Collect all chunks for later processing

                        documents_to_add_to_chroma.append(chunk["content"])
                        metadatas_to_add_to_chroma.append(chunk["metadata"])
                        ids_to_add_to_chroma.append(chunk_id)

                        # 3. Create Function/Class Nodes in Neo4j based on chunk type
                        if chunk['metadata']['chunk_type'] in ["function_definition", "function_definition_with_docstring"]:
                            auradb_connector.create_function_node(
                                chunk['metadata']['function_name'],
                                chunk['metadata']['file_path'],
                                chunk['metadata']['start_line'],
                                chunk['metadata']['end_line'],
                                chunk['metadata']['chroma_id'],
                                chunk['metadata'].get('class_name') # Pass class_name if exists
                            )
                        elif chunk['metadata']['chunk_type'] in ["class_definition", "class_definition_with_docstring"]:
                            auradb_connector.create_class_node(
                                chunk['metadata']['class_name'],
                                chunk['metadata']['file_path'],
                                chunk['metadata']['chroma_id']
                            )
                    
                    if documents_to_add_to_chroma:
                         # Generate embeddings for the chunks to be added to Chroma
                        chunk_embeddings = [generate_embedding(doc) for doc in documents_to_add_to_chroma]
                        code_collection.add(
                            embeddings=chunk_embeddings,
                            documents=documents_to_add_to_chroma,
                            metadatas=metadatas_to_add_to_chroma,
                            ids=ids_to_add_to_chroma
                        )
                        print(f"Added {len(documents_to_add_to_chroma)} chunks to ChromaDB from {file_path}")
                    
                    # 4. Extract and Store Relationships (simplified for demo)
                    # Function calls:
                    # This is highly simplified. A robust solution needs to:
                    # a) Resolve full path of called functions (e.g., from imports)
                    # b) Differentiate method calls from global function calls
                    # c) Handle dynamic calls.
                    # This example only captures calls within the same file and assumes direct resolution.
                    
                    # A more robust approach might be to use a separate static analysis tool or
                    # build a more sophisticated AST traversal logic.
                    function_calls = extract_function_calls(source_code_bytes, file_path)
                    print('Debugging 3')
                    for call in function_calls:
                        # For cross-file calls, `callee_file` would need to be resolved.
                        # For this example, we assume callee_file is the same if not explicitly set.
                        print('Debugging 4')
                        callee_file = call['callee_file'] if call['callee_file'] else call['caller_file']
                        print('Debugging 5')
                        print(f"  Attempting to create CALLS relationship: {call['caller']} in {call['caller_file']} calls {call['callee']} in {callee_file}")
                        auradb_connector.create_calls_relationship(
                            call['caller'], call['caller_file'],
                            call['callee'], callee_file
                        )

                    # Class defines relationships:
                    for chunk in chunks:
                        if chunk['metadata']['chunk_type'] in ["function_definition", "function_definition_with_docstring"]:
                            if 'class_name' in chunk['metadata'] and chunk['metadata']['class_name']:
                                auradb_connector.create_defines_relationship(
                                    chunk['metadata']['class_name'],
                                    chunk['metadata']['file_path'],
                                    chunk['metadata']['function_name']
                                )
                    print('Debugging 1')
                print('Debugging 2')
            
        
        print("\n--- Verifying Graph Data in AuraDB ---")
        # Example Query: Find all functions called by 'main_app'
        results = auradb_connector.run_query("""
            MATCH (f1:Function {name: 'main_app'})-[:CALLS]->(f2:Function)
            RETURN f1.name AS caller, f2.name AS callee, f2.file_path AS callee_file
        """)
        for record in results:
            print(f"'{record['caller']}' calls '{record['callee']}' in '{record['callee_file']}'")

        # Example Query: Find all functions defined in Calculator class
        # results = auradb_connector.run_query("""
        #     MATCH (c:Class {name: 'Calculator'})-[:DEFINES]->(f:Function)
        #     RETURN c.name AS class, f.name AS function, f.file_path AS file
        # """)
        # for record in results:
        #     print(f"Class '{record['class']}' defines function '{record['function']}' in '{record['file']}'")

    except Exception as e:
        print(f"Error during AuraDB operations: {e}")
    finally:
        if auradb_connector:
            auradb_connector.close()