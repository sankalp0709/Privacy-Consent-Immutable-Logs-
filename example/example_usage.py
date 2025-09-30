#!/usr/bin/env python3
"""
Example Usage of NAS Knowledge Retrieval in BHIV
Demonstrates how to integrate NAS-based knowledge retrieval with your agents
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from nas_retriever import NASKnowledgeRetriever
from nas_config import NASConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BHIVNASAgent:
    """Example BHIV agent using NAS knowledge retrieval."""
    
    def __init__(self, domain: str = "vedas"):
        self.domain = domain
        self.retriever = NASKnowledgeRetriever(domain)
        self.config = NASConfig()
        
        # Simulated LLM endpoint (replace with your Ollama endpoint)
        self.llm_endpoint = "https://2922af0f519d.ngrok-free.app/api/generate"
        
    def process_query(self, query: str, use_knowledge: bool = True) -> Dict[str, Any]:
        """Process a query using NAS knowledge retrieval + LLM."""
        logger.info(f"🔍 Processing query: '{query}'")
        
        result = {
            "query": query,
            "domain": self.domain,
            "timestamp": str(Path(__file__).stat().st_mtime),
            "knowledge_used": use_knowledge,
            "sources": [],
            "response": ""
        }
        
        try:
            if use_knowledge:
                # Step 1: Retrieve relevant knowledge from NAS
                logger.info("📚 Retrieving knowledge from NAS...")
                knowledge_results = self.retriever.query(query, top_k=3)
                
                if knowledge_results:
                    result["sources"] = knowledge_results
                    
                    # Step 2: Prepare context for LLM
                    context = self._prepare_context(query, knowledge_results)
                    
                    # Step 3: Generate response using LLM with context
                    response = self._generate_llm_response(context)
                    result["response"] = response
                    
                    logger.info(f"✅ Generated response using {len(knowledge_results)} knowledge sources")
                else:
                    logger.warning("⚠️ No knowledge found, using LLM only")
                    result["response"] = self._generate_llm_response(query)
            else:
                # Direct LLM response without knowledge
                result["response"] = self._generate_llm_response(query)
                
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            result["error"] = str(e)
            result["response"] = f"I apologize, but I encountered an error while processing your query: {e}"
        
        return result
    
    def _prepare_context(self, query: str, knowledge_results: List[Dict[str, Any]]) -> str:
        """Prepare context for LLM using retrieved knowledge."""
        context_parts = [
            f"Query: {query}",
            "",
            "Relevant Knowledge:",
        ]
        
        for i, result in enumerate(knowledge_results, 1):
            context_parts.extend([
                f"{i}. Source: {result.get('filename', 'Unknown')}",
                f"   Content: {result.get('content', '')[:300]}...",
                f"   Relevance Score: {result.get('score', 0):.3f}",
                ""
            ])
        
        context_parts.extend([
            "Instructions:",
            f"Based on the above knowledge sources, provide a comprehensive answer to the query about {self.domain}.",
            "If the knowledge sources don't contain relevant information, acknowledge this and provide a general response.",
            "Always cite the sources when using specific information from them.",
            "",
            "Response:"
        ])
        
        return "\n".join(context_parts)
    
    def _generate_llm_response(self, prompt: str) -> str:
        """Generate response using LLM (simulated for this example)."""
        # In a real implementation, you would call your Ollama endpoint here
        # For this example, we'll simulate the response
        
        logger.info("🤖 Generating LLM response...")
        
        # Simulated response based on domain
        domain_responses = {
            "vedas": f"Based on the Vedic knowledge, regarding '{prompt[:50]}...', the ancient texts teach us about the interconnectedness of all existence. The concept relates to dharma (righteous duty), karma (action and consequence), and the pursuit of moksha (liberation). The Vedas emphasize that true understanding comes through both study and practice of these principles.",
            
            "education": f"From an educational perspective, '{prompt[:50]}...' involves understanding fundamental learning principles. Effective education combines theoretical knowledge with practical application, encouraging critical thinking and lifelong learning. The key is to create engaging learning experiences that adapt to individual needs and learning styles.",
            
            "wellness": f"Regarding wellness and '{prompt[:50]}...', a holistic approach considers physical, mental, and emotional well-being. This includes regular exercise, balanced nutrition, stress management, adequate sleep, and maintaining positive relationships. The goal is to achieve harmony between mind, body, and spirit.",
            
            "general": f"Concerning '{prompt[:50]}...', this is a multifaceted topic that requires careful consideration of various perspectives. The answer involves understanding the underlying principles, examining different viewpoints, and applying critical thinking to reach meaningful conclusions."
        }
        
        response = domain_responses.get(self.domain, domain_responses["general"])
        
        # Add a note about knowledge sources if this was a context-based query
        if "Relevant Knowledge:" in prompt:
            response += "\n\n*This response was generated using knowledge retrieved from our company's knowledge base.*"
        
        return response
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        retriever_stats = self.retriever.get_stats()
        
        return {
            "agent_domain": self.domain,
            "nas_config": self.config.get_config(),
            "retriever_stats": retriever_stats,
            "llm_endpoint": self.llm_endpoint
        }

def demo_basic_usage():
    """Demonstrate basic usage of NAS knowledge retrieval."""
    print("🚀 BHIV NAS Knowledge Retrieval Demo")
    print("=" * 50)
    
    # Test different domains
    domains = ["vedas", "education", "wellness"]
    
    for domain in domains:
        print(f"\n🏷️ Testing domain: {domain}")
        print("-" * 30)
        
        try:
            agent = BHIVNASAgent(domain)
            
            # Test queries for each domain
            test_queries = {
                "vedas": "What is the meaning of dharma?",
                "education": "How can I improve my learning process?",
                "wellness": "What are the best practices for mental health?"
            }
            
            query = test_queries.get(domain, "What is wisdom?")
            
            # Process with knowledge
            result_with_knowledge = agent.process_query(query, use_knowledge=True)
            
            print(f"📝 Query: {result_with_knowledge['query']}")
            print(f"📚 Knowledge sources found: {len(result_with_knowledge.get('sources', []))}")
            
            if result_with_knowledge.get('sources'):
                print("📄 Top sources:")
                for i, source in enumerate(result_with_knowledge['sources'][:2], 1):
                    print(f"  {i}. {source.get('filename', 'Unknown')} (score: {source.get('score', 0):.3f})")
            
            print(f"🤖 Response: {result_with_knowledge['response'][:200]}...")
            
        except Exception as e:
            print(f"❌ Error testing domain {domain}: {e}")

def demo_interactive_mode():
    """Interactive demo mode."""
    print("\n🎮 Interactive Mode")
    print("=" * 50)
    
    # Choose domain
    print("Available domains: vedas, education, wellness, general")
    domain = input("Choose domain (default: vedas): ").strip() or "vedas"
    
    try:
        agent = BHIVNASAgent(domain)
        
        # Show agent stats
        stats = agent.get_agent_stats()
        print(f"\n📊 Agent Stats:")
        print(f"  Domain: {stats['agent_domain']}")
        print(f"  NAS accessible: {stats['retriever_stats']['nas_accessible']}")
        print(f"  Documents loaded: {stats['retriever_stats']['documents_count']}")
        print(f"  Embeddings loaded: {stats['retriever_stats']['embeddings_loaded']}")
        
        print(f"\n💬 Ask questions about {domain} (type 'quit' to exit)")
        
        while True:
            query = input(f"\n🔍 Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print("🔄 Processing...")
            result = agent.process_query(query)
            
            print(f"\n📚 Knowledge sources: {len(result.get('sources', []))}")
            if result.get('sources'):
                for i, source in enumerate(result['sources'][:2], 1):
                    print(f"  {i}. {source.get('filename', 'Unknown')}")
            
            print(f"\n🤖 Response:")
            print(result['response'])
            
    except Exception as e:
        print(f"❌ Error in interactive mode: {e}")

def demo_integration_with_existing_agents():
    """Show how to integrate with existing BHIV agents."""
    print("\n🔗 Integration with Existing BHIV Agents")
    print("=" * 50)
    
    print("""
To integrate NAS knowledge retrieval with your existing BHIV agents:

1. **Update your KnowledgeAgent.py:**
   
   from example.nas_retriever import NASKnowledgeRetriever
   
   class KnowledgeAgent:
       def __init__(self):
           self.nas_retriever = NASKnowledgeRetriever("vedas")
           # ... existing code
       
       def query(self, query_text: str, filters: dict = None, task_id: str = None):
           # Try NAS first
           nas_results = self.nas_retriever.query(query_text, top_k=5, filters=filters)
           
           if nas_results:
               return self._format_nas_results(nas_results)
           else:
               # Fallback to existing retrieval methods
               return self._fallback_retrieval(query_text)

2. **Update your agent configs:**
   
   Add NAS configuration to config/agent_configs.json:
   {
     "knowledge_agent": {
       "nas_enabled": true,
       "nas_domain": "vedas",
       "fallback_enabled": true
     }
   }

3. **Update your MCP Bridge:**
   
   # In mcp_bridge.py, add NAS support
   if agent_config.get('nas_enabled'):
       nas_domain = agent_config.get('nas_domain', 'general')
       nas_retriever = NASKnowledgeRetriever(nas_domain)
       # Use nas_retriever in your agent processing

4. **Environment Variables:**
   
   Add to your .env file:
   NAS_USERNAME=your_username
   NAS_PASSWORD=your_password
   NAS_DOMAIN=your-company-nas.local
   """)

def main():
    """Main demo function."""
    print("🎯 BHIV NAS Integration Example")
    print("Choose demo mode:")
    print("1. Basic usage demo")
    print("2. Interactive mode")
    print("3. Integration guide")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        demo_basic_usage()
    elif choice == "2":
        demo_interactive_mode()
    elif choice == "3":
        demo_integration_with_existing_agents()
    else:
        print("Running all demos...")
        demo_basic_usage()
        demo_integration_with_existing_agents()

if __name__ == "__main__":
    main()
