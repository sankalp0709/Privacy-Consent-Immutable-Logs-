#!/usr/bin/env python3
"""
Local BHIV Setup (No Docker, No NAS Admin Access Required)
Simple setup for testing and development
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalBHIVSetup:
    """Local BHIV setup without Docker or NAS admin requirements."""
    
    def __init__(self):
        self.setup_dir = Path("local_setup")
        self.setup_dir.mkdir(exist_ok=True)
        
        self.config = {
            "qdrant_url": "localhost:6333",
            "local_storage": str(self.setup_dir / "storage"),
            "domains": ["vedas", "education", "wellness"],
            "cache_dir": str(self.setup_dir / "cache")
        }
    
    def check_prerequisites(self) -> bool:
        """Check if we can run local setup."""
        logger.info("🔍 Checking local setup prerequisites...")
        
        try:
            # Check Python packages
            import qdrant_client
            import sentence_transformers
            logger.info("✅ Required packages available")
            
            # Create local directories
            os.makedirs(self.config["local_storage"], exist_ok=True)
            os.makedirs(self.config["cache_dir"], exist_ok=True)
            logger.info("✅ Local directories created")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Missing packages: {e}")
            logger.info("💡 Install with: pip install qdrant-client sentence-transformers")
            return False
        except Exception as e:
            logger.error(f"❌ Prerequisites check failed: {e}")
            return False
    
    def start_local_qdrant(self) -> bool:
        """Start Qdrant in local mode."""
        logger.info("🗄️ Starting local Qdrant...")
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams
            
            # Try to connect to existing Qdrant instance
            try:
                client = QdrantClient("localhost", port=6333, prefer_grpc=False)
                collections = client.get_collections()
                logger.info("✅ Connected to existing Qdrant instance")
                return True
            except Exception:
                logger.info("🔄 No existing Qdrant found, starting local instance...")
            
            # Start local Qdrant instance
            try:
                # Try using qdrant-client local mode
                client = QdrantClient(":memory:")  # In-memory for testing
                logger.info("✅ Started in-memory Qdrant instance")
                
                # Create collections for each domain
                for domain in self.config["domains"]:
                    collection_name = f"{domain}_knowledge_base"
                    try:
                        client.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(
                                size=384,  # all-MiniLM-L6-v2 embedding size
                                distance=Distance.COSINE
                            )
                        )
                        logger.info(f"✅ Created collection: {collection_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Collection {collection_name} might already exist: {e}")
                
                # Store client reference
                self.qdrant_client = client
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to start local Qdrant: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Qdrant setup failed: {e}")
            return False
    
    def create_sample_data(self) -> bool:
        """Create sample data for testing."""
        logger.info("📚 Creating sample knowledge data...")
        
        try:
            # Create sample documents for each domain
            sample_data = {
                "vedas": [
                    "Dharma is the principle of cosmic order and individual righteousness in Hindu philosophy.",
                    "Karma refers to the law of cause and effect governing actions and their consequences.",
                    "The Vedas are ancient Sanskrit texts that form the foundation of Hindu knowledge.",
                    "Meditation is a practice of focused attention to achieve mental clarity and spiritual insight.",
                    "Moksha represents liberation from the cycle of birth, death, and rebirth."
                ],
                "education": [
                    "Active learning involves engaging with material through discussion, practice, and teaching others.",
                    "Spaced repetition is a learning technique that involves reviewing information at increasing intervals.",
                    "Critical thinking is the objective analysis and evaluation of an issue to form a judgment.",
                    "Learning styles refer to different approaches or ways of learning and processing information.",
                    "Educational psychology studies how people learn and the best practices for teaching."
                ],
                "wellness": [
                    "Regular exercise improves cardiovascular health, strengthens muscles, and enhances mental well-being.",
                    "Mindfulness meditation reduces stress, improves focus, and promotes emotional regulation.",
                    "A balanced diet includes fruits, vegetables, whole grains, lean proteins, and healthy fats.",
                    "Adequate sleep is essential for physical recovery, memory consolidation, and immune function.",
                    "Social connections and relationships are crucial for mental health and overall life satisfaction."
                ]
            }
            
            # Save sample data to local files
            docs_dir = Path(self.config["local_storage"]) / "documents"
            docs_dir.mkdir(exist_ok=True)
            
            for domain, texts in sample_data.items():
                domain_dir = docs_dir / f"{domain}_texts"
                domain_dir.mkdir(exist_ok=True)
                
                for i, text in enumerate(texts, 1):
                    file_path = domain_dir / f"{domain}_sample_{i}.txt"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                
                logger.info(f"✅ Created {len(texts)} sample documents for {domain}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create sample data: {e}")
            return False
    
    def setup_embeddings(self) -> bool:
        """Setup embeddings for sample data."""
        logger.info("🧠 Setting up embeddings...")
        
        try:
            from sentence_transformers import SentenceTransformer
            from qdrant_client.http.models import PointStruct
            import uuid
            
            # Initialize encoder
            encoder = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Process each domain
            docs_dir = Path(self.config["local_storage"]) / "documents"
            
            for domain in self.config["domains"]:
                domain_dir = docs_dir / f"{domain}_texts"
                
                if not domain_dir.exists():
                    logger.warning(f"⚠️ No documents found for {domain}")
                    continue
                
                # Read documents
                documents = []
                for txt_file in domain_dir.glob("*.txt"):
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            documents.append({
                                "content": content,
                                "filename": txt_file.name,
                                "domain": domain
                            })
                
                if not documents:
                    logger.warning(f"⚠️ No valid documents for {domain}")
                    continue
                
                # Create embeddings
                texts = [doc["content"] for doc in documents]
                embeddings = encoder.encode(texts)
                
                # Upload to Qdrant
                collection_name = f"{domain}_knowledge_base"
                points = []
                
                for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding.tolist(),
                        payload={
                            "content": doc["content"],
                            "filename": doc["filename"],
                            "domain": doc["domain"],
                            "doc_index": i
                        }
                    )
                    points.append(point)
                
                # Upload to Qdrant
                if hasattr(self, 'qdrant_client'):
                    self.qdrant_client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                    logger.info(f"✅ Uploaded {len(points)} embeddings for {domain}")
                else:
                    logger.warning(f"⚠️ No Qdrant client available for {domain}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Embeddings setup failed: {e}")
            return False
    
    def test_setup(self) -> bool:
        """Test the local setup."""
        logger.info("🧪 Testing local setup...")
        
        try:
            from example.nas_retriever import NASKnowledgeRetriever
            
            # Test each domain
            for domain in self.config["domains"]:
                try:
                    # Use in-memory Qdrant (port doesn't matter for in-memory)
                    retriever = NASKnowledgeRetriever(domain, qdrant_url=":memory:")
                    
                    # Test query
                    test_queries = {
                        "vedas": "What is dharma?",
                        "education": "How to learn effectively?",
                        "wellness": "How to stay healthy?"
                    }
                    
                    query = test_queries.get(domain, "What is knowledge?")
                    results = retriever.query(query, top_k=3)
                    
                    logger.info(f"✅ {domain}: Found {len(results)} results for '{query}'")
                    
                except Exception as e:
                    logger.warning(f"⚠️ {domain} test failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Testing failed: {e}")
            return False
    
    def generate_config(self) -> bool:
        """Generate configuration files."""
        logger.info("📝 Generating local configuration...")
        
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            local_config = {
                "bhiv_local_setup": {
                    "version": "1.0",
                    "setup_type": "local",
                    "qdrant_mode": "in_memory",
                    "storage_path": self.config["local_storage"],
                    "cache_path": self.config["cache_dir"],
                    "domains": self.config["domains"],
                    "sample_data": True,
                    "status": "ready"
                }
            }
            
            config_file = config_dir / "bhiv_local_setup.json"
            with open(config_file, 'w') as f:
                json.dump(local_config, f, indent=2)
            
            logger.info(f"✅ Local configuration saved to: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Config generation failed: {e}")
            return False
    
    def run_setup(self) -> bool:
        """Run complete local setup."""
        logger.info("🚀 Starting Local BHIV Setup")
        logger.info("=" * 50)
        
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Local Qdrant", self.start_local_qdrant),
            ("Sample Data", self.create_sample_data),
            ("Embeddings", self.setup_embeddings),
            ("Testing", self.test_setup),
            ("Configuration", self.generate_config)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 {step_name}...")
            try:
                if step_func():
                    logger.info(f"✅ {step_name} - SUCCESS")
                else:
                    logger.error(f"❌ {step_name} - FAILED")
                    return False
            except Exception as e:
                logger.error(f"❌ {step_name} - ERROR: {e}")
                return False
        
        logger.info("\n🎉 LOCAL SETUP COMPLETE!")
        logger.info("Your BHIV system is ready for testing with sample data.")
        logger.info("\n🎯 Next Steps:")
        logger.info("1. Test queries: python example/example_usage.py")
        logger.info("2. Start BHIV API: python simple_api.py")
        logger.info("3. Add your own documents later")
        
        return True

def main():
    """Main setup function."""
    print("🏠 BHIV Local Setup (No Docker, No NAS Admin Required)")
    print("=" * 60)
    print("This will create a local BHIV system with sample data for testing.")
    print()
    
    setup = LocalBHIVSetup()
    success = setup.run_setup()
    
    if success:
        print("\n✅ Setup successful! You can now test your BHIV system.")
    else:
        print("\n❌ Setup failed. Check the logs above for details.")
    
    return success

if __name__ == "__main__":
    main()
