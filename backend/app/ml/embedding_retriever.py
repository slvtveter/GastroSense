"""Dense (semantic) retriever for the RAG pipeline.

Uses Gemini embeddings instead of a local sentence-transformers model on
purpose: the live demo runs on Render's free tier (512 MB RAM), where pulling
in torch + a local model would OOM the container. The embedding API reuses the
GEMINI_API_KEY the app already has and is multilingual, which is the whole point
here - the TF-IDF retriever scores Russian queries against the English data
chunks at ~0.0 (no shared character n-grams), so it's effectively blind to the
app's primary audience. Dense embeddings match on meaning, across languages.

Everything is wrapped so that a missing key, exhausted quota, or offline run
degrades gracefully to TF-IDF-only retrieval rather than breaking the chat.
"""
from __future__ import annotations

import os
from typing import List, Optional

import numpy as np

from app.logger import logger

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime
    genai = None

# Tried in order. gemini-embedding-001 is the stable model; the -2 line is a
# newer fallback in case 001 is throttled or retired (mirrors the failover
# pattern already used for text generation in agent_manager.py).
EMBEDDING_MODEL_CANDIDATES = [
    "models/gemini-embedding-001",
    "models/gemini-embedding-2",
]


class EmbeddingRetriever:
    def __init__(self) -> None:
        self.available = False
        self._doc_matrix: Optional[np.ndarray] = None  # (n_chunks, dim), L2-normalized
        api_key = os.getenv("GEMINI_API_KEY")
        if genai and api_key:
            api_key = api_key.strip('"').strip("'")
            genai.configure(api_key=api_key)
            self.available = True
        else:
            logger.info("EmbeddingRetriever disabled (no Gemini key) - falling back to TF-IDF only.")

    def _embed(self, content, task_type: str) -> Optional[np.ndarray]:
        """Embed a string or list of strings. Returns an L2-normalized matrix
        of shape (n, dim), or None if every model in the chain failed."""
        if not self.available:
            return None
        for model in EMBEDDING_MODEL_CANDIDATES:
            try:
                result = genai.embed_content(model=model, content=content, task_type=task_type)
                raw = result["embedding"]
                # embed_content returns a flat vector for a single string and a
                # list of vectors for a list - normalize both to a 2D array.
                vectors = np.array(raw, dtype=np.float32)
                if vectors.ndim == 1:
                    vectors = vectors[None, :]
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                return vectors / norms
            except Exception as exc:  # quota, rate limit, bad model id, network
                logger.warning("Embedding model %s failed (%s), trying next.", model, exc)
                continue
        logger.warning("All embedding models failed - dense retrieval unavailable for this rebuild.")
        return None

    def build(self, texts: List[str]) -> None:
        """Embed and cache the corpus. Called on every index rebuild."""
        if not self.available or not texts:
            self._doc_matrix = None
            return
        self._doc_matrix = self._embed(texts, task_type="retrieval_document")
        if self._doc_matrix is not None:
            logger.info("Dense index built: %s chunk embeddings (dim=%s).",
                        self._doc_matrix.shape[0], self._doc_matrix.shape[1])

    def search_scores(self, query: str) -> Optional[np.ndarray]:
        """Return a cosine-similarity score per chunk (aligned with build order),
        or None if dense retrieval isn't usable right now."""
        if self._doc_matrix is None:
            return None
        query_matrix = self._embed(query, task_type="retrieval_query")
        if query_matrix is None:
            return None
        # Both sides are L2-normalized, so the dot product IS cosine similarity.
        return (self._doc_matrix @ query_matrix[0]).astype(np.float32)


embedding_retriever = EmbeddingRetriever()
