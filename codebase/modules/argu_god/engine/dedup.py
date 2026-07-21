from .vector_store import embed
import numpy as np

SIMILARITY_THRESHOLD = 0.85


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def is_similar_to_any(candidate_text, existing_texts, threshold=SIMILARITY_THRESHOLD):
    if not existing_texts:
        return False
    candidate_emb = embed(candidate_text)
    for text in existing_texts:
        sim = cosine_similarity(candidate_emb, embed(text))
        if sim >= threshold:
            return True
    return False
