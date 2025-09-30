#!/usr/bin/env python3
"""
Agent Orchestrator - Intelligent Agent Routing and Coordination
Provides intent classification and intelligent routing to specialized agents.
"""

import os
import uuid
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from utils.logger import get_logger
from utils.groq_client import groq_client
from reinforcement.rl_context import RLContext

# Import all specialized agents
from agents.summarizer_agent import SummarizerAgent
from agents.planner_agent import PlannerAgent
from agents.file_search_agent import FileSearchAgent
from agents.qna_agent import QnAAgent

logger = get_logger(__name__)

class AgentOrchestrator:
    """Intelligent orchestrator for routing queries to specialized agents."""

    def __init__(self):
        self.name = "AgentOrchestrator"
        self.description = "Intelligent agent routing and coordination system"
        self.rl_context = RLContext()

        # Initialize all specialized agents
        self.agents = {
            "summarization": SummarizerAgent(),
            "planning": PlannerAgent(),
            "file_search": FileSearchAgent(),
            "qna": QnAAgent()
        }

        # Intent classification patterns
        self.intent_patterns = {
            "summarization": [
                r"\b(summarize|summary|summarise|condense|abstract|overview|recap|brief|shorten|digest|key points)\b",
                r"\b(tl;dr|too long; didn't read|give me the gist|bottom line)\b",
                r"\b(can you summarize|please summarize|summarize this|summarize the)\b"
            ],
            "planning": [
                r"\b(plan|planning|strategy|strategic|project|task|schedule|timeline|roadmap|goals|objectives)\b",
                r"\b(organize|coordinate|manage|execute|implement|how to|steps to|process for)\b",
                r"\b(create a plan|make a plan|develop a strategy|design a roadmap)\b"
            ],
            "file_search": [
                r"\b(search|find|locate|retrieve|lookup|discover|file|document|folder|directory)\b",
                r"\b(where is|where can I find|look for|search for|find me)\b",
                r"\b(in the files|in documents|in the database|in the knowledge base)\b"
            ],
            "qna": [
                r"\b(what|how|why|when|where|who|which|explain|describe|tell me)\b",
                r"\b(question|answer|help|assist|clarify|understand|mean|definition)\b",
                r"\b(can you explain|please explain|I want to know|I'm curious about)\b"
            ]
        }

        # Confidence thresholds for routing
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }

        logger.info("✅ AgentOrchestrator initialized with all specialized agents")

    def _classify_intent(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        """Classify the intent of the user query using pattern matching and optional LLM."""
        query_lower = query.lower()

        # Calculate confidence scores for each intent
        intent_scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = 0

            for pattern in patterns:
                found_matches = len(re.findall(pattern, query_lower, re.IGNORECASE))
                if found_matches > 0:
                    matches += found_matches
                    score += found_matches * 0.2  # Weight each match

            # Boost score for primary keywords at the beginning
            first_word = query_lower.split()[0] if query_lower.split() else ""
            if intent == "qna" and first_word in ["what", "how", "why", "when", "where", "who", "which"]:
                score += 0.5
            elif intent == "summarization" and any(word in query_lower.split()[:3] for word in ["summarize", "summary", "summarise"]):
                score += 0.5
            elif intent == "planning" and any(word in query_lower.split()[:3] for word in ["plan", "strategy", "project"]):
                score += 0.5
            elif intent == "file_search" and any(word in query_lower.split()[:3] for word in ["search", "find", "locate"]):
                score += 0.5

            # Normalize score to 0-1 range
            intent_scores[intent] = min(score, 1.0)

        # Find the highest scoring intent
        best_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x])
        confidence = intent_scores[best_intent]

        # Use LLM for intent classification if confidence is low
        if confidence < self.confidence_thresholds["medium"]:
            llm_intent, llm_confidence = self._classify_with_llm(query)
            if llm_confidence > confidence:
                best_intent = llm_intent
                confidence = llm_confidence
                logger.info(f"🤖 LLM override: {best_intent} (confidence: {confidence:.2f})")

        logger.info(f"🎯 Intent classified: {best_intent} (confidence: {confidence:.2f})")
        return best_intent, confidence, intent_scores

    def _classify_with_llm(self, query: str) -> Tuple[str, float]:
        """Use LLM for intent classification when pattern matching is uncertain."""
        try:
            prompt = f"""Analyze this user query and classify the primary intent. Choose from: summarization, planning, file_search, or qna.

Query: "{query}"

Respond with only the intent name and confidence score (0.0-1.0), separated by a comma.
Example: qna,0.9

Intent definitions:
- summarization: Requests to condense, shorten, or provide overview of content
- planning: Requests for strategies, plans, timelines, or project management
- file_search: Requests to find, locate, or retrieve specific information or files
- qna: Questions seeking explanations, definitions, or general information

Classification:"""

            response, success = groq_client.generate_response(prompt, max_tokens=50, temperature=0.3)

            if success and response:
                try:
                    intent, confidence_str = response.strip().split(",")
                    intent = intent.strip().lower()
                    confidence = float(confidence_str.strip())

                    if intent in self.intent_patterns and 0 <= confidence <= 1:
                        return intent, confidence
                except ValueError:
                    pass

            logger.warning("⚠️ LLM intent classification failed, using fallback")
            return "qna", 0.5  # Default fallback

        except Exception as e:
            logger.error(f"❌ LLM intent classification error: {str(e)}")
            return "qna", 0.5

    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to level."""
        if confidence >= self.confidence_thresholds["high"]:
            return "high"
        elif confidence >= self.confidence_thresholds["medium"]:
            return "medium"
        else:
            return "low"

    def _route_to_agent(self, intent: str, query: str, task_id: str, requested_agent: str = None) -> Dict[str, Any]:
        """Route the query to the appropriate specialized agent."""
        agent = self.agents.get(intent)

        if not agent:
            logger.error(f"❌ No agent found for intent: {intent}")
            return {
                "response": f"I apologize, but I don't have a specialized agent for handling {intent} requests at this time.",
                "agent": "orchestrator",
                "intent": intent,
                "status": "error",
                "error": f"No agent available for intent: {intent}",
                "agent_logs": [f"No agent found for intent: {intent}"]
            }

        logger.info(f"🔄 Routing to {agent.name} for {intent} intent")
        agent_start_time = datetime.now()

        try:
            # Call the appropriate agent with agent filter for Q&A
            if agent.name == "QnAAgent":
                result = agent.process_query(query, task_id, agent_filter=requested_agent)
            else:
                result = agent.process_query(query, task_id)

            agent_processing_time = (datetime.now() - agent_start_time).total_seconds()

            # Extract agent logs and processing details
            agent_logs = result.get("agent_logs", [])
            processing_details = result.get("processing_details", {})

            # Add orchestrator metadata and agent processing details
            result.update({
                "orchestrator_routed": True,
                "detected_intent": intent,
                "routing_agent": self.name,
                "agent_processing_time": agent_processing_time,
                "agent_logs": agent_logs,
                "processing_details": processing_details
            })

            logger.info(f"✅ Agent {agent.name} completed processing in {agent_processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"❌ Agent routing error: {str(e)}")
            return {
                "response": f"I encountered an error while processing your request with the {agent.name}. Please try again.",
                "agent": agent.name,
                "intent": intent,
                "status": "error",
                "error": str(e),
                "agent_logs": [f"Agent routing error: {str(e)}"]
            }

    def _create_fallback_response(self, query: str, intent_scores: Dict[str, float]) -> Dict[str, Any]:
        """Create a fallback response when routing fails."""
        # Find the next best intent
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        fallback_intent = sorted_intents[1][0] if len(sorted_intents) > 1 else "qna"

        logger.info(f"🔄 Fallback routing to {fallback_intent}")

        return self._route_to_agent(fallback_intent, query, str(uuid.uuid4()))

    def process_query(self, query: str, context: Dict[str, Any] = None, task_id: str = None) -> Dict[str, Any]:
        """Main orchestrator method for processing user queries."""
        task_id = task_id or str(uuid.uuid4())
        context = context or {}

        try:
            logger.info(f"🎭 AgentOrchestrator processing: '{query[:100]}...'")

            # Extract requested agent from context
            requested_agent = context.get("requested_agent", "edumentor_agent")

            # Step 1: Intent Classification
            intent, confidence, intent_scores = self._classify_intent(query)
            confidence_level = self._get_confidence_level(confidence)

            logger.info(f"🎯 Classified intent: {intent} (confidence: {confidence_level})")
            logger.info(f"🎭 Requested agent: {requested_agent}")

            # Step 2: Route to Agent (with fallback for low confidence)
            if confidence_level == "low":
                logger.warning(f"⚠️ Low confidence in intent classification ({confidence:.2f}), considering fallback")
                result = self._create_fallback_response(query, intent_scores)
                result["low_confidence_fallback"] = True
                result["original_intent"] = intent
            else:
                result = self._route_to_agent(intent, query, task_id, requested_agent)

            # Step 3: Add orchestrator metadata
            result.update({
                "orchestrator_processed": True,
                "intent_classification": {
                    "detected_intent": intent,
                    "confidence_score": confidence,
                    "confidence_level": confidence_level,
                    "all_scores": intent_scores
                },
                "processing_timestamp": datetime.now().isoformat(),
                "orchestrator_version": "1.0.0"
            })

            # Step 4: Log RL context
            self.rl_context.log_action(
                task_id=task_id,
                agent=self.name,
                model="intent_classifier",
                action="orchestrate_query",
                metadata={
                    "query": query,
                    "final_intent": result.get("detected_intent", intent),
                    "confidence": confidence,
                    "confidence_level": confidence_level,
                    "agent_used": result.get("agent", "unknown"),
                    "success": result.get("status") == "success"
                }
            )

            logger.info(f"✅ Orchestrator completed for task {task_id} - routed to {result.get('agent', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"❌ AgentOrchestrator error: {str(e)}")

            # Return error response
            return {
                "response": "I apologize, but I'm experiencing difficulties coordinating your request. Please try again later.",
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "intent_classification": {
                    "detected_intent": "unknown",
                    "confidence_score": 0.0,
                    "confidence_level": "none"
                },
                "timestamp": datetime.now().isoformat()
            }

    def run(self, input_path: str, live_feed: str = "", model: str = "agent_orchestrator",
            input_type: str = "text", task_id: str = None) -> Dict[str, Any]:
        """Main entry point for orchestrator execution - compatible with existing interface."""
        return self.process_query(input_path, task_id)

    def get_available_agents(self) -> Dict[str, Any]:
        """Get information about all available agents."""
        agent_info = {}
        for intent, agent in self.agents.items():
            agent_info[intent] = {
                "name": agent.name,
                "description": agent.description,
                "status": "available"
            }

        return {
            "orchestrator": self.name,
            "available_agents": agent_info,
            "supported_intents": list(self.intent_patterns.keys()),
            "timestamp": datetime.now().isoformat()
        }

    def health_check(self) -> Dict[str, Any]:
        """Check orchestrator and all agent health."""
        health_status = {
            "orchestrator": self.name,
            "status": "healthy",
            "agents": {},
            "timestamp": datetime.now().isoformat()
        }

        # Check each agent
        all_healthy = True
        for intent, agent in self.agents.items():
            try:
                agent_health = agent.health_check()
                health_status["agents"][intent] = {
                    "name": agent.name,
                    "status": agent_health.get("status", "unknown"),
                    "healthy": agent_health.get("status") == "healthy"
                }
                if agent_health.get("status") != "healthy":
                    all_healthy = False
            except Exception as e:
                health_status["agents"][intent] = {
                    "name": agent.name,
                    "status": "error",
                    "error": str(e),
                    "healthy": False
                }
                all_healthy = False

        # Overall status
        health_status["status"] = "healthy" if all_healthy else "degraded"

        return health_status