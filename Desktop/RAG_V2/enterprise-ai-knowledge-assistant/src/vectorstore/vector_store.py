"""
ChromaDB Vector Store for Enterprise AI Knowledge Assistant.

Phase 1 Upgrade:
- Added get_all_documents() for BM25 index building
- Added search() method with proper return format
- Added clear() method
- Better metadata handling
"""

import os
from typing import List, Dict, Any, Optional
from src.utils.logger import setup_logger

logger = setup_logger("VectorStore")


class VectorStore:
    """
    ChromaDB-backed vector store for document chunks.

    Stores embeddings + metadata, supports semantic search
    and full document retrieval for BM25 index building.
    """

    def __init__(self,
                 persist_directory: str = "data/vectorstore",
                 collection_name: str = "knowledge_base"):
        """
        Args:
            persist_directory: Where ChromaDB stores data on disk
            collection_name:   Name of the ChromaDB collection
        """
        import chromadb

        self.persist_directory = persist_directory
        self.collection_name   = collection_name

        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(
            f"VectorStore ready — collection: {collection_name} "
            f"({self.collection.count()} chunks stored)"
        )

    def add_documents(self,
                      chunks: List[Dict[str, Any]],
                      embeddings: List[List[float]]):
        """
        Add document chunks and their embeddings to ChromaDB.

        Args:
            chunks:     List of chunk dicts with text and metadata
            embeddings: Corresponding embedding vectors
        """
        if not chunks or not embeddings:
            return

        ids        = []
        documents  = []
        metadatas  = []
        embeds     = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            text     = chunk.get("text", chunk.get("content", ""))
            metadata = chunk.get("metadata", {})

            # Flatten metadata — ChromaDB only accepts str/int/float/bool
            flat_meta = {}
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    flat_meta[k] = v
                else:
                    flat_meta[k] = str(v)

            chunk_id = (
                f"{flat_meta.get('source', 'doc')}_"
                f"{flat_meta.get('page_number', 0)}_"
                f"{flat_meta.get('chunk_index', i)}_"
                f"{i}"
            )

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append(flat_meta)
            embeds.append(embedding)

        self.collection.add(
            ids        = ids,
            documents  = documents,
            metadatas  = metadatas,
            embeddings = embeds
        )

        logger.info(f"Added {len(chunks)} chunks to vector store")

    def search(self,
               query_embedding: List[float],
               top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            query_embedding: Query vector
            top_k:           Number of results to return

        Returns:
            List of dicts: {content, metadata, similarity, id}
        """
        count = self.collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)

        results = self.collection.query(
            query_embeddings = [query_embedding],
            n_results        = actual_k,
            include          = ["documents", "metadatas", "distances"]
        )

        output = []
        docs      = results.get("documents", [[]])[0]
        metas     = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids       = results.get("ids", [[]])[0]

        for doc, meta, dist, id_ in zip(docs, metas, distances, ids):
            # Convert distance to similarity (ChromaDB cosine = 1 - cosine_sim)
            similarity = 1.0 - dist

            output.append({
                "content":    doc,
                "metadata":   meta,
                "similarity": round(similarity, 4),
                "id":         id_,
            })

        return output

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieve ALL documents from the vector store.
        Used by BM25 index builder.

        Returns:
            List of dicts: {content, metadata, id}
        """
        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.get(
            include=["documents", "metadatas"]
        )

        output = []
        docs   = results.get("documents", [])
        metas  = results.get("metadatas", [])
        ids    = results.get("ids", [])

        for doc, meta, id_ in zip(docs, metas, ids):
            output.append({
                "content":  doc,
                "metadata": meta,
                "id":       id_,
            })

        return output

    def count(self) -> int:
        """Return total number of chunks stored."""
        return self.collection.count()

    def clear(self):
        """Delete and recreate the collection."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name     = self.collection_name,
            metadata = {"hnsw:space": "cosine"}
        )
        logger.info("Vector store cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Return stats about the vector store."""
        return {
            "total_chunks":    self.collection.count(),
            "collection_name": self.collection_name,
            "persist_dir":     self.persist_directory,
        }