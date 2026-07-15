import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
import uuid 
from pprint import pprint
from tree_sitter import Language, Parser
# import tree_sitter_languages
import tree_sitter_python as tspython

# Load the Python language grammar
# PY_LANGUAGE = Language(tree_sitter_languages.get_language('python'))
PY_LANGUAGE = Language(tspython.language())
# parser = Parser()
parser = Parser(PY_LANGUAGE)
# parser.set_language(PY_LANGUAGE)

def get_node_text(node, source_code_bytes):
    """Extracts the text of a tree-sitter node."""
    return source_code_bytes[node.start_byte:node.end_byte].decode('utf8')

def extract_python_chunks(file_path):
    """
    Parses a Python file and extracts semantic chunks (functions, classes, docstrings).
    Returns a list of dictionaries, each representing a chunk.
    """
    with open(file_path, 'rb') as f: # Read as bytes for tree-sitter
        source_code_bytes = f.read()

    tree = parser.parse(source_code_bytes)
    root_node = tree.root_node

    chunks = []
    # Use a set to keep track of processed nodes to avoid overlaps
    processed_nodes_text = set()

    # Traverse the AST to find functions, classes, and top-level statements/comments
    cursor = root_node.walk()

    # Define a simple stack for context (e.g., class_name for functions)
    context_stack = []

    def traverse_and_extract(node):
        current_context = {"file_path": file_path}
        if context_stack:
            current_context.update(context_stack[-1])

        # Prioritize larger, structural chunks
        if node.type == 'class_definition':
            class_name_node = node.child_by_field_name('name')
            class_name = get_node_text(class_name_node, source_code_bytes) if class_name_node else "AnonymousClass"
            
            # Extract class docstring if present (common pattern)
            class_body = node.child_by_field_name('body')
            if class_body and class_body.children:
                first_statement = class_body.children[0]
                if first_statement.type == 'expression_statement' and \
                   first_statement.children and \
                   first_statement.children[0].type == 'string':
                    docstring = get_node_text(first_statement.children[0], source_code_bytes)
                    chunk_text = f"Class {class_name}:\n{docstring}\n{get_node_text(node, source_code_bytes)}"
                    if chunk_text not in processed_nodes_text:
                        chunks.append({
                            "content": chunk_text,
                            "metadata": {
                                "file_path": file_path,
                                "start_line": node.start_point[0] + 1,
                                "end_line": node.end_point[0] + 1,
                                "chunk_type": "class_definition_with_docstring",
                                "class_name": class_name,
                                "language": "python"
                            }
                        })
                        processed_nodes_text.add(chunk_text)

            # Add the full class definition as a chunk
            full_class_text = get_node_text(node, source_code_bytes)
            if full_class_text not in processed_nodes_text:
                chunks.append({
                    "content": full_class_text,
                    "metadata": {
                        "file_path": file_path,
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "chunk_type": "class_definition",
                        "class_name": class_name,
                        "language": "python"
                    }
                })
                processed_nodes_text.add(full_class_text)

            context_stack.append({"class_name": class_name})
            for child in node.children:
                traverse_and_extract(child)
            context_stack.pop()

        elif node.type == 'function_definition':
            function_name_node = node.child_by_field_name('name')
            function_name = get_node_text(function_name_node, source_code_bytes) if function_name_node else "AnonymousFunction"

            # Extract function docstring if present
            function_body = node.child_by_field_name('body')
            if function_body and function_body.children:
                first_statement = function_body.children[0]
                if first_statement.type == 'expression_statement' and \
                   first_statement.children and \
                   first_statement.children[0].type == 'string':
                    docstring = get_node_text(first_statement.children[0], source_code_bytes)
                    chunk_text = f"Function {function_name}:\n{docstring}\n{get_node_text(node, source_code_bytes)}"
                    if chunk_text not in processed_nodes_text:
                        chunks.append({
                            "content": chunk_text,
                            "metadata": {
                                "file_path": file_path,
                                "start_line": node.start_point[0] + 1,
                                "end_line": node.end_point[0] + 1,
                                "chunk_type": "function_definition_with_docstring",
                                "function_name": function_name,
                                **current_context,
                                "language": "python"
                            }
                        })
                        processed_nodes_text.add(chunk_text)

            # Add the full function definition as a chunk
            full_function_text = get_node_text(node, source_code_bytes)
            if full_function_text not in processed_nodes_text:
                chunks.append({
                    "content": full_function_text,
                    "metadata": {
                        "file_path": file_path,
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "chunk_type": "function_definition",
                        "function_name": function_name,
                        **current_context,
                        "language": "python"
                    }
                })
                processed_nodes_text.add(full_function_text)
            
            # Continue traversal within function body
            for child in node.children:
                traverse_and_extract(child)

        # Handle top-level comments or significant statements not part of functions/classes
        elif node.type == 'expression_statement' and node.children and node.children[0].type == 'string' and node.parent == root_node:
             # This handles module-level docstrings
            docstring_text = get_node_text(node, source_code_bytes)
            if docstring_text not in processed_nodes_text:
                chunks.append({
                    "content": docstring_text,
                    "metadata": {
                        "file_path": file_path,
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "chunk_type": "module_docstring",
                        "language": "python"
                    }
                })
                processed_nodes_text.add(docstring_text)
        
        # Consider a fallback for smaller, less structured chunks (e.g., statements)
        # This can be basic character splitting for remaining code blocks if semantic chunking is too sparse.
        # For simplicity, we'll focus on functions/classes initially.
        # For anything not explicitly processed, you might add it as a 'general_code_block'
        # with a simpler text splitter or capture remaining top-level expressions.
        
        # General traversal for nodes not explicitly handled above, to ensure we find nested elements
        if node.type not in ['function_definition', 'class_definition']:
             for child in node.children:
                traverse_and_extract(child)

    traverse_and_extract(root_node)
    return chunks

# 'nomic-ai/nomic-embed-text-v1.5' is good for code, or 'BAAI/bge-small-en-v1.5'
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' 
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def generate_embedding(text):
    """Generates an embedding for the given text."""
    # Sentence Transformers can handle batching automatically for lists of texts
    return embedding_model.encode(text, convert_to_numpy=True).tolist()

CHROMA_DB_PATH = "./chroma_data"
os.makedirs(CHROMA_DB_PATH, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
code_collection = chroma_client.get_or_create_collection(name="my_project_code_embeddings")

def index_codebase_to_chromadb(project_root_dir):
    """
    Parses all Python files in a project, generates embeddings,
    and stores them in ChromaDB.
    """
    print(f"\n--- Indexing codebase in {project_root_dir} to ChromaDB ---")
    indexed_count = 0
    for root, _, files in os.walk(project_root_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith('.'):
                file_path = os.path.join(root, file)
                print(f"Indexing {file_path}...")
                chunks = extract_python_chunks(file_path)

                documents_to_add = []
                metadatas_to_add = []
                ids_to_add = []

                for chunk in chunks:
                    chunk_id = str(uuid.uuid4()) # Generate a unique ID for each chunk
                    embedding = generate_embedding(chunk["content"])

                    documents_to_add.append(chunk["content"])
                    metadatas_to_add.append(chunk["metadata"])
                    ids_to_add.append(chunk_id)
                    
                    # Store the chunk_id back in metadata for potential KG linkage
                    chunk["metadata"]["chroma_id"] = chunk_id
                    
                    # You could also store embedding directly in chunk dict for KG
                    chunk["embedding"] = embedding 

                if documents_to_add:
                    code_collection.add(
                        embeddings=[generate_embedding(doc) for doc in documents_to_add], # Embed on the fly for add
                        documents=documents_to_add,
                        metadatas=metadatas_to_add,
                        ids=ids_to_add
                    )
                    indexed_count += len(documents_to_add)
    
    print(f"\nFinished indexing. Total documents in ChromaDB: {code_collection.count()}")
    return code_collection # Return the collection for direct use

if __name__ == "__main__":

    print("--- Testing Code Parser & Chunking ---")
    all_chunks = []
    # Find all Python files in a dummy project directory
    project_root = "./dummy_project"
    for root, _, files in os.walk(project_root):
        for file in files:
            if file.endswith(".py") and not file.startswith('.'): # Exclude hidden files
                file_path = os.path.join(root, file)
                print(f"\nProcessing {file_path}...")
                chunks = extract_python_chunks(file_path)
                for i, chunk in enumerate(chunks):
                    # print(f"Chunk {i+1} ({chunk['metadata']['chunk_type']}):")
                    # print(f"  Lines: {chunk['metadata']['start_line']}-{chunk['metadata']['end_line']}")
                    # print(f"  Content:\n{chunk['content'][:200]}...") # Print first 200 chars
                    all_chunks.append(chunk)
    
    print(f"\nTotal chunks extracted: {len(all_chunks)}")

    print("\n--- Querying ChromaDB ---")
    # Ensure the dummy project exists from Step 1
    # You might want to run this only once or implement incremental updates

    # index_codebase_to_chromadb("./dummy_project")

    # Example ChromaDB Query    
    query_results = code_collection.query(
        query_texts=["How to add numbers in the calculator class?"],
        # n_results=2,
        # You can add where_clause for filtering, e.g.,
        # where={"language": "python", "file_path": "dummy_project/src/math_utils.py"}
    )
    pprint(query_results['ids'])
    # print(f"Collection '{code_collection.name}' contains {code_collection.count()} documents.")

    # Example for embedding a chunk
    print("\n--- Testing Embedding Generation ---")
    sample_chunk_content = "def calculate_area(radius): return math.pi * radius**2"
    embedding = generate_embedding(sample_chunk_content)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values of embedding: {embedding[:5]}...")