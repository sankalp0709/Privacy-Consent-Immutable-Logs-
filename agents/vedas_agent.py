#!/usr/bin/env python3
"""
Vedas Agent - Spiritual Wisdom Guide
Provides spiritual guidance and wisdom from Vedic texts using RAG API and Groq enhancement.
"""

import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from utils.rag_client import rag_client
from utils.groq_client import groq_client
from utils.vaani_tools import vaani_tools
from reinforcement.rl_context import RLContext

logger = get_logger(__name__)

class VedasAgent:
    """Agent for providing spiritual wisdom and Vedic guidance."""

    def __init__(self):
        self.name = "VedasAgent"
        self.description = "Spiritual wisdom guide drawing from Vedic texts"
        self.rl_context = RLContext()
        self.persona = "vedic_wisdom"

        # Vedic wisdom keywords for context enhancement
        self.vedic_keywords = [
            "dharma", "karma", "bhakti", "jnana", "yoga", "meditation",
            "vedas", "upanishads", "bhagavad-gita", "spirituality", "consciousness",
            "self-realization", "moksha", "samsara", "maya", "atman", "brahman"
        ]

        logger.info("✅ VedasAgent initialized with RAG API and Groq enhancement")

    def _get_knowledge_context(self, query: str) -> tuple[str, list]:
        """Get relevant knowledge from RAG API."""
        try:
            # Enhance query with Vedic context
            enhanced_query = f"Vedic wisdom spiritual guidance: {query}"

            # Query RAG API
            response = rag_client.query(enhanced_query, top_k=5)

            if response.get("status") == 200 and response.get("response"):
                # Combine relevant results for context
                contexts = []
                sources = []
                for result in response["response"][:3]:  # Top 3 results
                    if isinstance(result, dict) and "content" in result:
                        contexts.append(result["content"])
                        sources.append({
                            "content": result["content"][:200] + "...",  # Preview
                            "source": result.get("source", "unknown"),
                            "score": result.get("score", 0.0),
                            "document_id": result.get("document_id", ""),
                            "folder": result.get("folder", "rag_api")
                        })

                context_text = " ".join(contexts) if contexts else ""
                return context_text, sources

            logger.warning("⚠️ No knowledge context retrieved from RAG API")
            return "", []

        except Exception as e:
            logger.error(f"❌ Error getting knowledge context: {str(e)}")
            return "", []

    def _enhance_with_groq(self, query: str, knowledge_context: str = "") -> tuple[str, bool]:
        """Enhance response using Groq with Vedic wisdom persona."""
        try:
            # Build Vedic wisdom enhancement prompt
            prompt = f"""As a spiritual guide drawing from ancient Vedic wisdom, Bhagavad Gita, and Upanishads, provide a compassionate and insightful response to: "{query}"

{f'Knowledge Context from Vedic texts: {knowledge_context}' if knowledge_context else 'Draw from universal spiritual principles and Vedic teachings.'}

Please respond as a wise spiritual mentor who:
- Speaks with compassion and understanding
- References appropriate Vedic principles when relevant
- Provides practical spiritual guidance
- Maintains cultural sensitivity and respect
- Offers wisdom that promotes inner peace and self-realization
- Uses traditional spiritual terminology appropriately

Your response should be:
- Spiritually uplifting and encouraging
- Grounded in timeless wisdom
- Helpful for personal growth and understanding
- Respectful of all spiritual paths

Spiritual Guidance:"""

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
        """Provide fallback response when Groq is unavailable."""
        base_response = f"As a spiritual guide, I understand you're seeking wisdom about '{query}'. "

        if knowledge_context:
            base_response += f"Based on spiritual teachings: {knowledge_context[:500]}..."
        else:
            base_response += "The path to spiritual understanding involves self-reflection, compassion, and connecting with deeper truths."

        base_response += "\n\nMay you find the peace and wisdom you seek on your spiritual journey."
        return base_response

    def process_query(self, query: str, task_id: str = None) -> Dict[str, Any]:
        """Process a spiritual guidance query."""
        task_id = task_id or str(uuid.uuid4())

        try:
            logger.info(f"🕉️ VedasAgent processing query: '{query[:100]}...'")

            # Step 1: Get knowledge context from RAG API
            knowledge_context, sources = self._get_knowledge_context(query)

            # Step 2: Check if Vaani tools are needed
            vaani_used = False
            vaani_data = {}

            # Use Vaani for multilingual content if query mentions specific languages
            if any(lang in query.lower() for lang in ["hindi", "sanskrit", "marathi", "gujarati", "tamil", "telugu", "kannada", "malayalam", "bengali"]):
                logger.info("🌐 Using Vaani for multilingual spiritual content...")
                target_languages = []
                if "hindi" in query.lower():
                    target_languages.append("hi")
                if "sanskrit" in query.lower():
                    target_languages.append("sa")
                if "marathi" in query.lower():
                    target_languages.append("mr")

                if not target_languages:
                    target_languages = ["hi", "sa"]  # Default to Hindi and Sanskrit

                vaani_result = vaani_tools.generate_multilingual_content(
                    query=query,
                    target_languages=target_languages
                )

                if vaani_result.get("status") == "success":
                    vaani_used = True
                    vaani_data["multilingual"] = vaani_result

            # Use Vaani for voice content if query mentions audio/speech
            if any(word in query.lower() for word in ["voice", "audio", "speak", "pronounce", "chant", "mantra"]):
                logger.info("🎵 Using Vaani for voice content generation...")
                voice_result = vaani_tools.generate_voice_content(
                    content=knowledge_context or query,
                    language="hi",  # Default to Hindi for spiritual content
                    tone="devotional"
                )

                if voice_result.get("status") == "success":
                    vaani_used = True
                    vaani_data["voice"] = voice_result

            # Step 3: Enhance with Groq using Vedic wisdom persona
            enhanced_response, groq_used = self._enhance_with_groq(query, knowledge_context)

            # Step 4: Log RL context
            self.rl_context.log_action(
                task_id=task_id,
                agent=self.name,
                model="groq" if groq_used else "fallback",
                action="spiritual_guidance",
                metadata={
                    "query": query,
                    "knowledge_retrieved": bool(knowledge_context),
                    "groq_enhanced": groq_used,
                    "vaani_used": vaani_used,
                    "persona": self.persona,
                    "sources_count": len(sources)
                }
            )

            # Step 5: Prepare response with detailed sources and Vaani data
            response_data = {
                "response": enhanced_response,
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "persona": self.persona,
                "knowledge_context_used": bool(knowledge_context),
                "groq_enhanced": groq_used,
                "vaani_enhanced": vaani_used,
                "sources": sources,  # Include detailed source information
                "rag_data": {
                    "total_sources": len(sources),
                    "method": "rag_api_enhanced",
                    "knowledge_context_length": len(knowledge_context),
                    "has_groq_answer": groq_used
                },
                "vaani_data": vaani_data if vaani_used else None,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "metadata": {
                    "spiritual_keywords": [kw for kw in self.vedic_keywords if kw in query.lower()],
                    "guidance_type": "vedic_wisdom",
                    "enhancement_method": "groq" if groq_used else "fallback",
                    "vaani_features_used": list(vaani_data.keys()) if vaani_used else []
                }
            }

            logger.info(f"✅ VedasAgent completed processing for task {task_id} with {len(sources)} sources{' and Vaani tools' if vaani_used else ''}")
            return response_data

        except Exception as e:
            logger.error(f"❌ VedasAgent error: {str(e)}")

            # Return error response
            return {
                "response": "I apologize, but I'm experiencing difficulties providing spiritual guidance at this moment. Please try again later.",
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "sources": [],
                "rag_data": {"total_sources": 0, "method": "error", "error": str(e)},
                "vaani_data": None,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run(self, input_path: str, live_feed: str = "", model: str = "vedas_agent",
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