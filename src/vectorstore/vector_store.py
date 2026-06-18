"""
Vector Store for Enterprise AI Knowledge Assistant.
Stores and retrieves document chunks using ChromaDB.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from src.utils.logger import get_vectorstore_logger

logger = get_vectorstore_logger()


class VectorStore:
    """
    Manages document storage and retrieval using ChromaDB.

    How it works:
        1. Takes text chunks + their embeddings
        2. Stores them in ChromaDB locally
        3. When user asks question:
           - Converts question to embedding
           - Finds most similar chunks
           - Returns them as context for LLM

    Think of it like a smart search engine
    that understands MEANING not just keywords!
    """

    def __init__(self,
                 persist_directory: str = "data/vectorstore",
                 collection_name: str = "knowledge_base"):
        """
        Args:
            persist_directory: Where to save ChromaDB data
            collection_name:   Name of the collection
        """
        self.persist_directory = str(persist_directory)
        self.collection_name   = collection_name
        self.client            = None
        self.collection        = None
        self._initialize()

    def _initialize(self):
        """Set up ChromaDB client and collection."""
        try:
            # ── Create ChromaDB client ───────────────────────────
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )

            # ── Get or create collection ─────────────────────────
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            count = self.collection.count()
            logger.info(
                f"✅ VectorStore ready — "
                f"collection: {self.collection_name} "
                f"({count} chunks stored)"
            )

        except Exception as e:
            logger.error(f"VectorStore init failed: {str(e)}")
            raise

    def add_documents(self,
                      chunks: List[Dict[str, Any]],
                      embeddings: List[List[float]]) -> int:
        """
        Store document chunks with their embeddings.

        Args:
            chunks:     List of chunk dicts (content + metadata)
            embeddings: List of embedding vectors

        Returns:
            Number of chunks stored
        """
        if not chunks or not embeddings:
            logger.warning("No chunks or embeddings to store")
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and "
                f"embeddings ({len(embeddings)}) must match!"
            )

        # ── Prepare data for ChromaDB ────────────────────────────
        ids        = []
        documents  = []
        metadatas  = []
        current_count = self.collection.count()

        for i, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            chunk_id = f"chunk_{current_count + i}"
            ids.append(chunk_id)
            documents.append(chunk["content"])

            # ChromaDB metadata must be strings/ints/floats only
            clean_metadata = {}
            for k, v in chunk.get("metadata", {}).items():
                if isinstance(v, (str, int, float, bool)):
                    clean_metadata[k] = v
                else:
                    clean_metadata[k] = str(v)

            metadatas.append(clean_metadata)

        # ── Store in batches of 100 ──────────────────────────────
        batch_size = 100
        stored = 0

        for i in range(0, len(ids), batch_size):
            batch_ids   = ids[i:i + batch_size]
            batch_docs  = documents[i:i + batch_size]
            batch_meta  = metadatas[i:i + batch_size]
            batch_embed = embeddings[i:i + batch_size]

            self.collection.add(
                ids        = batch_ids,
                documents  = batch_docs,
                metadatas  = batch_meta,
                embeddings = batch_embed
            )
            stored += len(batch_ids)
            logger.info(f"Stored {stored}/{len(ids)} chunks")

        logger.info(f"✅ Total stored: {stored} chunks")
        return stored

    def search(self,
               query_embedding: List[float],
               top_k: int = 5,
               filter_source: Optional[str] = None
               ) -> List[Dict[str, Any]]:
        """
        Find most relevant chunks for a query.

        Args:
            query_embedding: Embedding of the question
            top_k:           How many results to return
            filter_source:   Optional filter by source file

        Returns:
            List of relevant chunks with scores
        """
        try:
            # ── Build filter if needed ───────────────────────────
            where = None
            if filter_source:
                where = {"source": filter_source}

            # ── Query ChromaDB ───────────────────────────────────
            results = self.collection.query(
                query_embeddings = [query_embedding],
                n_results        = min(top_k,
                                      self.collection.count()),
                where            = where,
                include          = ["documents",
                                    "metadatas",
                                    "distances"]
            )

            # ── Format results ───────────────────────────────────
            formatted = []
            documents  = results.get("documents", [[]])[0]
            metadatas  = results.get("metadatas",  [[]])[0]
            distances  = results.get("distances",  [[]])[0]

            for doc, meta, dist in zip(
                documents, metadatas, distances
            ):
                # Convert distance to similarity score
                similarity = round(1 - dist, 4)
                formatted.append({
                    "content":    doc,
                    "metadata":   meta,
                    "similarity": similarity,
                })

            logger.info(
                f"Found {len(formatted)} relevant chunks"
            )
            return formatted

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored documents."""
        try:
            count = self.collection.count()
            return {
                "total_chunks":    count,
                "collection_name": self.collection_name,
                "storage_path":    self.persist_directory,
            }
        except Exception:
            return {"total_chunks": 0}

    def clear(self) -> bool:
        """
        Delete all stored documents.
        Used when user wants to start fresh.
        """
        try:
            self.client.delete_collection(
                self.collection_name
            )
            self.collection = \
                self.client.get_or_create_collection(
                    name     = self.collection_name,
                    metadata = {"hnsw:space": "cosine"}
                )
            logger.info("✅ VectorStore cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Clear failed: {str(e)}")
            return False

    def is_empty(self) -> bool:
        """Check if no documents are stored yet."""
        return self.collection.count() == 0