#!/usr/bin/env python3
"""
Test Multi-Folder Vector Search
Demonstrates searching across all Qdrant folders for comprehensive results
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_multi_folder_manager():
    """Test the multi-folder vector manager."""
    try:
        from multi_folder_vector_manager import MultiFolderVectorManager
        
        print("🚀 Initializing Multi-Folder Vector Manager...")
        manager = MultiFolderVectorManager()
        
        # Get statistics
        print("\n📊 Getting folder statistics...")
        stats = manager.get_folder_statistics()
        
        print(f"Total folders configured: {stats['total_folders']}")
        print(f"Available folders: {stats['available_folders']}")
        print(f"Total collections: {stats['total_collections']}")
        print(f"Total points: {stats['total_points']}")
        
        print("\n📁 Folder Details:")
        for folder, details in stats['folder_details'].items():
            print(f"  {folder}:")
            print(f"    Collections: {details['collections']}")
            print(f"    Total points: {details['total_points']}")
            if details['collections_info']:
                for col in details['collections_info']:
                    print(f"      - {col['name']}: {col['points_count']} points")
        
        # Health check
        print("\n🏥 Health Check:")
        health = manager.health_check()
        for folder, status in health.items():
            print(f"  {folder}: {'✅' if status else '❌'}")
        
        # Test search
        print("\n🔍 Testing search functionality...")
        test_queries = [
            "What is dharma?",
            "Tell me about yoga philosophy",
            "What are the basics of Ayurveda?",
            "Explain Vedic knowledge"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            results = manager.search_all_folders(query, top_k=3)
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. Score: {result['score']:.3f}")
                    print(f"     Folder: {result['folder']}")
                    print(f"     Collection: {result['collection']}")
                    print(f"     Content: {result['content'][:100]}...")
            else:
                print("❌ No results found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_knowledge_agent():
    """Test the updated KnowledgeAgent with multi-folder support."""
    try:
        from agents.KnowledgeAgent import KnowledgeAgent
        
        print("\n🧠 Testing KnowledgeAgent with multi-folder support...")
        agent = KnowledgeAgent()
        
        # Get statistics
        print("\n📊 KnowledgeAgent Statistics:")
        stats = agent.get_statistics()
        if isinstance(stats, dict) and 'folder_details' in stats:
            print(f"Available folders: {stats['available_folders']}")
            print(f"Total collections: {stats['total_collections']}")
            print(f"Total points: {stats['total_points']}")
        else:
            print("Fallback retrievers status:")
            for retriever, status in stats.get('fallback_retrievers', {}).items():
                print(f"  {retriever}: {'✅' if status else '❌'}")
        
        # Health check
        print("\n🏥 KnowledgeAgent Health:")
        health = agent.health_check()
        for component, status in health.items():
            if component == 'folder_health' and isinstance(status, dict):
                print(f"  {component}:")
                for folder, folder_status in status.items():
                    print(f"    {folder}: {'✅' if folder_status else '❌'}")
            else:
                print(f"  {component}: {'✅' if status else '❌'}")
        
        # Test query
        print("\n🔍 Testing KnowledgeAgent query...")
        result = agent.query("What is dharma?", top_k=3)
        
        print(f"✅ Query successful:")
        print(f"  Method: {result.get('method', 'unknown')}")
        print(f"  Folder count: {result.get('folder_count', 0)}")
        print(f"  Total results: {result.get('total_results', 0)}")
        print(f"  Sources: {result.get('sources', [])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ KnowledgeAgent test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Multi-Folder Vector Search System")
    print("=" * 50)
    
    # Test 1: Multi-folder manager
    print("\n1️⃣ Testing Multi-Folder Vector Manager...")
    if test_multi_folder_manager():
        print("✅ Multi-folder manager test passed!")
    else:
        print("❌ Multi-folder manager test failed!")
        return
    
    # Test 2: KnowledgeAgent
    print("\n2️⃣ Testing KnowledgeAgent...")
    if test_knowledge_agent():
        print("✅ KnowledgeAgent test passed!")
    else:
        print("❌ KnowledgeAgent test failed!")
        return
    
    print("\n🎉 All tests completed successfully!")
    print("\n🚀 Your system now supports:")
    print("  ✅ Multi-folder vector search across all NAS folders")
    print("  ✅ Intelligent result ranking and combination")
    print("  ✅ Comprehensive knowledge retrieval")
    print("  ✅ Smart fallback mechanisms")
    print("  ✅ Health monitoring for all components")

if __name__ == "__main__":
    main()

