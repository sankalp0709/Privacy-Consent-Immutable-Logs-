#!/usr/bin/env python3
"""
Quick Test Script for BHIV NAS + Qdrant Setup
Run this to verify your setup is working correctly
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_qdrant_connection():
    """Test if Qdrant is running and accessible."""
    print("🔍 Testing Qdrant connection...")
    
    try:
        response = requests.get("http://localhost:6333/collections", timeout=5)
        if response.status_code == 200:
            collections = response.json()
            print(f"✅ Qdrant is running with {len(collections.get('result', {}).get('collections', []))} collections")
            
            # List collections
            for collection in collections.get('result', {}).get('collections', []):
                print(f"  📚 Collection: {collection['name']}")
            
            return True
        else:
            print(f"❌ Qdrant responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Qdrant (not running or wrong port)")
        return False
    except Exception as e:
        print(f"❌ Qdrant test failed: {e}")
        return False

def test_nas_retriever():
    """Test NAS retriever functionality."""
    print("\n🏢 Testing NAS retriever...")
    
    try:
        from example.nas_retriever import NASKnowledgeRetriever
        
        # Test with vedas domain
        retriever = NASKnowledgeRetriever("vedas")
        stats = retriever.get_stats()
        
        print(f"✅ NAS retriever initialized")
        print(f"  📊 Domain: {stats['domain']}")
        print(f"  🗄️ Qdrant available: {stats['qdrant_available']}")
        print(f"  📁 NAS accessible: {stats['nas_accessible']}")
        print(f"  📄 Documents count: {stats['documents_count']}")
        
        # Test a simple query
        results = retriever.query("What is wisdom?", top_k=3)
        print(f"  🔍 Test query returned {len(results)} results")
        
        if results:
            for i, result in enumerate(results[:2], 1):
                print(f"    {i}. {result.get('filename', 'Unknown')} (score: {result.get('score', 0):.3f})")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import NAS retriever: {e}")
        return False
    except Exception as e:
        print(f"❌ NAS retriever test failed: {e}")
        return False

def test_bhiv_api():
    """Test BHIV API if it's running."""
    print("\n🚀 Testing BHIV API...")
    
    try:
        # Test if simple_api.py is running
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ BHIV API is running")
            
            # Test a query
            query_data = {
                "query": "What is dharma?",
                "domain": "vedas"
            }
            
            response = requests.post(
                "http://localhost:8001/query",
                json=query_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API query successful")
                print(f"  📝 Response length: {len(str(result.get('response', '')))}")
                return True
            else:
                print(f"❌ API query failed with status {response.status_code}")
                return False
                
        else:
            print(f"❌ BHIV API responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️ BHIV API not running (start with: python simple_api.py)")
        return False
    except Exception as e:
        print(f"❌ BHIV API test failed: {e}")
        return False

def test_docker_qdrant():
    """Test if Qdrant Docker container is running."""
    print("\n🐳 Testing Docker Qdrant...")
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        
        if result.returncode == 0:
            if 'bhiv-qdrant' in result.stdout or 'qdrant' in result.stdout:
                print("✅ Qdrant Docker container is running")
                return True
            else:
                print("❌ Qdrant Docker container not found")
                print("💡 Start with: docker run -p 6333:6333 qdrant/qdrant:latest")
                return False
        else:
            print("❌ Docker command failed")
            return False
            
    except FileNotFoundError:
        print("⚠️ Docker not installed or not in PATH")
        return False
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def test_config_files():
    """Test if configuration files exist."""
    print("\n📝 Testing configuration files...")
    
    config_files = [
        "config/qdrant_deployment.json",
        "config/bhiv_nas_deployment.json"
    ]
    
    found_configs = 0
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ Found: {config_file}")
            found_configs += 1
        else:
            print(f"⚠️ Missing: {config_file}")
    
    if found_configs > 0:
        print(f"✅ {found_configs}/{len(config_files)} config files found")
        return True
    else:
        print("❌ No configuration files found")
        print("💡 Run: python example/deploy_bhiv_nas.py")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("🧪 BHIV NAS + Qdrant Setup Test")
    print("=" * 50)
    
    tests = [
        ("Docker Qdrant", test_docker_qdrant),
        ("Qdrant Connection", test_qdrant_connection),
        ("NAS Retriever", test_nas_retriever),
        ("Configuration Files", test_config_files),
        ("BHIV API", test_bhiv_api)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is working correctly.")
        print("\n🎯 Next steps:")
        print("1. Add your documents: python example/setup_nas_embeddings.py")
        print("2. Try queries: python example/example_usage.py")
        print("3. Start using: python simple_api.py")
    elif passed >= total * 0.6:  # 60% pass rate
        print("\n⚠️ Most tests passed, but some issues found.")
        print("Check the failed tests above and fix them.")
    else:
        print("\n❌ Many tests failed. Setup needs attention.")
        print("💡 Try running: python example/deploy_bhiv_nas.py")
    
    return passed == total

def quick_fix_suggestions():
    """Provide quick fix suggestions for common issues."""
    print("\n🔧 QUICK FIX SUGGESTIONS")
    print("=" * 50)
    
    print("If Qdrant is not running:")
    print("  docker run -d --name bhiv-qdrant -p 6333:6333 qdrant/qdrant:latest")
    
    print("\nIf NAS retriever fails:")
    print("  pip install qdrant-client sentence-transformers")
    
    print("\nIf BHIV API is not running:")
    print("  python simple_api.py")
    
    print("\nIf no config files:")
    print("  python example/deploy_bhiv_nas.py")
    
    print("\nFor complete setup:")
    print("  python example/deploy_bhiv_nas.py")

def main():
    """Main test function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick test mode
        print("⚡ Quick Test Mode")
        test_qdrant_connection()
        test_nas_retriever()
    elif len(sys.argv) > 1 and sys.argv[1] == "--fix":
        # Show fix suggestions
        quick_fix_suggestions()
    else:
        # Full test mode
        success = run_comprehensive_test()
        
        if not success:
            print("\n" + "=" * 50)
            quick_fix_suggestions()
        
        return success

if __name__ == "__main__":
    main()
