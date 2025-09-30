#!/usr/bin/env python3
"""
Q&A Agent - Question and Answer Specialist
Provides intelligent Q&A capabilities with knowledge retrieval and conversational responses.
"""

import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import get_logger
from utils.rag_client import rag_client
from utils.groq_client import groq_client
from utils.vaani_client import VaaniClient
from agents.KnowledgeAgent import KnowledgeAgent
from reinforcement.rl_context import RLContext

logger = get_logger(__name__)

class QnAAgent:
    """Agent specialized in question answering with knowledge base integration."""

    def __init__(self):
        self.name = "QnAAgent"
        self.description = "Intelligent question answering with knowledge retrieval"
        self.rl_context = RLContext()
        self.persona = "knowledgeable_assistant"

        # Initialize KnowledgeAgent for core functionality
        self.knowledge_agent = KnowledgeAgent()

        # Initialize Vaani client for content generation
        try:
            self.vaani_client = VaaniClient()
            self.vaani_available = True
        except Exception as e:
            logger.warning(f"Vaani client not available: {e}")
            self.vaani_client = None
            self.vaani_available = False

        # Q&A keywords
        self.qna_keywords = [
            "what", "how", "why", "when", "where", "who", "which",
            "explain", "describe", "tell me", "question", "answer",
            "help", "assist", "clarify", "understand"
        ]

        logger.info("✅ QnAAgent initialized with KnowledgeAgent, Groq enhancement, and Vaani integration")

    def _get_knowledge_context(self, query: str) -> str:
        """Get relevant knowledge from RAG API for Q&A context."""
        try:
            # Enhance query with Q&A context
            enhanced_query = f"Question answering and knowledge retrieval: {query}"

            # Query RAG API
            response = rag_client.query(enhanced_query, top_k=3)

            if response.get("status") == "success" and response.get("results"):
                # Combine relevant results
                contexts = []
                for result in response["results"][:2]:  # Top 2 results
                    if isinstance(result, dict) and "content" in result:
                        contexts.append(result["content"])

                return " ".join(contexts) if contexts else ""

            logger.warning("⚠️ No Q&A context retrieved from RAG API")
            return ""

        except Exception as e:
            logger.error(f"❌ Error getting Q&A context: {str(e)}")
            return ""

    def _enhance_with_groq(self, query: str, kb_response: str,
                           knowledge_context: str = "", agent_filter: str = None) -> tuple[str, bool]:
        """Enhance Q&A response using Groq with conversational expertise."""
        try:
            # Agent-specific persona and response style
            agent_personas = {
                "vedas_agent": {
                    "role": "Vedas scholar and spiritual guide",
                    "style": "spiritual wisdom, scriptural references, moral teachings",
                    "focus": "Provide answers rooted in Vedic principles, Hindu philosophy, and spiritual growth. Reference relevant scriptures and explain concepts through the lens of dharma, karma, and moksha."
                },
                "wellness_agent": {
                    "role": "holistic wellness expert",
                    "style": "compassionate guidance, practical advice, mind-body-spirit balance",
                    "focus": "Provide wellness-focused answers that promote physical, mental, and spiritual health. Include yoga, meditation, Ayurveda, and holistic healing approaches."
                },
                "edumentor_agent": {
                    "role": "educational mentor and learning specialist",
                    "style": "encouraging teacher, clear explanations, learning-focused",
                    "focus": "Provide educational answers that promote learning, critical thinking, and academic growth. Include teaching strategies and learning methodologies."
                },
                "knowledge_agent": {
                    "role": "knowledge specialist and information expert",
                    "style": "comprehensive researcher, factual accuracy, thorough analysis",
                    "focus": "Provide detailed, well-researched answers with comprehensive information and multiple perspectives."
                }
            }

            # Get agent-specific configuration
            agent_config = agent_personas.get(agent_filter, {
                "role": "knowledgeable assistant and subject matter expert",
                "style": "helpful, accurate, comprehensive",
                "focus": "Provide clear, accurate, and comprehensive answers with evidence and reasoning."
            })

            # Build agent-specific Q&A enhancement prompt
            prompt = f"""As a {agent_config['role']}, provide a comprehensive and accurate answer to: "{query}"

Knowledge Base Information:
{kb_response}

{f'Additional Context: {knowledge_context}' if knowledge_context else 'Use your expertise to provide complete and accurate information.'}

Please respond in a {agent_config['style']} manner. {agent_config['focus']}

Your answer should include:
- Direct response to the question
- Supporting details and explanations
- Context and background information when helpful
- Clear structure and organization
- Suggestions for further exploration if relevant

Answer:"""

            response, success = groq_client.generate_response(prompt, max_tokens=1200, temperature=0.7)

            if success and response:
                return response, True
            else:
                logger.warning("⚠️ Groq enhancement failed, using knowledge base response")
                return kb_response, False

        except Exception as e:
            logger.error(f"❌ Groq enhancement error: {str(e)}")
            return kb_response, False

    def _detect_question_type(self, query: str) -> str:
        """Detect the type of question being asked."""
        query_lower = query.lower()

        # Wh- questions
        if query_lower.startswith("what"):
            return "factual_definition"
        elif query_lower.startswith("how"):
            return "process_explanation"
        elif query_lower.startswith("why"):
            return "causal_explanation"
        elif query_lower.startswith("when"):
            return "temporal_information"
        elif query_lower.startswith("where"):
            return "location_information"
        elif query_lower.startswith("who"):
            return "person_entity"
        elif query_lower.startswith("which"):
            return "selection_choice"

        # Other question types
        elif any(word in query_lower for word in ["explain", "describe", "elaborate"]):
            return "explanatory"
        elif any(word in query_lower for word in ["compare", "contrast", "difference"]):
            return "comparative"
        elif any(word in query_lower for word in ["advantages", "benefits", "pros", "cons"]):
            return "evaluative"
        else:
            return "general_inquiry"

    def _format_follow_up_questions(self, query: str, question_type: str) -> List[str]:
        """Generate relevant follow-up questions based on the query type."""
        follow_ups = []

        if question_type == "factual_definition":
            follow_ups = [
                "Can you provide more details about this topic?",
                "What are some related concepts I should know about?",
                "How is this used in practice?"
            ]
        elif question_type == "process_explanation":
            follow_ups = [
                "What are the key steps involved?",
                "Are there any prerequisites I need to know?",
                "What tools or resources would help with this?"
            ]
        elif question_type == "causal_explanation":
            follow_ups = [
                "What factors contribute to this?",
                "What are the implications of this?",
                "How can this be prevented or improved?"
            ]
        else:
            follow_ups = [
                "Can you clarify this further?",
                "Do you have any examples?",
                "Is there anything else I should know?"
            ]

        return follow_ups[:2]  # Return top 2 follow-ups

    def process_query(self, query: str, task_id: str = None, agent_filter: str = None) -> Dict[str, Any]:
        """Process a Q&A query."""
        task_id = task_id or str(uuid.uuid4())

        try:
            logger.info(f"❓ QnAAgent processing query: '{query[:100]}...'")

            # Detect question type
            question_type = self._detect_question_type(query)

            # Step 1: Get knowledge base response using KnowledgeAgent with agent filtering
            kb_result = self.knowledge_agent.query(query, top_k=5, agent_filter=agent_filter)

            # Extract sources for detailed response
            sources = []
            if kb_result.get("status") == 200 and kb_result.get("response"):
                kb_response = " ".join(kb_result["response"]) if isinstance(kb_result["response"], list) else kb_result["response"]

                # Build sources array from kb_result with proper document info
                if isinstance(kb_result.get("response"), list):
                    kb_sources = kb_result.get("sources", [])
                    for i, content in enumerate(kb_result["response"]):
                        # Extract document name from source if available
                        source_info = kb_sources[i] if i < len(kb_sources) else f"{kb_result.get('method', 'knowledge_base')}_doc_{i}"
                        document_name = source_info.split(":")[-1] if ":" in source_info else source_info

                        sources.append({
                            "content": content[:500] + "..." if len(content) > 500 else content,
                            "source": f"rag:{document_name}",
                            "score": kb_result.get("total_results", 0) / (i + 1),  # Approximate score
                            "document_id": f"{document_name}_{i+1}",
                            "folder": kb_result.get("method", "rag_api")
                        })
            else:
                kb_response = "I don't have specific information about this topic in my knowledge base."

            # Step 2: Get additional knowledge context from RAG API
            knowledge_context = self._get_knowledge_context(query)

            # Step 3: Enhance with Groq using agent-specific expertise
            enhanced_response, groq_used = self._enhance_with_groq(query, kb_response, knowledge_context, agent_filter)

            # Step 4: Generate follow-up questions
            follow_up_questions = self._format_follow_up_questions(query, question_type)

            # Step 5: Generate Vaani content for social media
            vaani_data = {}
            vaani_enhanced = False
            if self.vaani_available and self.vaani_client:
                try:
                    # Generate content for Twitter and Instagram
                    platforms = ["twitter", "instagram"]
                    vaani_result = self.vaani_client.generate_content(
                        text=enhanced_response[:500],  # Limit text length
                        platforms=platforms,
                        tone="neutral",
                        language="en"
                    )

                    if vaani_result.get("generated_content"):
                        vaani_data = {
                            "platforms": platforms,
                            "platform_content": vaani_result["generated_content"]
                        }
                        vaani_enhanced = True
                        logger.info("✅ Vaani content generated for social media platforms")
                    else:
                        logger.warning("⚠️ Vaani content generation returned empty result")
                except Exception as e:
                    logger.warning(f"⚠️ Vaani content generation failed: {str(e)}")

            # Step 6: Log RL context and get agent selection logs
            rl_action_result = self.rl_context.log_action(
                task_id=task_id,
                agent=self.name,
                model="groq" if groq_used else "knowledge_base",
                action="question_answering",
                metadata={
                    "query": query,
                    "question_type": question_type,
                    "knowledge_retrieved": bool(kb_response and kb_response != "I don't have specific information about this topic in my knowledge base."),
                    "groq_enhanced": groq_used,
                    "vaani_enhanced": vaani_enhanced,
                    "follow_ups_generated": len(follow_up_questions),
                    "persona": self.persona
                }
            )

            # Get recent RL logs for this task
            rl_logs = []
            try:
                # Get recent RL actions for this task_id from in-memory storage
                recent_actions = [action for action in self.rl_context.actions
                                if action.get("task_id") == task_id][-5:]  # Last 5 actions for this task

                rl_logs = [{
                    "timestamp": action.get("timestamp"),
                    "agent": action.get("agent"),
                    "action": action.get("action"),
                    "details": action.get("metadata", {})
                } for action in recent_actions]

            except Exception as e:
                logger.warning(f"Could not retrieve RL logs: {e}")
                rl_logs = []

            # Step 7: Prepare comprehensive response
            knowledge_context_length = len(kb_response) + len(knowledge_context)

            response_data = {
                "response": enhanced_response,
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "persona": self.persona,
                "question_type": question_type,
                "follow_up_questions": follow_up_questions,
                "knowledge_context_used": True,
                "groq_enhanced": groq_used,
                "vaani_enhanced": vaani_enhanced,
                "sources": sources,
                "rag_data": {
                    "total_sources": len(sources),
                    "method": kb_result.get("method", "knowledge_base"),
                    "knowledge_context_length": knowledge_context_length,
                    "has_groq_answer": groq_used
                },
                "vaani_data": vaani_data,
                "rl_logs": rl_logs,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "metadata": {
                    "qna_keywords": [kw for kw in self.qna_keywords if kw in query.lower()],
                    "processing_type": "question_answering",
                    "enhancement_method": "groq" if groq_used else "knowledge_base",
                    "confidence_level": "high" if groq_used else "medium",
                    "sources_used": kb_result.get("total_results", 0)
                }
            }

            logger.info(f"✅ QnAAgent completed processing for task {task_id} - {question_type} question")
            return response_data

        except Exception as e:
            logger.error(f"❌ QnAAgent error: {str(e)}")

            # Return error response
            return {
                "response": "I apologize, but I'm experiencing difficulties answering your question at this moment. Please try again later.",
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run(self, input_path: str, live_feed: str = "", model: str = "qna_agent",
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
            "knowledge_agent_available": False,
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

        # Check KnowledgeAgent
        try:
            kb_health = self.knowledge_agent.health_check()
            health_status["knowledge_agent_available"] = kb_health.get("multi_folder_manager", False) or kb_health.get("qdrant_retriever", False)
        except Exception as e:
            logger.warning(f"KnowledgeAgent health check failed: {e}")

        # Overall status
        services_available = sum([
            health_status["rag_api_available"],
            health_status["groq_api_available"],
            health_status["knowledge_agent_available"]
        ])

        if services_available == 0:
            health_status["status"] = "degraded"
        elif services_available < 2:
            health_status["status"] = "partial"

        return health_status