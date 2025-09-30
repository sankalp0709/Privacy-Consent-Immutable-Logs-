#!/usr/bin/env python3
"""
NAS-based Knowledge Retriever for BHIV using Qdrant
Retrieves embeddings and documents from company NAS server via Qdrant vector database
"""

import os
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

try:
    # Prefer package import when example is a package
    from example.nas_config import NASConfig
except Exception:
    # Fallback to local import when run from within example/
    from nas_config import NASConfig

logger = logging.getLogger(__name__)

class NASKnowledgeRetriever:
    """Retrieve knowledge from company NAS server via Qdrant vector database."""

    def __init__(self, domain: str = "vedas", qdrant_url: str = "localhost:6333"):
        self.domain = domain
        self.config = NASConfig()
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.qdrant_client = QdrantClient(qdrant_url, prefer_grpc=False)
        self.collection_name = f"{domain}_knowledge_base"

        # Initialize paths for fallback
        self.documents_path = self.config.get_documents_path(domain)
        self.metadata_path = self.config.get_metadata_path(domain)

        # Fallback data
        self.documents = []
        self.metadata = {}

        # Check Qdrant connection and load fallback data
        self.qdrant_available = self._check_qdrant_connection()
        if not self.qdrant_available:
            self._load_fallback_data()
    
    def _check_qdrant_connection(self) -> bool:
        """Check if Qdrant is accessible and collection exists."""
        try:
            # Check if Qdrant server is accessible
            collections = self.qdrant_client.get_collections()

            # Check if our collection exists
            collection_exists = any(col.name == self.collection_name for col in collections.collections)

            if collection_exists:
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                logger.info(f"✅ Connected to Qdrant collection: {self.collection_name}")
                logger.info(f"📊 Collection has {collection_info.points_count} points")
                return True
            else:
                logger.warning(f"⚠️ Qdrant collection not found: {self.collection_name}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            return False

    def _load_fallback_data(self):
        """Load fallback data from NAS files when Qdrant is unavailable."""
        try:
            if not self.config.is_nas_accessible():
                logger.warning("⚠️ NAS server is not accessible, trying local cache")
                self._load_local_cache()
                return

            # Load metadata
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"✅ Loaded fallback metadata from {self.metadata_path}")
            else:
                logger.warning(f"❌ Metadata not found at {self.metadata_path}")

            # Load documents
            if os.path.exists(self.documents_path):
                for file_path in Path(self.documents_path).glob("*.txt"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.documents.append({
                            "filename": file_path.name,
                            "content": content,
                            "path": str(file_path)
                        })
                logger.info(f"✅ Loaded {len(self.documents)} fallback documents from {self.documents_path}")
            else:
                logger.warning(f"❌ Documents path not found at {self.documents_path}")

        except Exception as e:
            logger.error(f"❌ Failed to load fallback data: {e}")
            self._load_local_cache()
    
    def _load_local_cache(self):
        """Load from local cache if NAS and Qdrant are unavailable."""
        cache_dir = Path("cache/nas_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Try to load cached Qdrant backup
            cache_collection_file = cache_dir / f"{self.domain}_qdrant_backup.json"
            cache_metadata = cache_dir / f"{self.domain}_metadata.json"

            if cache_collection_file.exists():
                with open(cache_collection_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)

                # Extract documents from cached points
                for point_data in backup_data.get("points", []):
                    payload = point_data.get("payload", {})
                    if "content" in payload:
                        self.documents.append({
                            "filename": payload.get("filename", "Unknown"),
                            "content": payload.get("content", ""),
                            "path": payload.get("source_path", "")
                        })

                logger.info(f"📦 Using cached Qdrant backup from {cache_collection_file}")
                logger.info(f"📦 Loaded {len(self.documents)} documents from cache")

            if cache_metadata.exists():
                with open(cache_metadata, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"📦 Using cached metadata from {cache_metadata}")

        except Exception as e:
            logger.error(f"❌ Failed to load cache: {e}")
    
    def query(self, query_text: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Query the NAS knowledge base via Qdrant."""
        try:
            if self.qdrant_available:
                return self._query_qdrant(query_text, top_k, filters)
            else:
                return self._fallback_search(query_text, top_k, filters)

        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return self._fallback_search(query_text, top_k, filters)

    def _query_qdrant(self, query_text: str, top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Query Qdrant vector database."""
        try:
            # Encode query
            query_embedding = self.encoder.encode(query_text)

            # Prepare Qdrant filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            # Search in Qdrant using query_points (newer API)
            search_results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                query_filter=qdrant_filter,
                limit=top_k
            )

            results = []
            # query_points returns QueryResponse with points attribute
            points = search_results.points if hasattr(search_results, 'points') else search_results
            
            for i, result in enumerate(points):
                payload = result.payload
                content = payload.get("content", "")

                result_dict = {
                    "content": content[:500] + "..." if len(content) > 500 else content,
                    "filename": payload.get("filename", "Unknown"),
                    "score": float(result.score),
                    "rank": i + 1,
                    "source": "qdrant_nas",
                    "domain": self.domain,
                    "doc_index": payload.get("doc_index", i),
                    "length": payload.get("length", len(content))
                }

                # Add any additional payload data
                for key, value in payload.items():
                    if key not in result_dict:
                        result_dict[key] = value

                results.append(result_dict)

            logger.info(f"🔍 Found {len(results)} results from Qdrant for query: '{query_text[:50]}...'")
            return results

        except Exception as e:
            logger.error(f"❌ Qdrant query failed: {e}")
            raise
    
    def _fallback_search(self, query_text: str, top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fallback to simple text search if Qdrant is unavailable."""
        logger.info("🔄 Using fallback text search")

        results = []
        query_lower = query_text.lower()
        query_words = query_lower.split()

        for i, doc in enumerate(self.documents):
            content_lower = doc["content"].lower()

            # Simple relevance scoring based on keyword matches
            score = 0
            for word in query_words:
                score += content_lower.count(word)

            if score > 0:
                result = {
                    "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                    "filename": doc["filename"],
                    "score": score,
                    "rank": len(results) + 1,
                    "source": "fallback_search",
                    "domain": self.domain,
                    "doc_index": i,
                    "length": len(doc["content"])
                }

                # Apply filters if provided
                if filters and not self._matches_filters(result, filters):
                    continue

                results.append(result)

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"🔍 Found {len(results)} results from fallback search")
        return results[:top_k]
    
    def _matches_filters(self, result: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if result matches provided filters."""
        for key, value in filters.items():
            if key in result and result[key] != value:
                return False
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        qdrant_stats = {}
        if self.qdrant_available:
            try:
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                qdrant_stats = {
                    "qdrant_points_count": collection_info.points_count,
                    "qdrant_collection_name": self.collection_name
                }
            except Exception as e:
                qdrant_stats = {"qdrant_error": str(e)}

        return {
            "domain": self.domain,
            "nas_accessible": self.config.is_nas_accessible(),
            "qdrant_available": self.qdrant_available,
            "documents_count": len(self.documents),
            "metadata_entries": len(self.metadata),
            "documents_path": self.documents_path,
            **qdrant_stats
        }

# Example usage
if __name__ == "__main__":
    # Test the NAS retriever
    retriever = NASKnowledgeRetriever("vedas")
    
    print("📊 Retriever Stats:")
    stats = retriever.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test query
    results = retriever.query("What is dharma?", top_k=3)
    print(f"\n🔍 Query Results ({len(results)} found):")
    for result in results:
        print(f"  📄 {result['filename']} (score: {result['score']:.3f})")
        print(f"     {result['content'][:100]}...")
