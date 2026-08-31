import chromadb
from functools import lru_cache

_client = None
_collection = None
_indexed_topics = set()


def _get_client():
    global _client
    if _client is None:
        try:
            from pathlib import Path
            persist = Path(__file__).resolve().parents[4] / "data" / "chroma_db"
            persist.mkdir(parents=True, exist_ok=True)
            _client = chromadb.PersistentClient(path=str(persist))
        except Exception:
            _client = chromadb.Client(
                settings=chromadb.config.Settings(
                    persist_directory=str(Path(__file__).resolve().parents[4] / "data" / "chroma_db")
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
    from pathlib import Path
    cache_path = Path(__file__).resolve().parents[2] / "encoding_cache" / "all-MiniLM-L6-v2"
    try:
        from sentence_transformers import SentenceTransformer
        if cache_path.exists():
            return SentenceTransformer(str(cache_path), local_files_only=True)
        return SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception:
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


def sync_from_sqlite():
    """Rebuild Chroma from SQLite embeddings if collection empty (cold start)."""
    try:
        from kernel.persistence.db import kernel_db
        coll = _get_collection()
        if coll.count() > 0:
            return 0
        rows = kernel_db.load_all_embeddings()
        if not rows:
            return 0
        import struct
        for node_id, blob in rows:
            try:
                vals = list(struct.unpack(f"{len(blob)//4}f", blob))
                coll.add(ids=[node_id], embeddings=[vals], documents=[node_id], metadatas=[{"node_id": node_id}])
            except Exception:
                continue
        return len(rows)
    except Exception:
        return 0
