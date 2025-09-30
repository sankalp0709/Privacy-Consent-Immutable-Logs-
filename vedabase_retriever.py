from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from utils.logger import get_logger
from typing import Dict, Any, List, Optional
import re

logger = get_logger(__name__)

class VedabaseRetriever:
    def __init__(self, qdrant_url="localhost:6333", collection_name="vedas_knowledge_base"):
        self.client = QdrantClient(qdrant_url, prefer_grpc=False)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection_name = collection_name

        # Vedic book mappings for enhanced filtering
        self.vedic_books = {
            "rigveda": ["rigveda", "rig_veda", "rig"],
            "samaveda": ["samaveda", "sama_veda", "sama"],
            "yajurveda": ["yajurveda", "yajur_veda", "yajur"],
            "atharvaveda": ["atharvaveda", "atharva_veda", "atharva"],
            "bhagavad_gita": ["bhagavad", "gita", "bhagavad_gita"],
            "upanishads": ["upanishad", "upanishads"],
            "puranas": ["purana", "puranas"],
            "ramayana": ["ramayana"],
            "mahabharata": ["mahabharata"]
        }

    def parse_advanced_filters(self, query: str) -> tuple[str, Dict[str, Any]]:
        """Parse advanced filter syntax like @type:artha, @book:rigveda from query."""
        filters = {}
        clean_query = query

        # Extract @key:value patterns
        filter_pattern = r'@(\w+):(\w+)'
        matches = re.findall(filter_pattern, query)

        for key, value in matches:
            if key == "book":
                # Map book aliases to canonical names
                canonical_book = self._get_canonical_book_name(value.lower())
                if canonical_book:
                    filters["book"] = canonical_book
            elif key == "type":
                filters["type"] = value.lower()
            elif key == "version":
                filters["version"] = value
            else:
                filters[key] = value

            # Remove filter from query
            clean_query = re.sub(f'@{key}:{value}', '', clean_query).strip()

        return clean_query, filters

    def _get_canonical_book_name(self, book_alias: str) -> Optional[str]:
        """Get canonical book name from alias."""
        for canonical, aliases in self.vedic_books.items():
            if book_alias in aliases:
                return canonical
        return book_alias if book_alias else None

    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Optional[models.Filter]:
        """Build Qdrant filter from filter dictionary."""
        if not filters:
            return None

        conditions = []

        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
            elif isinstance(value, list):
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchAny(any=value)
                    )
                )

        if conditions:
            return models.Filter(must=conditions)
        return None

    def get_relevant_docs(self, query: str, filters: dict = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from Qdrant with enhanced filtering."""
        try:
            # Parse advanced filters from query
            clean_query, parsed_filters = self.parse_advanced_filters(query)

            # Merge with provided filters
            if filters:
                parsed_filters.update(filters)

            # Generate query vector
            query_vector = self.model.encode(clean_query).tolist()

            # Build Qdrant filter
            qdrant_filter = self._build_qdrant_filter(parsed_filters)

            # Search Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            # Format results with metadata
            results = []
            for hit in search_result:
                result = {
                    "text": hit.payload.get("text", ""),
                    "score": float(hit.score),
                    "source": hit.payload.get("source", "unknown"),
                    "book": hit.payload.get("book", "unknown"),
                    "type": hit.payload.get("type", "unknown"),
                    "version": hit.payload.get("version", "v1"),
                    "chunk_id": hit.payload.get("chunk_id", 0),
                    "metadata": {
                        "file_name": hit.payload.get("file_name", ""),
                        "total_chunks": hit.payload.get("total_chunks", 1),
                        "loaded_at": hit.payload.get("loaded_at", "")
                    }
                }
                results.append(result)

            logger.info(f"Retrieved {len(results)} documents for query: '{clean_query}' with filters: {parsed_filters}")
            return results

        except Exception as e:
            logger.error(f"Failed to retrieve documents: {str(e)}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics and metadata."""
        try:
            collection_info = self.client.get_collection(self.collection_name)

            # Get sample of documents to analyze metadata
            sample_docs = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_payload=True
            )[0]

            # Analyze available books and types
            books = set()
            types = set()
            sources = set()

            for doc in sample_docs:
                payload = doc.payload
                if "book" in payload:
                    books.add(payload["book"])
                if "type" in payload:
                    types.add(payload["type"])
                if "source" in payload:
                    sources.add(payload["source"])

            return {
                "collection_name": self.collection_name,
                "total_points": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors[""].size,
                "distance_metric": collection_info.config.params.vectors[""].distance.name,
                "available_books": sorted(list(books)),
                "available_types": sorted(list(types)),
                "total_sources": len(sources),
                "sample_sources": sorted(list(sources))[:10]
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"error": str(e)}

    def test_connection(self) -> bool:
        """Test Qdrant connection and collection availability."""
        try:
            collections = self.client.get_collections()
            collection_exists = any(
                col.name == self.collection_name
                for col in collections.collections
            )

            if collection_exists:
                # Test a simple query
                test_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=[0.0] * 384,  # Zero vector for testing
                    limit=1
                )
                logger.info(f"Qdrant connection test successful. Collection has {len(test_result)} points available.")
                return True
            else:
                logger.warning(f"Collection '{self.collection_name}' does not exist")
                return False

        except Exception as e:
            logger.error(f"Qdrant connection test failed: {str(e)}")
            return False