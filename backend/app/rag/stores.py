"""Vector store implementations."""
import logging
from typing import List, Dict, Tuple
import numpy as np
from qdrant_client import QdrantClient, models as qm
import uuid
from ..shared.helpers import convert_to_uuid

logger = logging.getLogger(__name__)


class InMemoryStore:
    """
    In-memory vector store using cosine similarity.
    
    Fallback when Qdrant is unavailable. Stores vectors and metadata in lists.
    """
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.vecs: List[np.ndarray] = []
        self.meta: List[Dict] = []
        self._hashes = set()

    def upsert(self, vectors: List[np.ndarray], metadatas: List[Dict]):
        """
        Insert or update vectors with metadata.
        
        Skips vectors that already exist (based on hash in metadata).
        
        Args:
            vectors: List of embedding vectors
            metadatas: List of metadata dictionaries (must include "hash" key)
        """
        for v, m in zip(vectors, metadatas):
            h = m.get("hash")
            if h and h in self._hashes:
                continue
            self.vecs.append(v.astype("float32"))
            self.meta.append(m)
            if h:
                self._hashes.add(h)

    def search(self, query: np.ndarray, k: int = 4) -> List[Tuple[float, Dict]]:
        """
        Search for k most similar vectors using cosine similarity.
        
        Args:
            query: Query vector
            k: Number of results to return
        
        Returns:
            List of (score, metadata) tuples, sorted by similarity (descending)
        """
        if not self.vecs:
            return []
        A = np.vstack(self.vecs)  # [N, d]
        q = query.reshape(1, -1)  # [1, d]
        # cosine similarity
        sims = (A @ q.T).ravel() / (np.linalg.norm(A, axis=1) * (np.linalg.norm(q) + 1e-9) + 1e-9)
        idx = np.argsort(-sims)[:k]
        return [(float(sims[i]), self.meta[i]) for i in idx]


class QdrantStore:
    """
    Qdrant vector store implementation.
    
    Primary vector store for production use. Falls back to InMemoryStore
    if Qdrant is unavailable.
    """
    
    def __init__(self, collection: str, dim: int = 384):
        self.client = QdrantClient(url="http://qdrant:6333", timeout=10.0)
        self.collection = collection
        self.dim = dim
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self.client.get_collection(self.collection)
            logger.debug(f"Qdrant collection '{self.collection}' already exists")
        except Exception as e:
            logger.info(f"Creating Qdrant collection '{self.collection}' (dim={self.dim})")
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE)
            )
            logger.info(f"Qdrant collection '{self.collection}' created successfully")

    def upsert(self, vectors: List[np.ndarray], metadatas: List[Dict]):
        """
        Insert or update vectors in Qdrant.
        
        Converts chunk hashes to UUIDs for point IDs (Qdrant requirement).
        
        Args:
            vectors: List of embedding vectors
            metadatas: List of metadata dictionaries (must include "hash" key)
        """
        try:
            logger.debug(f"Upserting {len(vectors)} points to Qdrant collection '{self.collection}'")
            points = []
            for i, (v, m) in enumerate(zip(vectors, metadatas)):
                # Convert hash to UUID format (Qdrant requires UUID point IDs)
                point_id = convert_to_uuid(m["hash"]) if m.get("hash") else str(uuid.uuid4())
                points.append(qm.PointStruct(id=point_id, vector=v.tolist(), payload=m))
            self.client.upsert(collection_name=self.collection, points=points)
            logger.debug(f"Successfully upserted {len(points)} points to Qdrant")
        except Exception as e:
            logger.error(f"Error upserting to Qdrant: {str(e)}", exc_info=True)
            raise

    def search(self, query: np.ndarray, k: int = 4) -> List[Tuple[float, Dict]]:
        """
        Search Qdrant for k most similar vectors.
        
        Args:
            query: Query vector
            k: Number of results to return
        
        Returns:
            List of (score, metadata) tuples, sorted by similarity (descending)
        """
        try:
            logger.debug(f"Searching Qdrant collection '{self.collection}' for k={k}")
            res = self.client.search(
                collection_name=self.collection,
                query_vector=query.tolist(),
                limit=k,
                with_payload=True
            )
            out = []
            for r in res:
                out.append((float(r.score), dict(r.payload)))
            logger.debug(f"Qdrant search returned {len(out)} results")
            return out
        except Exception as e:
            logger.error(f"Error searching Qdrant: {str(e)}", exc_info=True)
            raise

