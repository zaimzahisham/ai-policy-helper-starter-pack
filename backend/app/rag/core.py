"""RAG engine core: orchestration, metrics, and retrieval."""
import logging
import time
import os
from typing import List, Dict, Tuple
from .embedders import LocalEmbedder
from .stores import InMemoryStore, QdrantStore
from .llms import StubLLM, OpenAILLM, OllamaLLM
from ..settings import settings
from ..ingest.utils import doc_hash

logger = logging.getLogger(__name__)


class Metrics:
    """Tracks retrieval and generation latencies."""
    
    def __init__(self):
        self.t_retrieval = []
        self.t_generation = []

    def add_retrieval(self, ms: float):
        """Record retrieval latency in milliseconds."""
        self.t_retrieval.append(ms)

    def add_generation(self, ms: float):
        """Record generation latency in milliseconds."""
        self.t_generation.append(ms)

    def summary(self) -> Dict:
        """Compute average latencies."""
        avg_r = sum(self.t_retrieval)/len(self.t_retrieval) if self.t_retrieval else 0.0
        avg_g = sum(self.t_generation)/len(self.t_generation) if self.t_generation else 0.0
        return {
            "avg_retrieval_latency_ms": round(avg_r, 2),
            "avg_generation_latency_ms": round(avg_g, 2),
        }


class RAGEngine:
    """
    Main RAG orchestrator.
    
    Handles document ingestion (embedding + storage), retrieval (with MMR reranking),
    and generation (LLM-based answer creation).
    """
    
    def __init__(self):
        self.embedder = LocalEmbedder(dim=384)

        # Load internal agent guide (if present) to be used as system instructions for LLMs.
        guide_path = os.path.join(settings.data_dir, "Internal_SOP_Agent_Guide.md")
        try:
            with open(guide_path, "r", encoding="utf-8") as f:
                self.agent_guide = f.read()
            logger.info(f"Loaded agent guide from {guide_path} ({len(self.agent_guide)} chars)")
        except FileNotFoundError:
            self.agent_guide = ""
            logger.debug(f"Agent guide not found at {guide_path}, using empty guide")

        # Define base system prompt (shared across all LLMs for consistency)
        self.system_prompt_base = "You are a helpful company policy assistant. Cite sources by title and section when relevant."

        # Define required output format (shared across all LLMs for consistency)
        self.required_output_format = (
            "You MUST respond in the following format:\n\n"
            "Answer:\n"
            "<2-4 sentence direct answer for the user>\n\n"
            "Sources:\n"
            "- <Document_Title.md> — <Section>\n"
            "- <Document_Title.md> — <Section>\n\n"
            "Details:\n"
            "<Any additional explanation or important policy notes>"
        )
        
        # Vector store selection
        self._fallback_used = False
        if settings.vector_store == "qdrant":
            try:
                self.store = QdrantStore(collection=settings.collection_name, dim=384)
                logger.info(f"Using Qdrant vector store (collection: {settings.collection_name})")
            except Exception as e:
                logger.warning(f"Qdrant initialization failed, falling back to InMemoryStore: {str(e)}")
                self.store = InMemoryStore(dim=384)
                self._fallback_used = True
        else:
            self.store = InMemoryStore(dim=384)
            logger.info("Using InMemoryStore vector store")

        # LLM selection
        if settings.llm_provider == "openai" and settings.openai_api_key:
            try:
                self.llm = OpenAILLM(
                    api_key=settings.openai_api_key,
                    system_prompt_base=self.system_prompt_base,
                    agent_guide=self.agent_guide,
                    required_output_format=self.required_output_format
                )
                self.llm_name = "openai:gpt-4o-mini"
                logger.info("Using OpenAI LLM provider (gpt-4o-mini)")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed, falling back to StubLLM: {str(e)}")
                self.llm = StubLLM(
                    agent_guide=self.agent_guide,
                    required_output_format=self.required_output_format
                )
                self.llm_name = "stub"
        elif settings.llm_provider == "ollama":
            try:
                self.llm = OllamaLLM(
                    host=settings.ollama_host,
                    model=settings.ollama_model,
                    system_prompt_base=self.system_prompt_base,
                    agent_guide=self.agent_guide,
                    required_output_format=self.required_output_format
                )
                self.llm_name = f"ollama:{settings.ollama_model}"
                logger.info(f"Using Ollama LLM provider ({settings.ollama_model})")
            except Exception as e:
                logger.warning(f"Ollama initialization failed, falling back to StubLLM: {str(e)}")
                self.llm = StubLLM(
                    agent_guide=self.agent_guide,
                    required_output_format=self.required_output_format
                )
                self.llm_name = "stub"
        else:
            self.llm = StubLLM(
                agent_guide=self.agent_guide,
                required_output_format=self.required_output_format
            )
            self.llm_name = "stub"
            logger.info("Using StubLLM provider (deterministic, offline)")

        self.metrics = Metrics()
        self._doc_titles = set()
        self._chunk_hashes = set()
        self._chunk_count = 0
        self._ask_count = 0

    def _mmr_rerank(self, candidates: List[Tuple[float, Dict]], k: int, lambda_param: float = 0.7) -> List[Dict]:
        """
        Maximal Marginal Relevance reranking with metadata-based boosting.
        
        lambda_param: 1.0 = pure relevance, 0.0 = pure diversity
        
        Metadata boosting:
        - Heading level: H1=1.2x, H2=1.15x, H3=1.1x
        - Section priority: high=1.15x, medium=1.05x, low=1.0x
        
        Args:
            candidates: List of (score, metadata) tuples from vector search
            k: Number of results to return
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
        
        Returns:
            List of reranked metadata dictionaries
        """
        if not candidates or k >= len(candidates):
            return [meta for _, meta in candidates[:k]]
        
        selected = []
        remaining = list(candidates)
        
        # Start with highest-scoring result (with metadata boost applied)
        best_score, best_meta = remaining.pop(0)
        selected.append(best_meta)
        
        while len(selected) < k and remaining:
            best_mmr = -float('inf')
            best_idx = 0
            
            for idx, (score, meta) in enumerate(remaining):
                # Apply metadata-based boosting to similarity score
                boosted_score = score
                
                # Boost by heading level (H1/H2/H3 are more important)
                heading_level = meta.get("heading_level", 0)
                if heading_level == 1:
                    boosted_score *= 1.2  # H1: 20% boost
                elif heading_level == 2:
                    boosted_score *= 1.15  # H2: 15% boost
                elif heading_level == 3:
                    boosted_score *= 1.1  # H3: 10% boost
                
                # Boost by section priority (SLA, Policy, Terms are critical)
                section_priority = meta.get("section_priority", "low")
                if section_priority == "high":
                    boosted_score *= 1.15  # High priority: 15% boost
                elif section_priority == "medium":
                    boosted_score *= 1.05  # Medium priority: 5% boost
                
                # Compute max similarity to already-selected chunks
                max_sim = 0.0
                for sel in selected:
                    # Simple diversity: penalize same title+section
                    if sel.get("title") == meta.get("title") and sel.get("section") == meta.get("section"):
                        max_sim = 1.0  # same chunk
                    # else: different chunks are always diverse, even from same doc
                
                # MMR score: lambda * (boosted relevance) - (1-lambda) * diversity_penalty
                mmr_score = lambda_param * boosted_score - (1 - lambda_param) * max_sim
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = idx
            
            selected.append(remaining.pop(best_idx)[1])
        
        return selected

    def ingest_chunks(self, chunks: List[Dict]) -> Tuple[int, int]:
        """
        Store chunks in vector database (embed + upsert).
        
        Deduplicates chunks based on hash. Only new chunks are embedded and stored.
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
        
        Returns:
            Tuple of (new_docs_count, new_chunks_count)
        """
        try:
            logger.debug(f"Starting ingestion of {len(chunks)} chunks")
            vectors = []
            metas = []
            doc_titles_before = set(self._doc_titles)

            for ch in chunks:
                text = ch["text"]
                h = doc_hash(text)
                if h in self._chunk_hashes:
                    continue
                self._chunk_hashes.add(h)
                meta = {
                    "id": h,
                    "hash": h,
                    "title": ch["title"],
                    "section": ch.get("section"),
                    "text": text,
                    "heading_level": ch.get("heading_level", 0),
                    "section_priority": ch.get("section_priority", "low"),
                }
                v = self.embedder.embed(text)
                vectors.append(v)
                metas.append(meta)
                self._doc_titles.add(ch["title"])
                self._chunk_count += 1

            if vectors:
                logger.debug(f"Upserting {len(vectors)} new vectors to store")
                self.store.upsert(vectors, metas)
            else:
                logger.debug("No new vectors to upsert (all chunks already indexed)")
            
            new_docs = len(self._doc_titles) - len(doc_titles_before)
            new_chunks = len(metas)
            logger.info(f"Ingestion complete: {new_docs} new docs, {new_chunks} new chunks")
            return (new_docs, new_chunks)
        except Exception as e:
            logger.error(f"Error during chunk ingestion: {str(e)}", exc_info=True)
            raise

    def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        """
        Retrieve and rerank relevant chunks for a query.
        
        Args:
            query: User question
            k: Number of chunks to return
        
        Returns:
            List of reranked chunk metadata dictionaries
        """
        try:
            t0 = time.time()
            logger.debug(f"Retrieving chunks for query (k={k})")
            qv = self.embedder.embed(query)
            candidates = self.store.search(qv, k=k * 2)
            logger.debug(f"Found {len(candidates)} candidate chunks from vector search")
            reranked_results = self._mmr_rerank(candidates, k, lambda_param=0.7)
            elapsed_ms = (time.time()-t0)*1000.0
            self.metrics.add_retrieval(elapsed_ms)
            logger.debug(f"Retrieval complete: {len(reranked_results)} chunks after reranking ({elapsed_ms:.2f}ms)")
            return reranked_results
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}", exc_info=True)
            raise

    def generate(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate answer from query and retrieved contexts.
        
        Args:
            query: User question
            contexts: Retrieved chunk metadata
        
        Returns:
            Generated answer string
        """
        try:
            t0 = time.time()
            logger.debug(f"Generating answer with {len(contexts)} context chunks (LLM: {self.llm_name})")
            answer = self.llm.generate(query, contexts)
            elapsed_ms = (time.time()-t0)*1000.0
            self.metrics.add_generation(elapsed_ms)
            self._ask_count += 1
            logger.debug(f"Generation complete: {len(answer)} chars ({elapsed_ms:.2f}ms)")
            return answer
        except Exception as e:
            logger.error(f"Error during generation: {str(e)}", exc_info=True)
            self._ask_count += 1  # Still increment even on error for metrics accuracy
            raise

    def stats(self) -> Dict:
        """
        Get engine statistics.
        
        Returns:
            Dictionary with counts, latencies, and configuration
        """
        m = self.metrics.summary()
        return {
            "total_docs": len(self._doc_titles),
            "total_chunks": self._chunk_count,
            "ask_count": self._ask_count,
            "fallback_used": self._fallback_used,
            "embedding_model": settings.embedding_model,
            "llm_model": self.llm_name,
            **m
        }

