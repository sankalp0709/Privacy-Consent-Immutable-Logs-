#!/usr/bin/env python3
"""
Text Agent - General Text Processor
Provides general text processing and analysis using RAG API and Groq enhancement.
"""

import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from utils.rag_client import rag_client
from utils.groq_client import groq_client
from reinforcement.rl_context import RLContext

logger = get_logger(__name__)

class TextAgent:
    """Agent for general text processing and analysis."""

    def __init__(self):
        self.name = "TextAgent"
        self.description = "General text processing with RAG API and Groq enhancement"
        self.rl_context = RLContext()
        self.persona = "text_processor"

        # Text processing keywords
        self.text_keywords = [
            "analyze", "summarize", "explain", "describe", "process",
            "text", "content", "information", "data", "document"
        ]

        logger.info("✅ TextAgent initialized with RAG API and Groq enhancement")

    def _get_knowledge_context(self, query: str) -> str:
        """Get relevant knowledge from RAG API for text processing."""
        try:
            # Enhance query with text processing context
            enhanced_query = f"Text processing analysis: {query}"

            # Query RAG API
            response = rag_client.query(enhanced_query, top_k=5)

            if response.get("status") == "success" and response.get("results"):
                # Combine relevant results
                contexts = []
                for result in response["results"][:3]:  # Top 3 results
                    if isinstance(result, dict) and "content" in result:
                        contexts.append(result["content"])

                return " ".join(contexts) if contexts else ""

            logger.warning("⚠️ No text processing context retrieved from RAG API")
            return ""

        except Exception as e:
            logger.error(f"❌ Error getting text processing context: {str(e)}")
            return ""

    def _enhance_with_groq(self, query: str, knowledge_context: str = "") -> tuple[str, bool]:
        """Enhance response using Groq with text processing persona."""
        try:
            # Build text processing enhancement prompt
            prompt = f"""As a skilled text processor and content analyst, provide comprehensive analysis and processing for: "{query}"

{f'Relevant Context: {knowledge_context}' if knowledge_context else 'Draw from general knowledge and text processing best practices.'}

Please respond as a professional text analyst who:
- Provides clear, structured analysis
- Identifies key themes and concepts
- Offers practical insights and applications
- Uses appropriate analytical frameworks
- Maintains objectivity and accuracy
- Provides actionable recommendations

Your analysis should include:
- Main concepts and themes
- Key insights and implications
- Practical applications or recommendations
- Clear structure and organization

Text Analysis:"""

            response, success = groq_client.generate_response(prompt, max_tokens=1200, temperature=0.7)

            if success and response:
                return response, True
            else:
                logger.warning("⚠️ Groq enhancement failed, using fallback")
                return self._fallback_response(query, knowledge_context), False

        except Exception as e:
            logger.error(f"❌ Groq enhancement error: {str(e)}")
            return self._fallback_response(query, knowledge_context), False

    def _fallback_response(self, query: str, knowledge_context: str = "") -> str:
        """Provide fallback text processing response when Groq is unavailable."""
        base_response = f"As a text processor, I'll help you analyze '{query}'. "

        if knowledge_context:
            base_response += f"Based on available information: {knowledge_context[:500]}..."
        else:
            base_response += "I'll provide a structured analysis of the content."

        base_response += "\n\nThis appears to be a request for text processing and analysis."
        return base_response

    def process_query(self, query: str, task_id: str = None) -> Dict[str, Any]:
        """Process a text analysis query."""
        task_id = task_id or str(uuid.uuid4())

        try:
            logger.info(f"📄 TextAgent processing query: '{query[:100]}...'")

            # Step 1: Get knowledge context from RAG API
            knowledge_context = self._get_knowledge_context(query)

            # Step 2: Enhance with Groq using text processing persona
            enhanced_response, groq_used = self._enhance_with_groq(query, knowledge_context)

            # Step 3: Log RL context
            self.rl_context.log_action(
                task_id=task_id,
                agent=self.name,
                model="groq" if groq_used else "fallback",
                action="text_processing",
                metadata={
                    "query": query,
                    "knowledge_retrieved": bool(knowledge_context),
                    "groq_enhanced": groq_used,
                    "persona": self.persona
                }
            )

            # Step 4: Prepare response
            response_data = {
                "response": enhanced_response,
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "persona": self.persona,
                "knowledge_context_used": bool(knowledge_context),
                "groq_enhanced": groq_used,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "metadata": {
                    "text_keywords": [kw for kw in self.text_keywords if kw in query.lower()],
                    "processing_type": "general_text_analysis",
                    "enhancement_method": "groq" if groq_used else "fallback"
                }
            }

            logger.info(f"✅ TextAgent completed processing for task {task_id}")
            return response_data

        except Exception as e:
            logger.error(f"❌ TextAgent error: {str(e)}")

            # Return error response
            return {
                "response": "I apologize, but I'm experiencing difficulties processing your text request at this moment. Please try again later.",
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run(self, input_path: str, live_feed: str = "", model: str = "text_agent",
            input_type: str = "text", task_id: str = None) -> Dict[str, Any]:
        """Main entry point for agent execution - compatible with existing interface."""
        return self.process_query(input_path, task_id)

    def health_check(self) -> Dict[str, Any]:
        """Check agent health and dependencies."""
        health_status = {
            "agent": self.name,
            "status": "healthy",
            "rag_api_available": False,
            "groq_api_available": False,
            "timestamp": datetime.now().isoformat()
        }

        # Check RAG API
        try:
            rag_health = rag_client.health_check()
            health_status["rag_api_available"] = rag_health.get("available", False)
        except Exception as e:
            logger.warning(f"RAG API health check failed: {e}")

        # Check Groq API
        try:
            groq_health = groq_client.health_check()
            health_status["groq_api_available"] = groq_health.get("available", False)
        except Exception as e:
            logger.warning(f"Groq API health check failed: {e}")

        # Overall status
        if not health_status["rag_api_available"] and not health_status["groq_api_available"]:
            health_status["status"] = "degraded"
        elif not health_status["rag_api_available"] or not health_status["groq_api_available"]:
            health_status["status"] = "partial"

        return health_status