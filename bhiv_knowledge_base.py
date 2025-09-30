#!/usr/bin/env python3
"""
BHIV Knowledge Base System with NAS Integration
Combines document management on NAS with vector search capabilities
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from dataclasses import dataclass

# Import our NAS manager
from knowledge_base_manager import NASKnowledgeBaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any]
    chunk_index: int

class BHIVKnowledgeBase:
    """Main BHIV Knowledge Base System"""
    
    def __init__(self, nas_path: str, use_qdrant: bool = True):
        """
        Initialize the BHIV Knowledge Base
        
        Args:
            nas_path: Path to the NAS share
            use_qdrant: Whether to use Qdrant for vector search
        """
        self.nas_manager = NASKnowledgeBaseManager(nas_path)
        self.use_qdrant = use_qdrant
        self.qdrant_client = None
        
        # Initialize Qdrant if requested
        if use_qdrant:
            self._init_qdrant()
        
        # Create local cache directory
        self.cache_dir = Path("knowledge_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def _init_qdrant(self):
        """Initialize Qdrant client"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self.qdrant_client = QdrantClient("localhost", port=6333)
            
            # Test connection
            collections = self.qdrant_client.get_collections()
            logger.info("✅ Qdrant connection successful")
            
            # Create collection if it doesn't exist
            collection_name = "bhiv_knowledge_base"
            try:
                self.qdrant_client.get_collection(collection_name)
                logger.info(f"✅ Collection '{collection_name}' already exists")
            except:
                # Create collection with 384-dimensional vectors (sentence-transformers default)
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"✅ Created collection '{collection_name}'")
                
            self.collection_name = collection_name
            
        except ImportError:
            logger.warning("Qdrant client not installed. Vector search disabled.")
            self.use_qdrant = False
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}. Vector search disabled.")
            self.use_qdrant = False
    
    def test_system(self) -> Dict[str, bool]:
        """Test all system components"""
        results = {}
        
        # Test NAS connection
        results["nas_connection"] = self.nas_manager.test_connection()
        
        # Test Qdrant connection
        if self.use_qdrant and self.qdrant_client:
            try:
                self.qdrant_client.get_collections()
                results["qdrant_connection"] = True
            except:
                results["qdrant_connection"] = False
        else:
            results["qdrant_connection"] = False
        
        return results
    
    def add_document(self, file_path: str, document_id: Optional[str] = None) -> str:
        """
        Add a document to the knowledge base
        
        Args:
            file_path: Path to the document file
            document_id: Optional custom document ID
            
        Returns:
            Document ID of the added document
        """
        # Upload to NAS
        doc_id = self.nas_manager.upload_document(file_path, document_id)
        
        # Process for vector search if enabled
        if self.use_qdrant:
            self._process_document_for_search(doc_id, file_path)
        
        logger.info(f"✅ Document added to knowledge base: {doc_id}")
        return doc_id
    
    def _process_document_for_search(self, document_id: str, file_path: str):
        """Process document for vector search"""
        try:
            # Read document content
            content = self._extract_text(file_path)
            
            # Split into chunks
            chunks = self._split_into_chunks(content, document_id)
            
            # Generate embeddings and store in Qdrant
            self._store_chunks_in_qdrant(chunks)
            
            logger.info(f"✅ Document processed for search: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to process document for search: {e}")
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from various file formats"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.txt':
            return file_path.read_text(encoding='utf-8', errors='ignore')
        elif file_path.suffix.lower() == '.json':
            data = json.loads(file_path.read_text(encoding='utf-8'))
            return json.dumps(data, indent=2)
        else:
            # For other formats, try to read as text
            try:
                return file_path.read_text(encoding='utf-8', errors='ignore')
            except:
                return f"[Binary file: {file_path.name}]"
    
    def _split_into_chunks(self, content: str, document_id: str, chunk_size: int = 500) -> List[DocumentChunk]:
        """Split content into chunks for vector search"""
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_content = ' '.join(chunk_words)
            
            chunk_id = hashlib.md5(f"{document_id}_{i}".encode()).hexdigest()
            
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk_content,
                metadata={
                    "chunk_index": i // chunk_size,
                    "word_count": len(chunk_words),
                    "created_at": datetime.now().isoformat()
                },
                chunk_index=i // chunk_size
            )
            chunks.append(chunk)
        
        return chunks
    
    def _store_chunks_in_qdrant(self, chunks: List[DocumentChunk]):
        """Store document chunks in Qdrant"""
        if not self.use_qdrant or not self.qdrant_client:
            return
        
        try:
            # Generate embeddings (placeholder - would use sentence-transformers)
            points = []
            for chunk in chunks:
                # For now, create dummy embeddings
                # In production, use: model.encode(chunk.content)
                embedding = [0.1] * 384  # Placeholder embedding
                
                points.append({
                    "id": chunk.chunk_id,
                    "vector": embedding,
                    "payload": {
                        "document_id": chunk.document_id,
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "metadata": chunk.metadata
                    }
                })
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ Stored {len(chunks)} chunks in Qdrant")
            
        except Exception as e:
            logger.error(f"Failed to store chunks in Qdrant: {e}")
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search the knowledge base
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        if self.use_qdrant and self.qdrant_client:
            return self._vector_search(query, limit)
        else:
            return self._text_search(query, limit)
    
    def _vector_search(self, query: str, limit: int) -> List[Dict]:
        """Perform vector search using Qdrant"""
        try:
            # Generate query embedding (placeholder)
            query_embedding = [0.1] * 384  # Placeholder
            
            # Search in Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.payload["content"],
                    "document_id": result.payload["document_id"],
                    "score": result.score,
                    "metadata": result.payload.get("metadata", {})
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return self._text_search(query, limit)
    
    def _text_search(self, query: str, limit: int) -> List[Dict]:
        """Fallback text search"""
        # Simple text search in document metadata
        documents = self.nas_manager.list_documents()
        results = []
        
        query_lower = query.lower()
        for doc in documents:
            if query_lower in doc.get("original_filename", "").lower():
                results.append({
                    "content": f"Document: {doc['original_filename']}",
                    "document_id": doc["document_id"],
                    "score": 0.5,
                    "metadata": doc
                })
        
        return results[:limit]
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """Get the full content of a document"""
        doc_path = self.nas_manager.get_document_path(document_id)
        if doc_path and doc_path.exists():
            return self._extract_text(str(doc_path))
        return None
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the knowledge base"""
        return self.nas_manager.list_documents()
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the knowledge base"""
        # Delete from NAS
        success = self.nas_manager.delete_document(document_id)
        
        # Delete from Qdrant if enabled
        if success and self.use_qdrant and self.qdrant_client:
            try:
                # Delete all chunks for this document
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector={"filter": {"document_id": document_id}}
                )
                logger.info(f"✅ Deleted document from Qdrant: {document_id}")
            except Exception as e:
                logger.error(f"Failed to delete from Qdrant: {e}")
        
        return success
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        nas_stats = self.nas_manager.get_stats()
        
        stats = {
            **nas_stats,
            "vector_search_enabled": self.use_qdrant,
            "qdrant_connected": self.qdrant_client is not None
        }
        
        if self.use_qdrant and self.qdrant_client:
            try:
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                stats["vector_count"] = collection_info.vectors_count
            except:
                stats["vector_count"] = 0
        
        return stats

def main():
    """Test the BHIV Knowledge Base System"""
    
    # Load configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    nas_path = os.getenv("NAS_PATH", r"\\192.168.0.94\Guruukul_DB")
    
    # Initialize knowledge base
    kb = BHIVKnowledgeBase(nas_path, use_qdrant=True)
    
    # Test system
    test_results = kb.test_system()
    print("\n🧪 System Test Results:")
    for component, status in test_results.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {component}: {'OK' if status else 'FAILED'}")
    
    # Show stats
    stats = kb.get_stats()
    print("\n📊 Knowledge Base Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # List documents
    documents = kb.list_documents()
    print(f"\n📚 Documents ({len(documents)}):")
    for doc in documents:
        print(f"  - {doc['document_id']}: {doc['original_filename']}")

if __name__ == "__main__":
    main()
