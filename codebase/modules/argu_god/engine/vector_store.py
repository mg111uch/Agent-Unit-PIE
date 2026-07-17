import chromadb

_client = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.Client(
            settings=chromadb.config.Settings(
                persist_directory="./chroma_db"
            )
        )
    return _client


def _get_collection():
    global _collection
    if _collection is None:
        _collection = _get_client().get_or_create_collection(name="arguments")
    return _collection


def embed(text):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(text).tolist()


def index_graph(graph):
    collection = _get_collection()
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
    collection = _get_collection()
    results = collection.query(
        query_embeddings=[embed(query)],
        n_results=top_k
    )
    return results
