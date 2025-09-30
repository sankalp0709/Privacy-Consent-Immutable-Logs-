#!/usr/bin/env python3
"""
Multi-Folder Vector Store Manager
Combines embeddings from multiple Qdrant instances (one per NAS folder) for comprehensive search

Configuration via environment variables:
- QDRANT_URL: single instance URL (e.g., http://localhost:6333)
- QDRANT_URLS: comma-separated list of instance URLs (e.g., http://localhost:6333,http://localhost:6334,...)
- QDRANT_INSTANCE_NAMES: comma-separated list of friendly names matching QDRANT_URLS (e.g., qdrant_data,qdrant_fourth_data,...)
- QDRANT_VECTOR_SIZE: expected vector size (default: 384)
- NAS_PATH: base NAS path (used for reference/health only)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class MultiFolderVectorManager:
    """Aggregates search across multiple Qdrant instances and combines results."""
    
    def __init__(self, nas_base_path: Optional[str] = None):
        """Initialize with optional NAS base path and multiple Qdrant endpoints."""
        self.nas_base_path = nas_base_path or os.getenv("NAS_PATH", r"\\192.168.0.94\Guruukul_DB")
        self.vector_size = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))
        
        # Initialize encoder once
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Build list of Qdrant instances
        urls_env = os.getenv("QDRANT_URLS")
        if urls_env:
            self.instance_urls = [u.strip() for u in urls_env.split(",") if u.strip()]
        else:
            # Fallback to single URL
            self.instance_urls = [os.getenv("QDRANT_URL", "http://localhost:6333").strip()]
        
        names_env = os.getenv("QDRANT_INSTANCE_NAMES")
        if names_env:
            names = [n.strip() for n in names_env.split(",") if n.strip()]
            # Pad or trim to match length
            if len(names) < len(self.instance_urls):
                names += [f"qdrant_{i+1}" for i in range(len(names), len(self.instance_urls))]
            self.instance_names = names[:len(self.instance_urls)]
        else:
            # Default names
            default_names = [
                "qdrant_data",
                "qdrant_fourth_data",
                "qdrant_legacy_data",
                "qdrant_new_data"
            ]
            # Map names to instances positionally; pad if needed
            if len(default_names) < len(self.instance_urls):
                default_names += [f"qdrant_{i+1}" for i in range(len(default_names), len(self.instance_urls))]
            self.instance_names = default_names[:len(self.instance_urls)]
        
        # Create clients
        self.clients: Dict[str, QdrantClient] = {}
        for url, name in zip(self.instance_urls, self.instance_names):
            try:
                host_port = url.replace("http://", "").replace("https://", "")
                host = host_port.split(":")[0]
                port = int(host_port.split(":")[1]) if ":" in host_port else 6333
                self.clients[name] = QdrantClient(host, port=port)
            except Exception as e:
                logger.error(f"❌ Failed to initialize Qdrant client for {name} at {url}: {e}")
        
        # Cache collections per instance
        self.available_collections: Dict[str, List[Dict[str, Any]]] = {}
        self.initialize_collections()
    
    def initialize_collections(self):
        """Discover available collections in all Qdrant instances."""
        logger.info("🔍 Discovering collections across Qdrant instances...")
        self.available_collections.clear()
        
        for name, client in self.clients.items():
            try:
                collections = client.get_collections()
                instance_collections = []
                for collection in collections.collections:
                    try:
                        info = client.get_collection(collection.name)
                        if info.points_count > 0:
                            vector_size = None
                            try:
                                vector_size = info.config.params.vectors.size
                            except Exception:
                                pass
                            instance_collections.append({
                                "name": collection.name,
                                "points_count": info.points_count,
                                "vector_size": vector_size
                            })
                    except Exception as e:
                        logger.warning(f"⚠️ Error checking collection {collection.name} on {name}: {e}")
                self.available_collections[name] = instance_collections
                logger.info(f"✅ {name}: {len(instance_collections)} collections with data")
            except Exception as e:
                logger.error(f"❌ Error listing collections on {name}: {e}")
        
        total = sum(len(cols) for cols in self.available_collections.values())
        logger.info(f"🎯 Total available collections across instances: {total}")
    
    def search_all_folders(self, query: str, top_k: int = 5, instance_weights: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Search across all instances and combine results for best matches.
        
        Args:
            query: Search query
            top_k: Total number of results to return
            instance_weights: Optional weights per instance name
        """
        if not instance_weights:
            # Default weights: prefer newer instances by common naming
            instance_weights = {}
            for name in self.instance_names:
                if "new" in name:
                    instance_weights[name] = 1.0
                elif "fourth" in name:
                    instance_weights[name] = 0.9
                elif "legacy" in name:
                    instance_weights[name] = 0.7
                else:
                    instance_weights[name] = 0.8
        
        logger.info(f"🔎 Searching across {len(self.clients)} instances for: '{query}'")
        query_embedding = self.encoder.encode(query)
        all_results: List[Dict[str, Any]] = []
        
        for instance_name, collections in self.available_collections.items():
            if not collections:
                continue
            weight = instance_weights.get(instance_name, 0.8)
            client = self.clients.get(instance_name)
            logger.info(f"📡 Instance: {instance_name} (weight {weight})")
            
            for col in collections:
                collection_name = col["name"]
                try:
                    res = client.query_points(
                        collection_name=collection_name,
                        query=query_embedding.tolist(),
                        limit=top_k * 2
                    )
                    for point in res.points:
                        score = float(point.score) * weight
                        payload = point.payload or {}
                        all_results.append({
                            "content": payload.get("content", ""),
                            "document_id": payload.get("document_id", ""),
                            "source": payload.get("source", instance_name),
                            "score": score,
                            "folder": instance_name,
                            "collection": collection_name,
                            "metadata": payload.get("metadata", {})
                        })
                except Exception as e:
                    logger.warning(f"⚠️ Search error on {instance_name}/{collection_name}: {e}")
        
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]
    
    def get_folder_statistics(self) -> Dict[str, Any]:
        """Get statistics about all instances and collections."""
        stats = {
            "available_folders": len(self.available_collections),
            "total_collections": 0,
            "total_points": 0,
            "folder_details": {}
        }
        
        for name, collections in self.available_collections.items():
            points = sum(col.get("points_count", 0) for col in collections)
            stats["folder_details"][name] = {
                "collections": len(collections),
                "total_points": points,
                "collections_info": collections
            }
            stats["total_collections"] += len(collections)
            stats["total_points"] += points
        
        # Backward compatible key
        stats["total_folders"] = len(self.available_collections)
        return stats
    
    def health_check(self) -> Dict[str, bool]:
        """Check health by verifying each instance returns collections."""
        health: Dict[str, bool] = {}
        for name, client in self.clients.items():
            try:
                collections = client.get_collections()
                health[name] = len(collections.collections) > 0
            except Exception:
                health[name] = False
        return health

# CLI test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    mgr = MultiFolderVectorManager()
    print("📊 Stats:", mgr.get_folder_statistics())
    print("🏥 Health:", mgr.health_check())
    results = mgr.search_all_folders("What is dharma?", top_k=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['folder']}/{r['collection']} score={r['score']:.3f} :: {r['content'][:100]}...")
