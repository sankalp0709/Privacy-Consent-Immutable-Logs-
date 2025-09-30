#!/usr/bin/env python3
"""
Test NAS Integration for BHIV Knowledge Base
Test connectivity and retrieval from company NAS server
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from nas_config import NASConfig
from nas_retriever import NASKnowledgeRetriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NASIntegrationTest:
    """Test suite for NAS integration."""
    
    def __init__(self):
        self.config = NASConfig()
        self.test_results = {}
    
    def test_nas_connectivity(self) -> bool:
        """Test basic NAS connectivity."""
        logger.info("🔍 Testing NAS connectivity...")
        
        try:
            is_accessible = self.config.is_nas_accessible()
            self.test_results["nas_connectivity"] = is_accessible
            
            if is_accessible:
                logger.info("✅ NAS is accessible")
                
                # Test specific paths
                paths_to_test = [
                    self.config.current_config.get("embeddings_path"),
                    self.config.current_config.get("documents_path"),
                    self.config.current_config.get("metadata_path")
                ]
                
                for path in paths_to_test:
                    if path and os.path.exists(path):
                        logger.info(f"✅ Path accessible: {path}")
                    else:
                        logger.warning(f"⚠️ Path not found: {path}")
                
                return True
            else:
                logger.error("❌ NAS is not accessible")
                return False
                
        except Exception as e:
            logger.error(f"❌ NAS connectivity test failed: {e}")
            self.test_results["nas_connectivity"] = False
            return False
    
    def test_embeddings_loading(self, domain: str = "vedas") -> bool:
        """Test loading embeddings from NAS."""
        logger.info(f"🧠 Testing embeddings loading for domain: {domain}")
        
        try:
            retriever = NASKnowledgeRetriever(domain)
            stats = retriever.get_stats()
            
            self.test_results[f"embeddings_loading_{domain}"] = {
                "embeddings_loaded": stats["embeddings_loaded"],
                "documents_count": stats["documents_count"],
                "metadata_entries": stats["metadata_entries"]
            }
            
            if stats["embeddings_loaded"]:
                logger.info(f"✅ Embeddings loaded successfully")
                logger.info(f"📊 Documents: {stats['documents_count']}")
                logger.info(f"📊 Metadata entries: {stats['metadata_entries']}")
                return True
            else:
                logger.warning(f"⚠️ Embeddings not loaded")
                return False
                
        except Exception as e:
            logger.error(f"❌ Embeddings loading test failed: {e}")
            self.test_results[f"embeddings_loading_{domain}"] = False
            return False
    
    def test_knowledge_retrieval(self, domain: str = "vedas") -> bool:
        """Test knowledge retrieval from NAS."""
        logger.info(f"🔍 Testing knowledge retrieval for domain: {domain}")
        
        try:
            retriever = NASKnowledgeRetriever(domain)
            
            # Test queries for different domains
            test_queries = {
                "vedas": ["What is dharma?", "Explain karma", "What are the Vedas?"],
                "education": ["How to learn effectively?", "What is education?", "Study methods"],
                "wellness": ["How to stay healthy?", "Mental wellness tips", "Exercise benefits"],
                "general": ["What is knowledge?", "How to think?", "What is wisdom?"]
            }
            
            queries = test_queries.get(domain, ["What is the meaning of life?"])
            
            all_successful = True
            for query in queries:
                logger.info(f"🔍 Testing query: '{query}'")
                
                start_time = time.time()
                results = retriever.query(query, top_k=3)
                end_time = time.time()
                
                if results:
                    logger.info(f"✅ Found {len(results)} results in {end_time - start_time:.2f}s")
                    for i, result in enumerate(results[:2]):  # Show top 2
                        logger.info(f"  {i+1}. {result.get('filename', 'Unknown')} (score: {result.get('score', 0):.3f})")
                        logger.info(f"     {result.get('content', '')[:100]}...")
                else:
                    logger.warning(f"⚠️ No results found for query: '{query}'")
                    all_successful = False
            
            self.test_results[f"knowledge_retrieval_{domain}"] = all_successful
            return all_successful
            
        except Exception as e:
            logger.error(f"❌ Knowledge retrieval test failed: {e}")
            self.test_results[f"knowledge_retrieval_{domain}"] = False
            return False
    
    def test_performance(self, domain: str = "vedas") -> bool:
        """Test retrieval performance."""
        logger.info(f"⚡ Testing performance for domain: {domain}")
        
        try:
            retriever = NASKnowledgeRetriever(domain)
            
            # Performance test queries
            test_queries = [
                "What is the meaning of life?",
                "How to achieve happiness?",
                "What is wisdom?",
                "Explain consciousness",
                "What is truth?"
            ]
            
            total_time = 0
            successful_queries = 0
            
            for query in test_queries:
                start_time = time.time()
                results = retriever.query(query, top_k=5)
                end_time = time.time()
                
                query_time = end_time - start_time
                total_time += query_time
                
                if results:
                    successful_queries += 1
                    logger.info(f"✅ Query '{query[:30]}...' completed in {query_time:.2f}s")
                else:
                    logger.warning(f"⚠️ Query '{query[:30]}...' returned no results")
            
            avg_time = total_time / len(test_queries) if test_queries else 0
            success_rate = successful_queries / len(test_queries) if test_queries else 0
            
            logger.info(f"📊 Performance Results:")
            logger.info(f"  Average query time: {avg_time:.2f}s")
            logger.info(f"  Success rate: {success_rate:.1%}")
            logger.info(f"  Total queries: {len(test_queries)}")
            
            self.test_results[f"performance_{domain}"] = {
                "avg_time": avg_time,
                "success_rate": success_rate,
                "total_queries": len(test_queries)
            }
            
            # Consider test successful if avg time < 2s and success rate > 80%
            return avg_time < 2.0 and success_rate > 0.8
            
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.test_results[f"performance_{domain}"] = False
            return False
    
    def test_fallback_mechanisms(self, domain: str = "vedas") -> bool:
        """Test fallback mechanisms when NAS is unavailable."""
        logger.info(f"🔄 Testing fallback mechanisms for domain: {domain}")
        
        try:
            # Temporarily simulate NAS unavailability
            original_config = self.config.current_config.copy()
            
            # Modify config to point to non-existent path
            self.config.current_config["embeddings_path"] = "/non/existent/path"
            
            retriever = NASKnowledgeRetriever(domain)
            results = retriever.query("test query", top_k=3)
            
            # Restore original config
            self.config.current_config = original_config
            
            if results:
                logger.info(f"✅ Fallback mechanism working - found {len(results)} results")
                self.test_results[f"fallback_{domain}"] = True
                return True
            else:
                logger.warning(f"⚠️ Fallback mechanism returned no results")
                self.test_results[f"fallback_{domain}"] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Fallback test failed: {e}")
            self.test_results[f"fallback_{domain}"] = False
            return False
    
    def run_all_tests(self, domains: list = None) -> dict:
        """Run all tests for specified domains."""
        if domains is None:
            domains = ["vedas"]
        
        logger.info("🚀 Starting NAS Integration Tests")
        logger.info("=" * 50)
        
        # Test 1: NAS Connectivity
        connectivity_ok = self.test_nas_connectivity()
        
        if not connectivity_ok:
            logger.error("❌ NAS connectivity failed - skipping other tests")
            return self.test_results
        
        # Test other components for each domain
        for domain in domains:
            logger.info(f"\n🏷️ Testing domain: {domain}")
            logger.info("-" * 30)
            
            self.test_embeddings_loading(domain)
            self.test_knowledge_retrieval(domain)
            self.test_performance(domain)
            self.test_fallback_mechanisms(domain)
        
        # Summary
        logger.info("\n📊 Test Summary")
        logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, bool) and result)
        
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success rate: {passed_tests/total_tests:.1%}")
        
        return self.test_results

def main():
    """Main test function."""
    print("🧪 BHIV NAS Integration Test Suite")
    print("=" * 50)
    
    # Get domains to test
    domains_input = input("Enter domains to test (comma-separated, default: vedas): ").strip()
    if domains_input:
        domains = [d.strip() for d in domains_input.split(",")]
    else:
        domains = ["vedas"]
    
    # Run tests
    tester = NASIntegrationTest()
    results = tester.run_all_tests(domains)
    
    # Save results
    import json
    results_file = "nas_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {results_file}")
    print("🎯 Next steps:")
    print("  1. Fix any failed tests")
    print("  2. Run 'python example_usage.py' to see integration in action")
    print("  3. Integrate with your BHIV agents")

if __name__ == "__main__":
    main()
