#!/usr/bin/env python3
"""
RAG API Client
Client for the external RAG API that provides knowledge base retrieval and Groq answers.
"""

import requests
import json
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from config.settings import RAG_CONFIG

logger = get_logger(__name__)

class RAGClient:
    """Client for external RAG API integration."""

    def __init__(self, api_url: str = None):
        self.api_url = api_url or RAG_CONFIG["api_url"]
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BHIV-Core-RAG-Client/1.0'
        })

    def query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query the RAG API for knowledge base retrieval.

        Args:
            query: The search query
            top_k: Number of top results to retrieve

        Returns:
            Dictionary containing retrieved_chunks and groq_answer
        """
        try:
            payload = {
                "query": query,
                "top_k": top_k
            }

            logger.info(f"🔍 Querying RAG API: '{query[:100]}...'")

            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=RAG_CONFIG["timeout"]
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ RAG API returned {len(result.get('retrieved_chunks', []))} chunks")

                # Transform the response to match our expected format
                return self._transform_response(result, query)
            else:
                logger.error(f"❌ RAG API error: {response.status_code} - {response.text}")
                return self._create_fallback_response(query, top_k)

        except Exception as e:
            logger.error(f"❌ Error querying RAG API: {str(e)}")
            return self._create_fallback_response(query, top_k)

    def _transform_response(self, api_response: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Transform RAG API response to our internal format."""
        retrieved_chunks = api_response.get('retrieved_chunks', [])
        groq_answer = api_response.get('groq_answer', '')

        # Transform chunks to our expected format
        transformed_chunks = []
        for chunk in retrieved_chunks:
            transformed_chunks.append({
                "content": chunk.get("content", ""),
                "source": f"rag:{chunk.get('file', 'unknown')}",
                "score": float(chunk.get("score", 0.0)),
                "metadata": {
                    "file": chunk.get("file", ""),
                    "index": chunk.get("index", 0),
                    "rag_source": "external_api"
                },
                "document_id": f"{chunk.get('file', 'unknown')}_{chunk.get('index', 0)}",
                "folder": "rag_api"
            })

        return {
            "response": transformed_chunks,
            "groq_answer": groq_answer,
            "method": "rag_api",
            "total_results": len(transformed_chunks),
            "status": 200,
            "timestamp": api_response.get("timestamp", ""),
            "query": original_query,
            "metadata": {
                "tags": ["semantic_search", "rag_api", "groq_enhanced"],
                "retriever": "external_rag_api",
                "total_results": len(transformed_chunks),
                "has_groq_answer": bool(groq_answer)
            }
        }

    def _create_fallback_response(self, query: str, top_k: int) -> Dict[str, Any]:
        """Create a fallback response when RAG API is unavailable."""
        logger.warning("🆘 Creating fallback response for RAG API")

        return {
            "response": [{
                "content": f"I apologize, but I'm currently unable to access the knowledge base. Your query was: '{query}'",
                "source": "fallback:error",
                "score": 0.1,
                "metadata": {"error": "RAG API unavailable"},
                "document_id": "fallback-001",
                "folder": "fallback"
            }],
            "groq_answer": f"I apologize, but I'm currently unable to access the knowledge base to provide a comprehensive answer to your query: '{query}'. Please try again later.",
            "method": "fallback",
            "total_results": 1,
            "status": 503,
            "timestamp": "",
            "query": query,
            "metadata": {
                "tags": ["fallback", "error"],
                "retriever": "none",
                "total_results": 1,
                "error": "RAG API unavailable"
            }
        }

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the RAG API."""
        try:
            # Simple health check with a test query
            test_response = self.query("test", top_k=1)
            return {
                "status": "healthy" if test_response["status"] == 200 else "unhealthy",
                "response_time": "ok",
                "api_url": self.api_url
            }
        except Exception as e:
            logger.error(f"❌ RAG API health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_url": self.api_url
            }

# Global RAG client instance
rag_client = RAGClient()