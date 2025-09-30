#!/usr/bin/env python3
"""
Setup NAS Embeddings for BHIV Knowledge Base with Qdrant
This script helps setup and configure embeddings on your company NAS using Qdrant vector database
"""

import os
import sys
import json
import shutil
import uuid
from pathlib import Path
from typing import List, Dict, Any
import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from nas_config import NASConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NASEmbeddingsSetup:
    """Setup embeddings on company NAS server with Qdrant."""

    def __init__(self, qdrant_url: str = "localhost:6333"):
        self.config = NASConfig()
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.qdrant_client = QdrantClient(qdrant_url, prefer_grpc=False)
        self.qdrant_url = qdrant_url
        
    def check_nas_connection(self) -> bool:
        """Check if NAS is accessible."""
        logger.info("🔍 Checking NAS connection...")
        
        if self.config.is_nas_accessible():
            logger.info("✅ NAS is accessible")
            return True
        else:
            logger.error("❌ NAS is not accessible")
            logger.info("💡 Make sure:")
            logger.info("  1. NAS server is running")
            logger.info("  2. Network connection is stable")
            logger.info("  3. Credentials are correct")
            logger.info("  4. Share is mounted (run setup_company_nas.py)")
            return False
    
    def create_nas_directory_structure(self):
        """Create required directory structure on NAS."""
        logger.info("📁 Creating NAS directory structure...")
        
        try:
            base_paths = [
                self.config.current_config["embeddings_path"],
                self.config.current_config["documents_path"], 
                self.config.current_config["metadata_path"]
            ]
            
            for path in base_paths:
                os.makedirs(path, exist_ok=True)
                logger.info(f"✅ Created: {path}")
                
            # Create domain-specific subdirectories
            domains = ["vedas", "education", "wellness", "general"]
            for domain in domains:
                domain_docs = os.path.join(self.config.current_config["documents_path"], f"{domain}_texts")
                os.makedirs(domain_docs, exist_ok=True)
                logger.info(f"✅ Created domain directory: {domain_docs}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            return False
        
        return True
    
    def process_local_documents(self, local_docs_path: str, domain: str = "vedas") -> bool:
        """Process local documents and create embeddings in Qdrant."""
        logger.info(f"📚 Processing documents from {local_docs_path} for domain: {domain}")

        if not os.path.exists(local_docs_path):
            logger.error(f"❌ Local documents path not found: {local_docs_path}")
            return False

        try:
            # Collect documents
            documents = []
            metadata = {}

            for file_path in Path(local_docs_path).glob("*.txt"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                documents.append(content)
                doc_id = str(len(documents) - 1)
                metadata[doc_id] = {
                    "filename": file_path.name,
                    "domain": domain,
                    "source_path": str(file_path),
                    "length": len(content),
                    "doc_id": doc_id
                }

                logger.info(f"📄 Processed: {file_path.name}")

            if not documents:
                logger.warning("⚠️ No documents found to process")
                return False

            # Create embeddings
            logger.info(f"🧠 Creating embeddings for {len(documents)} documents...")
            embeddings = self.encoder.encode(documents)

            # Create or recreate Qdrant collection
            collection_name = f"{domain}_knowledge_base"
            self._setup_qdrant_collection(collection_name, embeddings.shape[1])

            # Prepare points for Qdrant
            points = []
            for i, (embedding, doc, meta) in enumerate(zip(embeddings, documents, metadata.values())):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "content": doc,
                        "filename": meta["filename"],
                        "domain": domain,
                        "source_path": meta["source_path"],
                        "length": meta["length"],
                        "doc_index": i
                    }
                )
                points.append(point)

            # Upload to Qdrant
            logger.info(f"📤 Uploading {len(points)} points to Qdrant collection: {collection_name}")
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )

            # Save metadata to NAS for backup
            metadata_file = self.config.get_metadata_path(domain)
            documents_dir = self.config.get_documents_path(domain)

            # Save metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved metadata backup: {metadata_file}")

            # Copy documents to NAS for backup
            os.makedirs(documents_dir, exist_ok=True)
            for i, (doc, meta) in enumerate(zip(documents, metadata.values())):
                doc_file = os.path.join(documents_dir, meta["filename"])
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(doc)
            logger.info(f"✅ Copied {len(documents)} documents to: {documents_dir}")

            logger.info(f"✅ Successfully created Qdrant collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to process documents: {e}")
            return False
    
    def _setup_qdrant_collection(self, collection_name: str, vector_size: int):
        """Setup Qdrant collection for embeddings."""
        try:
            # Delete existing collection if it exists
            try:
                self.qdrant_client.delete_collection(collection_name)
                logger.info(f"🗑️ Deleted existing collection: {collection_name}")
            except Exception:
                pass  # Collection doesn't exist

            # Create new collection
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Created Qdrant collection: {collection_name}")

        except Exception as e:
            logger.error(f"❌ Failed to setup Qdrant collection: {e}")
            raise

    def test_embeddings(self, domain: str = "vedas") -> bool:
        """Test the created embeddings in Qdrant."""
        logger.info(f"🧪 Testing embeddings for domain: {domain}")

        try:
            collection_name = f"{domain}_knowledge_base"

            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == collection_name for col in collections.collections)

            if not collection_exists:
                logger.error(f"❌ Qdrant collection not found: {collection_name}")
                return False

            # Get collection info
            collection_info = self.qdrant_client.get_collection(collection_name)
            logger.info(f"✅ Found Qdrant collection with {collection_info.points_count} vectors")

            # Test query
            test_query = "What is dharma?"
            query_embedding = self.encoder.encode([test_query])

            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=3
            )

            logger.info(f"🔍 Test query: '{test_query}'")
            logger.info(f"📊 Results:")
            for i, result in enumerate(search_results):
                filename = result.payload.get('filename', 'Unknown')
                score = result.score
                content_preview = result.payload.get('content', '')[:100] + "..."
                logger.info(f"  {i+1}. {filename} (score: {score:.3f})")
                logger.info(f"     {content_preview}")

            return True

        except Exception as e:
            logger.error(f"❌ Testing failed: {e}")
            return False
    
    def create_local_cache(self, domain: str = "vedas"):
        """Create local cache of Qdrant collection and NAS metadata."""
        logger.info(f"📦 Creating local cache for domain: {domain}")

        try:
            cache_dir = Path("cache/nas_cache")
            cache_dir.mkdir(parents=True, exist_ok=True)

            collection_name = f"{domain}_knowledge_base"

            # Export Qdrant collection to local cache
            cache_collection_file = cache_dir / f"{domain}_qdrant_backup.json"

            # Get all points from Qdrant collection
            try:
                points = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=10000  # Adjust based on your collection size
                )[0]

                # Save points to JSON for backup
                backup_data = {
                    "collection_name": collection_name,
                    "domain": domain,
                    "points_count": len(points),
                    "points": [
                        {
                            "id": str(point.id),
                            "vector": point.vector,
                            "payload": point.payload
                        }
                        for point in points
                    ]
                }

                with open(cache_collection_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)

                logger.info(f"✅ Cached Qdrant collection: {cache_collection_file}")
                logger.info(f"📊 Cached {len(points)} points")

            except Exception as e:
                logger.warning(f"⚠️ Failed to cache Qdrant collection: {e}")

            # Copy metadata from NAS to local cache
            nas_metadata = self.config.get_metadata_path(domain)
            cache_metadata = cache_dir / f"{domain}_metadata.json"

            if os.path.exists(nas_metadata):
                shutil.copy2(nas_metadata, cache_metadata)
                logger.info(f"✅ Cached metadata: {cache_metadata}")

        except Exception as e:
            logger.error(f"❌ Failed to create cache: {e}")

    def restore_from_cache(self, domain: str = "vedas") -> bool:
        """Restore Qdrant collection from local cache."""
        logger.info(f"🔄 Restoring from cache for domain: {domain}")

        try:
            cache_dir = Path("cache/nas_cache")
            cache_collection_file = cache_dir / f"{domain}_qdrant_backup.json"

            if not cache_collection_file.exists():
                logger.error(f"❌ Cache file not found: {cache_collection_file}")
                return False

            # Load backup data
            with open(cache_collection_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            collection_name = backup_data["collection_name"]
            points_data = backup_data["points"]

            # Get vector size from first point
            if not points_data:
                logger.error("❌ No points in backup data")
                return False

            vector_size = len(points_data[0]["vector"])

            # Setup collection
            self._setup_qdrant_collection(collection_name, vector_size)

            # Restore points
            points = []
            for point_data in points_data:
                point = PointStruct(
                    id=point_data["id"],
                    vector=point_data["vector"],
                    payload=point_data["payload"]
                )
                points.append(point)

            # Upload in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                logger.info(f"📤 Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}")

            logger.info(f"✅ Restored {len(points)} points to collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to restore from cache: {e}")
            return False

def main():
    """Main setup function."""
    print("🚀 BHIV NAS Embeddings Setup")
    print("=" * 50)
    
    setup = NASEmbeddingsSetup()
    
    # Step 1: Check NAS connection
    if not setup.check_nas_connection():
        print("\n❌ Setup failed: NAS not accessible")
        print("💡 Run 'python setup_company_nas.py' first")
        return False
    
    # Step 2: Create directory structure
    if not setup.create_nas_directory_structure():
        print("\n❌ Setup failed: Could not create directories")
        return False
    
    # Step 3: Process documents (you need to provide local documents)
    local_docs = input("\n📁 Enter path to local documents (or press Enter to skip): ").strip()
    if local_docs and os.path.exists(local_docs):
        domain = input("🏷️ Enter domain name (default: vedas): ").strip() or "vedas"
        
        if setup.process_local_documents(local_docs, domain):
            print(f"\n✅ Successfully processed documents for domain: {domain}")
            
            # Step 4: Test embeddings
            if setup.test_embeddings(domain):
                print(f"\n✅ Embeddings test passed for domain: {domain}")
                
                # Step 5: Create local cache
                setup.create_local_cache(domain)
                print(f"\n✅ Local cache created for domain: {domain}")
                
                print(f"\n🎉 Setup complete! You can now use NAS embeddings.")
                print(f"💡 Test with: python example_usage.py")
                return True
    
    print("\n⚠️ Setup completed with warnings. Check logs above.")
    return False

if __name__ == "__main__":
    main()
