import chromadb

client = chromadb.Client(
    settings=chromadb.config.Settings(
        persist_directory="./chroma_db"
    )
)

collection = client.get_or_create_collection(name="arguments")

def embed(text):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(text).tolist()

def index_graph(graph):
    for node in graph.get("nodes", []):
        text = f"{node.get('name')} {node.get('premise')}"

        collection.add(
            documents=[text],
            embeddings=[embed(text)],
            metadatas=[{
                "name": node.get("name"),
                "side": node.get("side"),
                "premise": node.get("premise")
            }],
            ids=[node.get("name")]
        )

def search_similar(argument, top_k=3):
    query = f"{argument.get('name')} {argument.get('premise')}"

    results = collection.query(
        query_embeddings=[embed(query)],
        n_results=top_k
    )

    return results

client.persist()