#!/usr/bin/env python3
"""
Qdrant Deployment Setup for BHIV NAS Integration
Setup and deploy Qdrant vector database for production use with NAS embeddings
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantDeployment:
    """Deploy and configure Qdrant for BHIV NAS integration."""
    
    def __init__(self, deployment_type: str = "docker"):
        self.deployment_type = deployment_type  # "docker", "local", "cloud"
        self.qdrant_url = "localhost:6333"
        self.qdrant_client = None
        
        # Deployment configurations
        self.configs = {
            "docker": {
                "image": "qdrant/qdrant:latest",
                "port": "6333:6333",
                "volume": "./qdrant_storage:/qdrant/storage",
                "container_name": "bhiv-qdrant"
            },
            "local": {
                "install_command": "pip install qdrant-client[fastembed]",
                "config_path": "./qdrant_config.yaml"
            },
            "cloud": {
                "url": "https://your-cluster.qdrant.io",
                "api_key": os.getenv("QDRANT_API_KEY", "")
            }
        }
    
    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites."""
        logger.info("🔍 Checking deployment prerequisites...")
        
        if self.deployment_type == "docker":
            return self._check_docker()
        elif self.deployment_type == "local":
            return self._check_python_env()
        elif self.deployment_type == "cloud":
            return self._check_cloud_config()
        else:
            logger.error(f"❌ Unknown deployment type: {self.deployment_type}")
            return False
    
    def _check_docker(self) -> bool:
        """Check Docker installation."""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker found: {result.stdout.strip()}")
                return True
            else:
                logger.error("❌ Docker not found")
                return False
        except FileNotFoundError:
            logger.error("❌ Docker not installed")
            return False
    
    def _check_python_env(self) -> bool:
        """Check Python environment."""
        try:
            import qdrant_client
            logger.info("✅ Qdrant client available")
            return True
        except ImportError:
            logger.error("❌ Qdrant client not installed")
            logger.info("💡 Install with: pip install qdrant-client")
            return False
    
    def _check_cloud_config(self) -> bool:
        """Check cloud configuration."""
        config = self.configs["cloud"]
        if not config["api_key"]:
            logger.error("❌ QDRANT_API_KEY not set")
            return False
        
        logger.info("✅ Cloud configuration available")
        return True
    
    def deploy_qdrant(self) -> bool:
        """Deploy Qdrant based on deployment type."""
        logger.info(f"🚀 Deploying Qdrant ({self.deployment_type})...")
        
        if self.deployment_type == "docker":
            return self._deploy_docker()
        elif self.deployment_type == "local":
            return self._deploy_local()
        elif self.deployment_type == "cloud":
            return self._deploy_cloud()
        else:
            logger.error(f"❌ Unknown deployment type: {self.deployment_type}")
            return False
    
    def _deploy_docker(self) -> bool:
        """Deploy Qdrant using Docker."""
        try:
            config = self.configs["docker"]
            
            # Create storage directory
            storage_dir = Path("./qdrant_storage")
            storage_dir.mkdir(exist_ok=True)
            
            # Stop existing container if running
            subprocess.run(['docker', 'stop', config["container_name"]], 
                         capture_output=True)
            subprocess.run(['docker', 'rm', config["container_name"]], 
                         capture_output=True)
            
            # Run Qdrant container
            docker_cmd = [
                'docker', 'run', '-d',
                '--name', config["container_name"],
                '-p', config["port"],
                '-v', config["volume"],
                config["image"]
            ]
            
            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Qdrant container started: {config['container_name']}")
                
                # Wait for Qdrant to be ready
                self._wait_for_qdrant()
                return True
            else:
                logger.error(f"❌ Failed to start Qdrant container: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Docker deployment failed: {e}")
            return False
    
    def _deploy_local(self) -> bool:
        """Deploy Qdrant locally."""
        logger.info("✅ Local Qdrant deployment (using client only)")
        logger.info("💡 Make sure Qdrant server is running separately")
        return True
    
    def _deploy_cloud(self) -> bool:
        """Deploy to Qdrant cloud."""
        config = self.configs["cloud"]
        self.qdrant_url = config["url"]
        logger.info(f"✅ Using Qdrant cloud: {self.qdrant_url}")
        return True
    
    def _wait_for_qdrant(self, timeout: int = 60):
        """Wait for Qdrant to be ready."""
        logger.info("⏳ Waiting for Qdrant to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                client = QdrantClient(self.qdrant_url, prefer_grpc=False)
                client.get_collections()
                logger.info("✅ Qdrant is ready!")
                return True
            except Exception:
                time.sleep(2)
        
        logger.error("❌ Qdrant failed to start within timeout")
        return False
    
    def setup_collections(self, domains: List[str] = None) -> bool:
        """Setup Qdrant collections for different domains."""
        if domains is None:
            domains = ["vedas", "education", "wellness", "general"]
        
        logger.info(f"📚 Setting up collections for domains: {domains}")
        
        try:
            if self.deployment_type == "cloud":
                client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.configs["cloud"]["api_key"]
                )
            else:
                client = QdrantClient(self.qdrant_url, prefer_grpc=False)
            
            self.qdrant_client = client
            
            # Setup collection for each domain
            for domain in domains:
                collection_name = f"{domain}_knowledge_base"
                
                try:
                    # Delete existing collection if it exists
                    client.delete_collection(collection_name)
                    logger.info(f"🗑️ Deleted existing collection: {collection_name}")
                except Exception:
                    pass  # Collection doesn't exist
                
                # Create new collection
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created collection: {collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup collections: {e}")
            return False
    
    def test_deployment(self) -> bool:
        """Test the Qdrant deployment."""
        logger.info("🧪 Testing Qdrant deployment...")
        
        try:
            if self.deployment_type == "cloud":
                client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.configs["cloud"]["api_key"]
                )
            else:
                client = QdrantClient(self.qdrant_url, prefer_grpc=False)
            
            # Test basic operations
            collections = client.get_collections()
            logger.info(f"✅ Found {len(collections.collections)} collections")
            
            for collection in collections.collections:
                info = client.get_collection(collection.name)
                logger.info(f"  📚 {collection.name}: {info.points_count} points")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Deployment test failed: {e}")
            return False
    
    def generate_config_file(self) -> str:
        """Generate configuration file for the deployment."""
        config = {
            "qdrant": {
                "deployment_type": self.deployment_type,
                "url": self.qdrant_url,
                "collections": {
                    "vedas": "vedas_knowledge_base",
                    "education": "education_knowledge_base", 
                    "wellness": "wellness_knowledge_base",
                    "general": "general_knowledge_base"
                }
            },
            "nas": {
                "integration_enabled": True,
                "backup_enabled": True,
                "cache_enabled": True
            }
        }
        
        if self.deployment_type == "cloud":
            config["qdrant"]["api_key_env"] = "QDRANT_API_KEY"
        
        config_file = "config/qdrant_deployment.json"
        os.makedirs("config", exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✅ Configuration saved to: {config_file}")
        return config_file
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for the deployment."""
        return {
            "deployment_type": self.deployment_type,
            "qdrant_url": self.qdrant_url,
            "status": "deployed" if self.qdrant_client else "not_deployed",
            "config": self.configs[self.deployment_type]
        }

def main():
    """Main deployment function."""
    print("🚀 BHIV Qdrant Deployment Setup")
    print("=" * 50)
    
    # Choose deployment type
    print("Choose deployment type:")
    print("1. Docker (recommended for development)")
    print("2. Local (requires separate Qdrant server)")
    print("3. Cloud (Qdrant Cloud service)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    deployment_map = {
        "1": "docker",
        "2": "local", 
        "3": "cloud"
    }
    
    deployment_type = deployment_map.get(choice, "docker")
    
    # Initialize deployment
    deployment = QdrantDeployment(deployment_type)
    
    # Check prerequisites
    if not deployment.check_prerequisites():
        print("\n❌ Prerequisites not met. Please install required components.")
        return False
    
    # Deploy Qdrant
    if not deployment.deploy_qdrant():
        print("\n❌ Deployment failed.")
        return False
    
    # Setup collections
    domains = input("\nEnter domains (comma-separated, default: vedas,education,wellness): ").strip()
    if domains:
        domains = [d.strip() for d in domains.split(",")]
    else:
        domains = ["vedas", "education", "wellness"]
    
    if not deployment.setup_collections(domains):
        print("\n❌ Collection setup failed.")
        return False
    
    # Test deployment
    if not deployment.test_deployment():
        print("\n❌ Deployment test failed.")
        return False
    
    # Generate config
    config_file = deployment.generate_config_file()
    
    # Show connection info
    info = deployment.get_connection_info()
    print(f"\n✅ Deployment successful!")
    print(f"📊 Connection Info:")
    print(f"  Type: {info['deployment_type']}")
    print(f"  URL: {info['qdrant_url']}")
    print(f"  Status: {info['status']}")
    print(f"  Config: {config_file}")
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Run: python example/setup_nas_embeddings.py")
    print(f"2. Test: python example/test_nas_integration.py")
    print(f"3. Use: python example/example_usage.py")
    
    return True

if __name__ == "__main__":
    main()
