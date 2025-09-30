#!/usr/bin/env python3
"""
Setup vedas_knowledge_base collection in Qdrant
"""

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

def create_vedas_collection():
    """Create the vedas_knowledge_base collection in Qdrant."""
    
    try:
        # Connect to Qdrant
        client = QdrantClient("localhost", port=6333)
        
        # Check if collection exists
        collections = client.get_collections()
        collection_exists = any(col.name == "vedas_knowledge_base" for col in collections.collections)
        
        if collection_exists:
            print("✅ Collection vedas_knowledge_base already exists")
            return True
        
        # Create collection
        client.create_collection(
            collection_name="vedas_knowledge_base",
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
        
        print("✅ Successfully created vedas_knowledge_base collection")
        return True
        
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return False

def check_collection():
    """Check if the collection exists."""
    try:
        client = QdrantClient("localhost", port=6333)
        collections = client.get_collections()
        
        for collection in collections.collections:
            if collection.name == "vedas_knowledge_base":
                # Get detailed collection info
                collection_info = client.get_collection("vedas_knowledge_base")
                print(f"✅ Collection vedas_knowledge_base exists with {collection_info.points_count} points")
                return True
        
        print("❌ Collection vedas_knowledge_base not found")
        return False
        
    except Exception as e:
        print(f"❌ Error checking collections: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Setting up vedas_knowledge_base collection...")
    
    # Check if collection already exists
    if check_collection():
        print("Collection already exists!")
    else:
        # Create collection
        if create_vedas_collection():
            print("Collection created successfully!")
            # Verify creation
            check_collection()
        else:
            print("Failed to create collection!")
