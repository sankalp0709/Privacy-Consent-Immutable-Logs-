#!/usr/bin/env python3
"""
Populate vedas_knowledge_base collection with embeddings from sample documents
"""

import os
import uuid
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

def populate_vedas_collection():
    """Populate the vedas_knowledge_base collection with embeddings from sample documents."""
    
    try:
        # Initialize encoder
        encoder = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Initialized embedding model")
        
        # Connect to Qdrant
        client = QdrantClient("localhost", port=6333)
        print("✅ Connected to Qdrant")
        
        # Check if collection exists
        collections = client.get_collections()
        collection_exists = any(col.name == "vedas_knowledge_base" for col in collections.collections)
        
        if not collection_exists:
            print("❌ Collection vedas_knowledge_base not found. Please run setup_vedas_collection.py first.")
            return False
        
        # Process sample documents
        sample_docs_path = Path("sample_documents")
        documents = []
        
        for txt_file in sample_docs_path.glob("*.txt"):
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    documents.append({
                        "content": content,
                        "filename": txt_file.name,
                        "domain": "vedas"
                    })
                    print(f"📄 Loaded: {txt_file.name}")
        
        if not documents:
            print("❌ No documents found to process")
            return False
        
        print(f"📚 Processing {len(documents)} documents...")
        
        # Create embeddings
        texts = [doc["content"] for doc in documents]
        embeddings = encoder.encode(texts)
        print(f"🧠 Created embeddings for {len(texts)} documents")
        
        # Prepare points for Qdrant
        points = []
        for i, (embedding, doc) in enumerate(zip(embeddings, documents)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={
                    "content": doc["content"],
                    "filename": doc["filename"],
                    "domain": doc["domain"],
                    "source_path": str(sample_docs_path / doc["filename"]),
                    "length": len(doc["content"]),
                    "doc_index": i
                }
            )
            points.append(point)
        
        # Upload to Qdrant
        print(f"📤 Uploading {len(points)} points to Qdrant...")
        client.upsert(
            collection_name="vedas_knowledge_base",
            points=points
        )
        
        print("✅ Successfully populated vedas_knowledge_base collection!")
        
        # Verify upload
        collection_info = client.get_collection("vedas_knowledge_base")
        print(f"📊 Collection now has {collection_info.points_count} points")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating collection: {e}")
        return False

def test_search():
    """Test search functionality in the populated collection."""
    try:
        # Initialize encoder
        encoder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Connect to Qdrant
        client = QdrantClient("localhost", port=6333)
        
        # Test query
        test_query = "What is dharma?"
        query_embedding = encoder.encode(test_query)
        
        print(f"🔍 Testing search with: '{test_query}'")
        
        # Search in Qdrant using query_points (newer API)
        search_results = client.query_points(
            collection_name="vedas_knowledge_base",
            query_vector=query_embedding.tolist(),
            limit=3
        )
        
        print(f"📊 Found {len(search_results)} results:")
        for i, result in enumerate(search_results):
            filename = result.payload.get('filename', 'Unknown')
            score = result.score
            content_preview = result.payload.get('content', '')[:100] + "..."
            print(f"  {i+1}. {filename} (score: {score:.3f})")
            print(f"     {content_preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Populating vedas_knowledge_base collection...")
    
    if populate_vedas_collection():
        print("\n🧪 Testing search functionality...")
        test_search()
    else:
        print("Failed to populate collection!")
