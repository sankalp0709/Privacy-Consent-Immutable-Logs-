#!/usr/bin/env python3
"""
Gurukul Integration Bridge for Knowledge Base
Provides API bridge for Gurukul frontend/backend to access BHIV knowledge base.
"""

import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class GurukulKnowledgeBridge:
    """Bridge class for Gurukul to access BHIV knowledge base."""
    
    def __init__(self, bhiv_api_url: str = "http://localhost:8004"):
        self.bhiv_api_url = bhiv_api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Gurukul-Bridge/1.0'
        })
    
    def call_knowledge_base(self, query: str, filters: Optional[Dict[str, Any]] = None, 
                          user_id: str = "gurukul_user") -> Dict[str, Any]:
        """
        Main method for Gurukul to query the knowledge base.
        
        Args:
            query: Natural language query
            filters: Optional filters like {"book": "rigveda", "type": "artha"}
            user_id: User identifier from Gurukul
            
        Returns:
            Structured response with answer, sources, and metadata
        """
        try:
            # Prepare request payload
            payload = {
                "query": query,
                "user_id": f"gurukul_{user_id}",
                "filters": filters or {},
                "limit": 5
            }
            
            # Call BHIV knowledge base API
            response = self.session.post(
                f"{self.bhiv_api_url}/query-kb",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Format for Gurukul consumption
                return {
                    "success": True,
                    "answer": result.get("response", ""),
                    "sources": self._format_sources(result.get("sources", [])),
                    "confidence": self._calculate_confidence(result),
                    "query_id": result.get("query_id"),
                    "knowledge_base_results": result.get("knowledge_base_results", 0),
                    "response_time": result.get("response_time", 0),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "retriever_type": result.get("metadata", {}).get("retriever", "unknown"),
                        "enhanced_by_llm": not result.get("fallback", False),
                        "filters_applied": filters or {}
                    }
                }
            else:
                logger.error(f"BHIV API error: {response.status_code} - {response.text}")
                return self._error_response(f"API error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("Knowledge base query timeout")
            return self._error_response("Request timeout")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to BHIV API")
            return self._error_response("Service unavailable")
        except Exception as e:
            logger.error(f"Knowledge base query failed: {str(e)}")
            return self._error_response(str(e))
    
    def ask_vedas(self, question: str, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """Specialized method for Vedic wisdom queries."""
        try:
            payload = {
                "query": question,
                "user_id": f"gurukul_{user_id}"
            }
            
            response = self.session.post(
                f"{self.bhiv_api_url}/ask-vedas",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "wisdom": result.get("response", ""),
                    "sources": self._format_sources(result.get("sources", [])),
                    "query_id": result.get("query_id"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return self._error_response(f"Vedas API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ask Vedas failed: {str(e)}")
            return self._error_response(str(e))
    
    def get_educational_content(self, topic: str, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """Get educational content from the knowledge base."""
        try:
            payload = {
                "query": topic,
                "user_id": f"gurukul_{user_id}"
            }
            
            response = self.session.post(
                f"{self.bhiv_api_url}/edumentor",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "content": result.get("response", ""),
                    "sources": self._format_sources(result.get("sources", [])),
                    "query_id": result.get("query_id"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return self._error_response(f"Education API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Educational content failed: {str(e)}")
            return self._error_response(str(e))
    
    def search_by_book(self, query: str, book: str, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """Search within a specific Vedic book."""
        filters = {"book": book.lower()}
        return self.call_knowledge_base(query, filters, user_id)
    
    def search_by_type(self, query: str, content_type: str, user_id: str = "gurukul_user") -> Dict[str, Any]:
        """Search by content type (artha, dharma, kama, moksha)."""
        filters = {"type": content_type.lower()}
        return self.call_knowledge_base(query, filters, user_id)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Check if BHIV knowledge base is healthy and accessible."""
        try:
            response = self.session.get(f"{self.bhiv_api_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "healthy",
                    "bhiv_api": "accessible",
                    "uptime": health_data.get("uptime", 0),
                    "total_requests": health_data.get("total_requests", 0),
                    "success_rate": health_data.get("success_rate", 0),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "bhiv_api": "error",
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "bhiv_api": "unreachable",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _format_sources(self, sources: List[str]) -> List[Dict[str, str]]:
        """Format source list for Gurukul UI consumption."""
        formatted_sources = []
        for source in sources:
            # Extract filename and path info
            if isinstance(source, str):
                filename = source.split('\\')[-1] if '\\' in source else source.split('/')[-1]
                formatted_sources.append({
                    "filename": filename,
                    "full_path": source,
                    "type": self._detect_source_type(filename)
                })
        return formatted_sources
    
    def _detect_source_type(self, filename: str) -> str:
        """Detect source type from filename."""
        filename_lower = filename.lower()
        if any(book in filename_lower for book in ["rigveda", "samaveda", "yajurveda", "atharvaveda"]):
            return "veda"
        elif any(text in filename_lower for text in ["upanishad", "gita", "purana"]):
            return "scripture"
        elif "pdf" in filename_lower:
            return "document"
        else:
            return "text"
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score based on result metadata."""
        base_confidence = 0.5
        
        # Boost confidence if knowledge base found results
        kb_results = result.get("knowledge_base_results", 0)
        if kb_results > 0:
            base_confidence += 0.3
        
        # Boost if enhanced by LLM
        if not result.get("fallback", False):
            base_confidence += 0.2
        
        # Boost based on number of sources
        sources_count = len(result.get("sources", []))
        if sources_count > 0:
            base_confidence += min(0.2, sources_count * 0.05)
        
        return min(1.0, base_confidence)
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate standardized error response."""
        return {
            "success": False,
            "error": error_message,
            "answer": "I apologize, but I'm unable to process your request at the moment. Please try again later.",
            "sources": [],
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat()
        }


# Global instance for easy import
gurukul_bridge = GurukulKnowledgeBridge()


# Example usage functions for Gurukul backend integration
def ask_knowledge_base(query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Simple function for basic knowledge base queries."""
    return gurukul_bridge.call_knowledge_base(query, user_id=user_id)

def ask_vedas_wisdom(question: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Simple function for Vedic wisdom queries."""
    return gurukul_bridge.ask_vedas(question, user_id=user_id)

def search_rigveda(query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Search specifically in Rigveda."""
    return gurukul_bridge.search_by_book(query, "rigveda", user_id=user_id)

def search_upanishads(query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Search specifically in Upanishads."""
    return gurukul_bridge.search_by_book(query, "upanishads", user_id=user_id)

def get_dharma_guidance(query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Get dharma-related guidance."""
    return gurukul_bridge.search_by_type(query, "dharma", user_id=user_id)
