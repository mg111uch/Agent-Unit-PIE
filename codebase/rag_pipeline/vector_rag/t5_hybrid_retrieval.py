# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
# from langchain.chains import RetrievalQA
# from langchain.prompts import PromptTemplate
# from langchain_community.llms import Ollama # For local LLM
from t4_neo4j import AuraDBCodeGraph,URI,USERNAME,PASSWORD
from t2_embedding import EMBEDDING_MODEL_NAME
from python.rag_pipeline.ChunkEmbedChroma import chroma_client


# Initialize Embedding Model for LangChain/LlamaIndex
# This needs to be the SAME model as used for indexing
embedding_function = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
# '''
# Initialize ChromaDB as a LangChain VectorStore
chroma_vectorstore = Chroma(
    client=chroma_client,
    collection_name="my_project_code_embeddings",
    embedding_function=embedding_function
)

# Initialize AuraDB Connector (from previous code)
# Make sure URI, USERNAME, PASSWORD are loaded from .env
auradb_connector = AuraDBCodeGraph(URI, USERNAME, PASSWORD)

def hybrid_code_retriever(query: str, top_k_vector=5, top_k_graph=3):
    """
    Performs a hybrid retrieval:
    1. Vector search in ChromaDB.
    2. Uses extracted entities/functions from vector search to traverse the knowledge graph.
    """
    print(f"\n--- Hybrid Retrieval for query: '{query}' ---")
    retrieved_vector_docs = []
    retrieved_graph_context = []
    
    # 1. Vector Search
    vector_results = chroma_vectorstore.similarity_search_with_score(query, k=top_k_vector)
    
    potential_function_names = set()
    potential_class_names = set()
    potential_file_paths = set()

    print(f"Vector Search found {len(vector_results)} results:")
    for doc, score in vector_results:
        print(f"  Score: {score:.4f}, Type: {doc.metadata.get('chunk_type')}, File: {doc.metadata.get('file_path')}, Content: {doc.page_content[:100]}...")
        retrieved_vector_docs.append(doc.page_content) # Add raw content to list

        # Extract entities for graph traversal
        if 'function_name' in doc.metadata and doc.metadata['function_name']:
            potential_function_names.add(doc.metadata['function_name'])
        if 'class_name' in doc.metadata and doc.metadata['class_name']:
            potential_class_names.add(doc.metadata['class_name'])
        if 'file_path' in doc.metadata and doc.metadata['file_path']:
            potential_file_paths.add(doc.metadata['file_path'])

    # 2. Knowledge Graph Traversal (based on vector search results)
    print("\n--- Augmenting with Knowledge Graph ---")
    
    # Example: Find functions called by functions found in vector search
    for func_name in potential_function_names:
        cypher_query = f"""
        MATCH (f:Function {{name: '{func_name}'}})-[r:CALLS|DEFINES]->(related_node)
        RETURN f.name AS source_name, type(r) AS relationship_type, related_node.name AS target_name, related_node.file_path AS target_file
        LIMIT {top_k_graph}
        """
        graph_results = auradb_connector.run_query(cypher_query)
        if graph_results:
            print(f"  Graph relationships for '{func_name}':")
            for record in graph_results:
                graph_context = (
                    f"Relationship: {record['source_name']} {record['relationship_type']} {record['target_name']}"
                    f" (File: {record.get('target_file', 'N/A')})"
                )
                print(f"    - {graph_context}")
                retrieved_graph_context.append(graph_context)

    # Example: Find functions within classes found in vector search
    for cls_name in potential_class_names:
        cypher_query = f"""
        MATCH (c:Class {{name: '{cls_name}'}})-[:DEFINES]->(f:Function)
        RETURN c.name AS class_name, f.name AS function_name, f.file_path AS file_path
        LIMIT {top_k_graph}
        """
        graph_results = auradb_connector.run_query(cypher_query)
        if graph_results:
            print(f"  Functions defined in class '{cls_name}':")
            for record in graph_results:
                graph_context = (
                    f"Class {record['class_name']} defines function {record['function_name']}"
                    f" (File: {record.get('file_path', 'N/A')})"
                )
                print(f"    - {graph_context}")
                retrieved_graph_context.append(graph_context)
    
    # Combine all retrieved context
    full_context = "\n\n".join(retrieved_vector_docs + retrieved_graph_context)
    return full_context

if __name__ == "__main__":
    # Ensure AuraDB is initialized before calling hybrid_code_retriever
    # (This is handled by the `auradb_connector` global instance)
    
    # Test the hybrid retriever
    retrieved_context = hybrid_code_retriever("How does user authentication work?")
    print("\n--- Combined Context for LLM ---")
    print(retrieved_context)
# '''