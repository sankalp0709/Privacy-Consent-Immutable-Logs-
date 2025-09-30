#!/usr/bin/env python3
"""
Configuration Test Script for Uniguru-LM Service
Tests all the configuration and connectivity before starting the main service
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test that all required environment variables are present"""
    logger.info("🔧 Testing Environment Variables...")
    
    required_vars = [
        'GEMINI_API_KEY',
        'GROQ_API_KEY', 
        'MONGO_URI',
        'NAS_PATH',
        'QDRANT_URL',
        'OLLAMA_URL',
        'OLLAMA_MODEL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mask sensitive info
            if 'API_KEY' in var:
                masked_value = value[:10] + "..." if len(value) > 10 else "***"
                logger.info(f"  ✅ {var}: {masked_value}")
            else:
                logger.info(f"  ✅ {var}: {value}")
    
    if missing_vars:
        logger.error(f"  ❌ Missing environment variables: {missing_vars}")
        return False
    
    logger.info("  ✅ All required environment variables present")
    return True

def test_nas_connectivity():
    """Test NAS and local path connectivity"""
    logger.info("🌐 Testing NAS and Local Path Connectivity...")
    
    paths_to_test = [
        ("NAS Path", os.getenv("NAS_PATH", r"\\192.168.0.94\Guruukul_DB")),
        ("Local Qdrant Data", os.getenv("QDRANT_DATA_PATH", r"G:\qdrant_data")),
        ("Local Embeddings", os.getenv("EMBEDDINGS_PATH", r"G:\qdrant_embeddings")),
        ("Local Documents", os.getenv("DOCUMENTS_PATH", r"G:\source_documents"))
    ]
    
    accessible_paths = []
    for name, path in paths_to_test:
        try:
            if os.path.exists(path):
                logger.info(f"  ✅ {name}: Accessible at {path}")
                accessible_paths.append(name)
            else:
                logger.warning(f"  ⚠️  {name}: Not accessible at {path}")
        except Exception as e:
            logger.error(f"  ❌ {name}: Error checking {path} - {e}")
    
    if accessible_paths:
        logger.info(f"  ✅ {len(accessible_paths)} paths accessible")
        return True
    else:
        logger.error("  ❌ No data paths accessible")
        return False

def test_qdrant_folders():
    """Test Qdrant folder structure"""
    logger.info("📁 Testing Qdrant Folder Structure...")
    
    # Try both local and NAS paths
    base_paths = [
        os.getenv("QDRANT_DATA_PATH", r"G:\qdrant_data"),
        os.path.join(os.getenv("NAS_PATH", r"\\192.168.0.94\Guruukul_DB"), "qdrant_data")
    ]
    
    folders = ["qdrant_data", "qdrant_fourth_data", "qdrant_legacy_data", "qdrant_new_data"]
    found_folders = []
    
    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue
            
        logger.info(f"  📂 Checking base path: {base_path}")
        for folder in folders:
            folder_path = os.path.join(base_path, folder)
            if os.path.exists(folder_path):
                logger.info(f"    ✅ Found: {folder}")
                found_folders.append(folder)
            else:
                # Try direct folder name under base path
                alt_folder_path = os.path.join(os.path.dirname(base_path), folder)
                if os.path.exists(alt_folder_path):
                    logger.info(f"    ✅ Found: {folder} (at parent level)")
                    found_folders.append(folder)
    
    if found_folders:
        logger.info(f"  ✅ Found {len(set(found_folders))} unique Qdrant folders")
        return True
    else:
        logger.warning("  ⚠️  No Qdrant folders found")
        return False

def test_ollama_connectivity():
    """Test Ollama endpoint connectivity"""
    logger.info("🦙 Testing Ollama Connectivity...")
    
    import requests
    
    ollama_url = os.getenv("OLLAMA_URL")
    if not ollama_url:
        logger.error("  ❌ OLLAMA_URL not configured")
        return False
    
    try:
        # Test with a simple health check or model info
        test_payload = {
            "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
            "prompt": "test",
            "stream": False,
            "options": {"max_tokens": 10}
        }
        
        response = requests.post(
            ollama_url,
            json=test_payload,
            headers={"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"  ✅ Ollama accessible at {ollama_url}")
            return True
        else:
            logger.warning(f"  ⚠️  Ollama returned status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Error connecting to Ollama: {e}")
        return False

def test_mongodb_connectivity():
    """Test MongoDB connectivity"""
    logger.info("🍃 Testing MongoDB Connectivity...")
    
    try:
        from pymongo import MongoClient
        
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/bhiv_core")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        logger.info(f"  ✅ MongoDB accessible at {mongo_uri}")
        return True
        
    except ImportError:
        logger.error("  ❌ pymongo not installed")
        return False
    except Exception as e:
        logger.error(f"  ❌ MongoDB connection failed: {e}")
        return False

def test_qdrant_connectivity():
    """Test Qdrant connectivity"""
    logger.info("🎯 Testing Qdrant Connectivity...")
    
    try:
        from qdrant_client import QdrantClient
        
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        
        # Parse URL for host and port
        from urllib.parse import urlparse
        parsed = urlparse(qdrant_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6333
        
        client = QdrantClient(host=host, port=port)
        collections = client.get_collections()
        
        logger.info(f"  ✅ Qdrant accessible with {len(collections.collections)} collections")
        for collection in collections.collections:
            logger.info(f"    📦 Collection: {collection.name}")
        
        return True
        
    except ImportError:
        logger.error("  ❌ qdrant-client not installed")
        return False
    except Exception as e:
        logger.error(f"  ❌ Qdrant connection failed: {e}")
        return False

def test_import_dependencies():
    """Test that all required Python packages can be imported"""
    logger.info("📦 Testing Python Dependencies...")
    
    dependencies = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('sentence_transformers', 'SentenceTransformers'),
        ('torch', 'PyTorch'),
        ('qdrant_client', 'QdrantClient'),
        ('pymongo', 'PyMongo'),
        ('requests', 'Requests'),
        ('pydantic', 'Pydantic')
    ]
    
    missing_deps = []
    for package, name in dependencies:
        try:
            __import__(package)
            logger.info(f"  ✅ {name}")
        except ImportError:
            logger.error(f"  ❌ {name} (install with: pip install {package})")
            missing_deps.append(package)
    
    if missing_deps:
        logger.error(f"  ❌ Missing dependencies: {missing_deps}")
        return False
    
    logger.info("  ✅ All dependencies available")
    return True

def main():
    """Run all configuration tests"""
    logger.info("🚀 Uniguru-LM Configuration Test")
    logger.info("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Python Dependencies", test_import_dependencies),
        ("NAS and Local Paths", test_nas_connectivity),
        ("Qdrant Folders", test_qdrant_folders),
        ("MongoDB Connection", test_mongodb_connectivity),
        ("Qdrant Connection", test_qdrant_connectivity),
        ("Ollama Connection", test_ollama_connectivity)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 {test_name}")
        try:
            if test_func():
                passed_tests += 1
            logger.info("-" * 30)
        except Exception as e:
            logger.error(f"  ❌ Test failed with exception: {e}")
            logger.info("-" * 30)
    
    # Summary
    logger.info(f"\n📊 Test Results Summary")
    logger.info("=" * 50)
    logger.info(f"Passed: {passed_tests} / {total_tests}")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! Uniguru-LM is ready to start.")
        return True
    elif passed_tests >= total_tests // 2:
        logger.warning("⚠️  Some tests failed, but core functionality should work.")
        return True
    else:
        logger.error("❌ Critical tests failed. Please fix configuration before starting.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)