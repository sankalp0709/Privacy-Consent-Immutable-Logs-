"""
Gurukul Backend Integration for BHIV Knowledge Base
Complete integration guide and implementation for Gurukul system
"""

import requests
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class GurukulKnowledgeBaseClient:
    """
    Production-ready client for integrating Gurukul with BHIV Knowledge Base
    """
    
    def __init__(self, bhiv_api_url: str = "http://localhost:8001", timeout: int = 30):
        self.bhiv_api_url = bhiv_api_url.rstrip('/')
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    # ============================================================================
    # CORE KNOWLEDGE BASE METHODS
    # ============================================================================
    
    async def query_knowledge_base(self, query: str, filters: Dict[str, Any] = None, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """
        Main knowledge base query method for Gurukul integration.
        
        Args:
            query: User's question or search query
            filters: Optional filters like {"book": "rigveda", "type": "artha"}
            user_id: Gurukul user identifier
            
        Returns:
            Dict with response, sources, metadata, and status
        """
        try:
            payload = {
                "query": query,
                "filters": filters or {},
                "user_id": user_id,
                "limit": 5
            }
            
            if self.session:
                # Async request
                async with self.session.post(
                    f"{self.bhiv_api_url}/query-kb",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._format_response(result, "success")
                    else:
                        error_text = await response.text()
                        return self._format_error(f"API error {response.status}: {error_text}")
            else:
                # Sync request
                response = requests.post(
                    f"{self.bhiv_api_url}/query-kb",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self._format_response(result, "success")
                else:
                    return self._format_error(f"API error {response.status_code}: {response.text}")
                    
        except Exception as e:
            return self._format_error(f"Connection error: {str(e)}")
    
    async def ask_vedas(self, question: str, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """
        Ask the Vedas for spiritual wisdom - specialized endpoint.
        
        Args:
            question: Spiritual or philosophical question
            user_id: Gurukul user identifier
            
        Returns:
            Dict with spiritual wisdom response
        """
        try:
            payload = {
                "query": question,
                "user_id": user_id
            }
            
            if self.session:
                async with self.session.post(
                    f"{self.bhiv_api_url}/ask-vedas",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._format_response(result, "vedic_wisdom")
                    else:
                        error_text = await response.text()
                        return self._format_error(f"Vedas API error {response.status}: {error_text}")
            else:
                response = requests.post(
                    f"{self.bhiv_api_url}/ask-vedas",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self._format_response(result, "vedic_wisdom")
                else:
                    return self._format_error(f"Vedas API error {response.status_code}: {response.text}")
                    
        except Exception as e:
            return self._format_error(f"Vedas connection error: {str(e)}")
    
    async def get_educational_content(self, topic: str, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """
        Get educational content from the knowledge base.
        
        Args:
            topic: Educational topic or subject
            user_id: Gurukul user identifier
            
        Returns:
            Dict with educational content
        """
        try:
            payload = {
                "query": topic,
                "user_id": user_id
            }
            
            if self.session:
                async with self.session.post(
                    f"{self.bhiv_api_url}/edumentor",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._format_response(result, "educational")
                    else:
                        error_text = await response.text()
                        return self._format_error(f"Education API error {response.status}: {error_text}")
            else:
                response = requests.post(
                    f"{self.bhiv_api_url}/edumentor",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self._format_response(result, "educational")
                else:
                    return self._format_error(f"Education API error {response.status_code}: {response.text}")
                    
        except Exception as e:
            return self._format_error(f"Education connection error: {str(e)}")
    
    # ============================================================================
    # SPECIALIZED SEARCH METHODS
    # ============================================================================
    
    async def search_by_book(self, query: str, book: str, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """Search within a specific Vedic book."""
        filters = {"book": book.lower()}
        return await self.query_knowledge_base(query, filters, user_id)
    
    async def search_by_type(self, query: str, content_type: str, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """Search by content type (dharma, artha, kama, moksha)."""
        filters = {"type": content_type.lower()}
        return await self.query_knowledge_base(query, filters, user_id)
    
    async def advanced_search(self, query: str, book: str = None, content_type: str = None, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """Advanced search with multiple filters."""
        filters = {}
        if book:
            filters["book"] = book.lower()
        if content_type:
            filters["type"] = content_type.lower()
        
        return await self.query_knowledge_base(query, filters, user_id)
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _format_response(self, result: Dict[str, Any], response_type: str) -> Dict[str, Any]:
        """Format API response for Gurukul consumption."""
        return {
            "success": True,
            "type": response_type,
            "response": result.get("response", ""),
            "sources": result.get("sources", []),
            "knowledge_base_results": result.get("knowledge_base_results", 0),
            "metadata": {
                "query_id": result.get("query_id"),
                "timestamp": datetime.now().isoformat(),
                "processing_time": result.get("processing_time"),
                "model_used": result.get("model_used")
            }
        }
    
    def _format_error(self, error_message: str) -> Dict[str, Any]:
        """Format error response for Gurukul consumption."""
        return {
            "success": False,
            "error": error_message,
            "response": "I apologize, but I'm unable to access the knowledge base at the moment. Please try again later.",
            "sources": [],
            "knowledge_base_results": 0,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "error_type": "api_error"
            }
        }
    
    async def health_check(self) -> bool:
        """Check if BHIV API is healthy."""
        try:
            if self.session:
                async with self.session.get(f"{self.bhiv_api_url}/health") as response:
                    return response.status == 200
            else:
                response = requests.get(f"{self.bhiv_api_url}/health", timeout=5)
                return response.status_code == 200
        except:
            return False


# ============================================================================
# GURUKUL INTEGRATION FUNCTIONS
# ============================================================================

# Sync wrapper for non-async Gurukul backends
def call_knowledge_base_sync(query: str, filters: Dict[str, Any] = None, user_id: str = "gurukul_user") -> Dict[str, Any]:
    """
    Synchronous wrapper for Gurukul backends that don't support async.
    
    Usage in Gurukul backend:
        from integrations.gurukul_backend_integration import call_knowledge_base_sync
        
        result = call_knowledge_base_sync("what is dharma", {"book": "rigveda"}, user_id)
        if result["success"]:
            return result["response"]
        else:
            return "Knowledge base unavailable"
    """
    client = GurukulKnowledgeBaseClient()
    
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(client.query_knowledge_base(query, filters, user_id))
        loop.close()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": "Knowledge base connection failed",
            "sources": [],
            "knowledge_base_results": 0
        }

# Async function for modern Gurukul backends
async def call_knowledge_base_async(query: str, filters: Dict[str, Any] = None, user_id: str = "gurukul_user") -> Dict[str, Any]:
    """
    Async function for modern Gurukul backends.
    
    Usage in async Gurukul backend:
        from integrations.gurukul_backend_integration import call_knowledge_base_async
        
        result = await call_knowledge_base_async("what is dharma", {"book": "rigveda"}, user_id)
        if result["success"]:
            return result["response"]
        else:
            return "Knowledge base unavailable"
    """
    async with GurukulKnowledgeBaseClient() as client:
        return await client.query_knowledge_base(query, filters, user_id)


# ============================================================================
# EXAMPLE USAGE FOR GURUKUL DEVELOPERS
# ============================================================================

async def example_gurukul_integration():
    """Example showing how to integrate with Gurukul system."""
    
    print("🏫 [GURUKUL] Example BHIV Knowledge Base Integration")
    
    # Initialize client
    async with GurukulKnowledgeBaseClient() as kb_client:
        
        # Check health
        if not await kb_client.health_check():
            print("❌ [ERROR] BHIV API is not available")
            return
        
        print("✅ [HEALTH] BHIV API is healthy")
        
        # Example 1: General knowledge query
        print("\n📚 [EXAMPLE 1] General knowledge query")
        result = await kb_client.query_knowledge_base("what is dharma", user_id="gurukul_student_123")
        print(f"Response: {result['response'][:100]}...")
        print(f"Sources: {len(result['sources'])} found")
        
        # Example 2: Ask the Vedas
        print("\n🕉️  [EXAMPLE 2] Ask the Vedas")
        result = await kb_client.ask_vedas("How should I live a righteous life?", user_id="gurukul_student_123")
        print(f"Vedic Wisdom: {result['response'][:100]}...")
        
        # Example 3: Search specific book
        print("\n📖 [EXAMPLE 3] Search in Rigveda")
        result = await kb_client.search_by_book("fire rituals", "rigveda", user_id="gurukul_student_123")
        print(f"Rigveda Results: {result['knowledge_base_results']} chunks found")
        
        # Example 4: Educational content
        print("\n🎓 [EXAMPLE 4] Educational content")
        result = await kb_client.get_educational_content("Sanskrit grammar", user_id="gurukul_student_123")
        print(f"Educational Content: {result['response'][:100]}...")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_gurukul_integration())
