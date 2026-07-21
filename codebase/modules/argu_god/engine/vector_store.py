import chromadb
from functools import lru_cache

_client = None
_collection = None
_indexed_topics = set()


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


@lru_cache(maxsize=1)
def _get_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        import hashlib
        import numpy as np

        class _FallbackEmbedder:
            def encode(self, text, **_kwargs):
                seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                rng = np.random.RandomState(seed)
                return rng.randn(384).astype(np.float32)

        return _FallbackEmbedder()


def embed(text):
    return _get_model().encode(text).tolist()


def index_graph(graph):
    collection = _get_collection()
    for node in graph.get("nodes", []):
        text = f"{node.get('name')} {node.get('premise')}"
        try:
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
        except Exception:
            pass


def search_similar(argument, top_k=3):
    query = f"{argument.get('name')} {argument.get('premise')}"
    collection = _get_collection()
    results = collection.query(
        query_embeddings=[embed(query)],
        n_results=top_k
    )
    return results
