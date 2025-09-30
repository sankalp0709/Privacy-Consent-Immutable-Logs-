#!/usr/bin/env python3
"""
Planner Agent - Task Planning and Strategy Specialist
Provides intelligent task planning, project management, and strategic guidance.
"""

import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import get_logger
from utils.rag_client import rag_client
from utils.groq_client import groq_client
from reinforcement.rl_context import RLContext

logger = get_logger(__name__)

class PlannerAgent:
    """Agent specialized in task planning, project management, and strategic guidance."""

    def __init__(self):
        self.name = "PlannerAgent"
        self.description = "Intelligent task planning and strategic guidance"
        self.rl_context = RLContext()
        self.persona = "strategic_planner"

        # Planning keywords
        self.planning_keywords = [
            "plan", "planning", "strategy", "strategic", "project", "task",
            "schedule", "timeline", "roadmap", "goals", "objectives", "milestones",
            "organize", "coordinate", "manage", "execute", "implement"
        ]

        logger.info("✅ PlannerAgent initialized with RAG API and Groq enhancement")

    def _get_knowledge_context(self, query: str) -> str:
        """Get relevant knowledge from RAG API for planning context."""
        try:
            # Enhance query with planning context
            enhanced_query = f"Project planning and management strategies: {query}"

            # Query RAG API
            response = rag_client.query(enhanced_query, top_k=3)

            if response.get("status") == "success" and response.get("results"):
                # Combine relevant results
                contexts = []
                for result in response["results"][:2]:  # Top 2 results
                    if isinstance(result, dict) and "content" in result:
                        contexts.append(result["content"])

                return " ".join(contexts) if contexts else ""

            logger.warning("⚠️ No planning context retrieved from RAG API")
            return ""

        except Exception as e:
            logger.error(f"❌ Error getting planning context: {str(e)}")
            return ""

    def _enhance_with_groq(self, query: str, knowledge_context: str = "") -> tuple[str, bool]:
        """Enhance response using Groq with planning expertise."""
        try:
            # Build planning enhancement prompt
            prompt = f"""As a strategic planner and project management expert, provide comprehensive planning guidance for: "{query}"

{f'Relevant Context: {knowledge_context}' if knowledge_context else 'Apply proven project management and planning methodologies.'}

Please respond as a professional strategic planner who:
- Breaks down complex tasks into manageable components
- Identifies dependencies and critical paths
- Considers risks and mitigation strategies
- Provides realistic timelines and resource estimates
- Uses structured planning frameworks
- Offers practical implementation guidance

Your planning response should include:
- Clear objectives and scope definition
- Step-by-step action plans
- Timeline and milestone recommendations
- Resource and dependency analysis
- Risk assessment and contingency plans
- Success metrics and evaluation criteria

Strategic Plan:"""

            response, success = groq_client.generate_response(prompt, max_tokens=1200, temperature=0.7)

            if success and response:
                return response, True
            else:
                logger.warning("⚠️ Groq enhancement failed, using fallback")
                return self._fallback_plan(query, knowledge_context), False

        except Exception as e:
            logger.error(f"❌ Groq enhancement error: {str(e)}")
            return self._fallback_plan(query, knowledge_context), False

    def _fallback_plan(self, query: str, knowledge_context: str = "") -> str:
        """Provide fallback planning response when Groq is unavailable."""
        base_response = f"Strategic Plan for '{query}':\n\n"

        # Basic planning structure
        base_response += """**Phase 1: Planning & Preparation**
• Define objectives and scope
• Identify key stakeholders
• Assess resources and constraints

**Phase 2: Execution**
• Break down tasks into manageable steps
• Establish timelines and milestones
• Monitor progress and adjust as needed

**Phase 3: Review & Optimization**
• Evaluate outcomes against objectives
• Identify lessons learned
• Plan for continuous improvement

"""

        if knowledge_context:
            base_response += f"\n**Additional Context:** {knowledge_context[:300]}..."
        else:
            base_response += "\n**Note:** This is a basic planning framework. Consider consulting with domain experts for complex projects."

        return base_response

    def _detect_plan_type(self, query: str) -> str:
        """Detect the type of planning requested."""
        query_lower = query.lower()

        if any(word in query_lower for word in ["project", "implementation", "execution"]):
            return "project_management"
        elif any(word in query_lower for word in ["strategy", "strategic", "long-term"]):
            return "strategic_planning"
        elif any(word in query_lower for word in ["task", "workflow", "process"]):
            return "task_planning"
        elif any(word in query_lower for word in ["schedule", "timeline", "calendar"]):
            return "scheduling"
        else:
            return "general_planning"

    def _create_action_plan(self, query: str, plan_type: str) -> List[Dict[str, Any]]:
        """Create a structured action plan based on the query and plan type."""
        actions = []

        if plan_type == "project_management":
            actions = [
                {"phase": "Initiation", "step": 1, "action": "Define project scope and objectives", "duration": "1-2 days"},
                {"phase": "Planning", "step": 2, "action": "Identify stakeholders and team members", "duration": "2-3 days"},
                {"phase": "Planning", "step": 3, "action": "Create detailed project plan and timeline", "duration": "3-5 days"},
                {"phase": "Execution", "step": 4, "action": "Implement project tasks according to plan", "duration": "Variable"},
                {"phase": "Monitoring", "step": 5, "action": "Track progress and manage changes", "duration": "Ongoing"},
                {"phase": "Closure", "step": 6, "action": "Review outcomes and document lessons learned", "duration": "1-2 days"}
            ]
        elif plan_type == "strategic_planning":
            actions = [
                {"phase": "Analysis", "step": 1, "action": "Conduct SWOT analysis and environmental scanning", "duration": "1-2 weeks"},
                {"phase": "Vision", "step": 2, "action": "Define mission, vision, and strategic objectives", "duration": "1 week"},
                {"phase": "Strategy", "step": 3, "action": "Develop strategic initiatives and priorities", "duration": "2-3 weeks"},
                {"phase": "Planning", "step": 4, "action": "Create implementation roadmap and action plans", "duration": "2-4 weeks"},
                {"phase": "Execution", "step": 5, "action": "Implement strategic initiatives", "duration": "6-12 months"},
                {"phase": "Review", "step": 6, "action": "Monitor progress and adjust strategy as needed", "duration": "Quarterly"}
            ]
        else:  # general planning
            actions = [
                {"phase": "Assessment", "step": 1, "action": "Analyze current situation and requirements", "duration": "1-2 days"},
                {"phase": "Planning", "step": 2, "action": "Define goals and create detailed plan", "duration": "2-3 days"},
                {"phase": "Preparation", "step": 3, "action": "Gather resources and prepare for execution", "duration": "1-2 days"},
                {"phase": "Execution", "step": 4, "action": "Implement the plan step by step", "duration": "Variable"},
                {"phase": "Evaluation", "step": 5, "action": "Review results and make improvements", "duration": "1 day"}
            ]

        return actions

    def process_query(self, query: str, task_id: str = None) -> Dict[str, Any]:
        """Process a planning query."""
        task_id = task_id or str(uuid.uuid4())

        try:
            logger.info(f"📋 PlannerAgent processing query: '{query[:100]}...'")

            # Detect plan type
            plan_type = self._detect_plan_type(query)

            # Create action plan
            action_plan = self._create_action_plan(query, plan_type)

            # Step 1: Get knowledge context from RAG API
            knowledge_context = self._get_knowledge_context(query)

            # Step 2: Enhance with Groq using planning expertise
            enhanced_response, groq_used = self._enhance_with_groq(query, knowledge_context)

            # Step 3: Log RL context
            self.rl_context.log_action(
                task_id=task_id,
                agent=self.name,
                model="groq" if groq_used else "fallback",
                action="strategic_planning",
                metadata={
                    "query": query,
                    "plan_type": plan_type,
                    "action_steps": len(action_plan),
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
                "plan_type": plan_type,
                "action_plan": action_plan,
                "knowledge_context_used": bool(knowledge_context),
                "groq_enhanced": groq_used,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "metadata": {
                    "planning_keywords": [kw for kw in self.planning_keywords if kw in query.lower()],
                    "processing_type": "strategic_planning",
                    "enhancement_method": "groq" if groq_used else "fallback",
                    "action_steps_count": len(action_plan),
                    "estimated_complexity": "medium"  # Could be enhanced with ML
                }
            }

            logger.info(f"✅ PlannerAgent completed processing for task {task_id}")
            return response_data

        except Exception as e:
            logger.error(f"❌ PlannerAgent error: {str(e)}")

            # Return error response
            return {
                "response": "I apologize, but I'm experiencing difficulties creating a strategic plan at this moment. Please try again later.",
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run(self, input_path: str, live_feed: str = "", model: str = "planner_agent",
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