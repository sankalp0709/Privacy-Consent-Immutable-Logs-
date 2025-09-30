#!/usr/bin/env python3
"""
Summarizer Agent - Text Summarization Specialist
Provides intelligent text summarization with multiple strategies and formats.
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

class SummarizerAgent:
    """Agent specialized in text summarization with multiple strategies."""

    def __init__(self):
        self.name = "SummarizerAgent"
        self.description = "Intelligent text summarization with multiple strategies"
        self.rl_context = RLContext()
        self.persona = "summarization_expert"

        # Summarization keywords
        self.summary_keywords = [
            "summarize", "summary", "summarise", "condense", "abstract",
            "overview", "recap", "brief", "shorten", "digest", "key points"
        ]

        logger.info("✅ SummarizerAgent initialized with RAG API and Groq enhancement")

    def _get_knowledge_context(self, query: str) -> str:
        """Get relevant knowledge from RAG API for summarization context."""
        try:
            # Enhance query with summarization context
            enhanced_query = f"Summarization techniques and best practices: {query}"

            # Query RAG API
            response = rag_client.query(enhanced_query, top_k=3)

            if response.get("status") == "success" and response.get("results"):
                # Combine relevant results
                contexts = []
                for result in response["results"][:2]:  # Top 2 results
                    if isinstance(result, dict) and "content" in result:
                        contexts.append(result["content"])

                return " ".join(contexts) if contexts else ""

            logger.warning("⚠️ No summarization context retrieved from RAG API")
            return ""

        except Exception as e:
            logger.error(f"❌ Error getting summarization context: {str(e)}")
            return ""

    def _enhance_with_groq(self, query: str, knowledge_context: str = "") -> tuple[str, bool]:
        """Enhance response using Groq with summarization expertise."""
        try:
            # Build summarization enhancement prompt
            prompt = f"""As an expert summarizer and content strategist, provide a comprehensive yet concise summary of: "{query}"

{f'Relevant Context: {knowledge_context}' if knowledge_context else 'Apply proven summarization techniques and best practices.'}

Please respond as a professional summarizer who:
- Identifies the most important information and key points
- Maintains the original meaning while reducing length
- Uses clear, concise language
- Structures information logically
- Preserves critical details and context
- Creates summaries appropriate for the intended audience

Your summary should include:
- Main ideas and key concepts
- Important details and supporting evidence
- Logical flow and structure
- Appropriate level of detail for the content type

Summary:"""

            response, success = groq_client.generate_response(prompt, max_tokens=1000, temperature=0.6)

            if success and response:
                return response, True
            else:
                logger.warning("⚠️ Groq enhancement failed, using fallback")
                return self._fallback_summary(query, knowledge_context), False

        except Exception as e:
            logger.error(f"❌ Groq enhancement error: {str(e)}")
            return self._fallback_summary(query, knowledge_context), False

    def _fallback_summary(self, query: str, knowledge_context: str = "") -> str:
        """Provide fallback summarization when Groq is unavailable."""
        base_response = f"Summary of '{query}':\n\n"

        if knowledge_context:
            # Extract key sentences from context
            sentences = knowledge_context.split('.')
            key_sentences = []
            for sentence in sentences[:5]:  # Take first 5 sentences
                sentence = sentence.strip()
                if sentence and len(sentence) > 20:  # Filter meaningful sentences
                    key_sentences.append(sentence)

            if key_sentences:
                base_response += "Key points:\n" + "\n".join(f"• {s}" for s in key_sentences[:3])
            else:
                base_response += "This content requires detailed analysis for effective summarization."
        else:
            base_response += "This appears to be a request for content summarization. Please provide the text to be summarized."

        return base_response

    def _detect_summary_type(self, query: str) -> str:
        """Detect the type of summary requested."""
        query_lower = query.lower()

        if any(word in query_lower for word in ["executive", "brief", "high-level"]):
            return "executive"
        elif any(word in query_lower for word in ["detailed", "comprehensive", "thorough"]):
            return "detailed"
        elif any(word in query_lower for word in ["bullet", "points", "list"]):
            return "bullet_points"
        elif any(word in query_lower for word in ["key", "main", "important"]):
            return "key_points"
        else:
            return "general"

    def process_query(self, query: str, task_id: str = None) -> Dict[str, Any]:
        """Process a summarization query."""
        task_id = task_id or str(uuid.uuid4())
        agent_logs = []
        processing_details = {}

        try:
            agent_logs.append(f"📝 SummarizerAgent processing query: '{query[:100]}...'")
            logger.info(f"📝 SummarizerAgent processing query: '{query[:100]}...'")

            # Detect summary type
            summary_type = self._detect_summary_type(query)
            agent_logs.append(f"🎯 Detected summary type: {summary_type}")
            processing_details["summary_type"] = summary_type

            # Step 1: Get knowledge context from RAG API
            agent_logs.append("🔍 Retrieving knowledge context from RAG API...")
            knowledge_context = self._get_knowledge_context(query)
            context_length = len(knowledge_context) if knowledge_context else 0
            agent_logs.append(f"📚 Retrieved {context_length} characters of context")
            processing_details["knowledge_context_length"] = context_length

            # Step 2: Enhance with Groq using summarization expertise
            agent_logs.append("🤖 Enhancing with Groq summarization expertise...")
            enhanced_response, groq_used = self._enhance_with_groq(query, knowledge_context)
            agent_logs.append(f"✨ Groq enhancement: {'successful' if groq_used else 'fallback used'}")
            processing_details["groq_enhanced"] = groq_used

            # Step 3: Log RL context
            self.rl_context.log_action(
                task_id=task_id,
                agent=self.name,
                model="groq" if groq_used else "fallback",
                action="text_summarization",
                metadata={
                    "query": query,
                    "summary_type": summary_type,
                    "knowledge_retrieved": bool(knowledge_context),
                    "groq_enhanced": groq_used,
                    "persona": self.persona
                }
            )
            agent_logs.append("📊 RL context logged")

            # Step 4: Prepare response
            response_data = {
                "response": enhanced_response,
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "persona": self.persona,
                "summary_type": summary_type,
                "knowledge_context_used": bool(knowledge_context),
                "groq_enhanced": groq_used,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "agent_logs": agent_logs,
                "processing_details": processing_details,
                "metadata": {
                    "summary_keywords": [kw for kw in self.summary_keywords if kw in query.lower()],
                    "processing_type": "text_summarization",
                    "enhancement_method": "groq" if groq_used else "fallback",
                    "estimated_compression_ratio": "70-80%"  # Typical summarization ratio
                }
            }

            agent_logs.append(f"✅ SummarizerAgent completed processing for task {task_id}")
            logger.info(f"✅ SummarizerAgent completed processing for task {task_id}")
            return response_data

        except Exception as e:
            error_msg = f"❌ SummarizerAgent error: {str(e)}"
            agent_logs.append(error_msg)
            logger.error(error_msg)

            # Return error response
            return {
                "response": "I apologize, but I'm experiencing difficulties creating a summary at this moment. Please try again later.",
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "agent_logs": agent_logs,
                "processing_details": processing_details,
                "timestamp": datetime.now().isoformat()
            }

    def run(self, input_path: str, live_feed: str = "", model: str = "summarizer_agent",
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