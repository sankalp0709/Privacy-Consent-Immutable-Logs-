#!/usr/bin/env python3
"""
Wellness Agent - Holistic Wellness Advisor
Provides comprehensive wellness and health guidance using RAG API and Groq enhancement.
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

class WellnessAgent:
    """Agent for providing holistic wellness and health guidance."""

    def __init__(self):
        self.name = "WellnessAgent"
        self.description = "Holistic wellness advisor providing health guidance"
        self.rl_context = RLContext()
        self.persona = "wellness_advisor"

        # Wellness keywords for context enhancement
        self.wellness_keywords = [
            "health", "wellness", "stress", "meditation", "yoga", "mindfulness",
            "nutrition", "exercise", "sleep", "mental health", "holistic",
            "balance", "energy", "healing", "prevention", "lifestyle"
        ]

        logger.info("✅ WellnessAgent initialized with RAG API and Groq enhancement")

    def _get_knowledge_context(self, query: str) -> tuple[str, list]:
        """Get relevant wellness knowledge from RAG API."""
        try:
            # Enhance query with wellness context
            enhanced_query = f"Wellness health guidance: {query}"

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

            logger.warning("⚠️ No wellness context retrieved from RAG API")
            return "", []

        except Exception as e:
            logger.error(f"❌ Error getting wellness context: {str(e)}")
            return "", []

    def _enhance_with_groq(self, query: str, knowledge_context: str = "") -> tuple[str, bool]:
        """Enhance response using Groq with wellness advisor persona."""
        try:
            # Build wellness guidance enhancement prompt
            prompt = f"""As a compassionate and knowledgeable wellness advisor, provide holistic health guidance for: "{query}"

{f'Wellness Knowledge Context: {knowledge_context}' if knowledge_context else 'Draw from holistic health principles and wellness best practices.'}

Please respond as a caring wellness advisor who:
- Takes a holistic approach to health and well-being
- Considers physical, mental, emotional, and spiritual aspects
- Provides practical, actionable advice
- Encourages sustainable lifestyle changes
- Promotes prevention and natural healing approaches
- Respects individual differences and circumstances

Your response should address:
- Immediate concerns and practical solutions
- Long-term wellness strategies
- Mind-body connection and stress management
- Lifestyle factors affecting health
- When to seek professional medical advice

Wellness Guidance:"""

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
        """Provide fallback wellness response when Groq is unavailable."""
        base_response = f"As your wellness advisor, I'm here to support your health journey regarding '{query}'. "

        if knowledge_context:
            base_response += f"Based on wellness principles: {knowledge_context[:500]}..."
        else:
            base_response += "Wellness is about nurturing your whole self - body, mind, and spirit."

        base_response += "\n\nRemember, small consistent steps lead to lasting wellness. Take care of yourself."
        return base_response

    def process_query(self, query: str, task_id: str = None) -> Dict[str, Any]:
        """Process a wellness guidance query."""
        task_id = task_id or str(uuid.uuid4())

        try:
            logger.info(f"🌿 WellnessAgent processing query: '{query[:100]}...'")

            # Step 1: Get wellness context from RAG API
            knowledge_context, sources = self._get_knowledge_context(query)

            # Step 2: Check if Vaani tools are needed
            vaani_used = False
            vaani_data = {}

            # Use Vaani for platform content if query mentions social media or sharing
            if any(platform in query.lower() for platform in ["twitter", "instagram", "linkedin", "social media", "post", "share", "community"]):
                logger.info("📱 Using Vaani for wellness platform content...")
                platforms = []
                if "twitter" in query.lower():
                    platforms.append("twitter")
                if "instagram" in query.lower():
                    platforms.append("instagram")
                if "linkedin" in query.lower():
                    platforms.append("linkedin")

                if not platforms:
                    platforms = ["instagram", "linkedin"]  # Wellness content works well on these

                platform_result = vaani_tools.generate_platform_content(
                    content=knowledge_context or query,
                    platforms=platforms,
                    tone="uplifting"
                )

                if platform_result.get("status") == "success":
                    vaani_used = True
                    vaani_data["platforms"] = platform_result

            # Use Vaani for multilingual wellness content
            if any(lang in query.lower() for lang in ["hindi", "sanskrit", "marathi", "gujarati", "tamil", "telugu", "kannada", "malayalam", "bengali"]):
                logger.info("🌐 Using Vaani for multilingual wellness content...")
                target_languages = []
                if "hindi" in query.lower():
                    target_languages.append("hi")
                if "sanskrit" in query.lower():
                    target_languages.append("sa")
                if "marathi" in query.lower():
                    target_languages.append("mr")

                if not target_languages:
                    target_languages = ["hi", "en"]

                multilingual_result = vaani_tools.generate_multilingual_content(
                    query=query,
                    target_languages=target_languages
                )

                if multilingual_result.get("status") == "success":
                    vaani_used = True
                    vaani_data["multilingual"] = multilingual_result

            # Use Vaani for voice content if query mentions meditation, relaxation, or audio
            if any(word in query.lower() for word in ["meditation", "relaxation", "voice", "audio", "guided", "breathing", "mantra"]):
                logger.info("🎵 Using Vaani for wellness voice content...")
                voice_result = vaani_tools.generate_voice_content(
                    content=knowledge_context or query,
                    language="hi",  # Hindi works well for wellness content
                    tone="devotional"  # Calming tone for wellness
                )

                if voice_result.get("status") == "success":
                    vaani_used = True
                    vaani_data["voice"] = voice_result

            # Use Vaani for content security analysis if query mentions sensitive wellness topics
            if any(word in query.lower() for word in ["mental health", "depression", "anxiety", "trauma", "sensitive", "private"]):
                logger.info("🔒 Using Vaani for wellness content security analysis...")
                security_result = vaani_tools.analyze_content_security(
                    content=knowledge_context or query
                )

                if security_result.get("status") == "success":
                    vaani_used = True
                    vaani_data["security"] = security_result

            # Step 3: Enhance with Groq using wellness advisor persona
            enhanced_response, groq_used = self._enhance_with_groq(query, knowledge_context)

            # Step 4: Log RL context
            self.rl_context.log_action(
                task_id=task_id,
                agent=self.name,
                model="groq" if groq_used else "fallback",
                action="wellness_guidance",
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
                    "wellness_keywords": [kw for kw in self.wellness_keywords if kw in query.lower()],
                    "guidance_type": "holistic_wellness",
                    "enhancement_method": "groq" if groq_used else "fallback",
                    "vaani_features_used": list(vaani_data.keys()) if vaani_used else []
                }
            }

            logger.info(f"✅ WellnessAgent completed processing for task {task_id}")
            return response_data

        except Exception as e:
            logger.error(f"❌ WellnessAgent error: {str(e)}")

            # Return error response
            return {
                "response": "I apologize, but I'm experiencing difficulties providing wellness guidance at this moment. Please try again later.",
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run(self, input_path: str, live_feed: str = "", model: str = "wellness_agent",
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