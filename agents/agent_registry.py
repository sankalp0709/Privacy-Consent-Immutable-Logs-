# import json
# import os
# from typing import Dict, Any, Optional
# from utils.logger import get_logger

# logger = get_logger(__name__)

# class AgentRegistry:
#     """Registry for managing agent configurations and routing."""
    
#     def __init__(self, config_file: str = "config/agent_configs.json"):
#         self.config_file = config_file
#         self.agents = {}
#         self.load_agents()
    
#     def load_agents(self):
#         """Load agent configurations from JSON file."""
#         try:
#             if os.path.exists(self.config_file):
#                 with open(self.config_file, 'r') as f:
#                     self.agents = json.load(f)
#                 logger.info(f"Loaded {len(self.agents)} agents from {self.config_file}")
#             else:
#                 logger.warning(f"Agent config file not found: {self.config_file}")
#                 self.agents = {}
#         except Exception as e:
#             logger.error(f"Error loading agent configs: {e}")
#             self.agents = {}
    
#     def find_agent(self, task_context: Dict[str, Any]) -> str:
#         """Find appropriate agent based on task context."""
#         if isinstance(task_context, str):
#             # If passed a string, treat it as agent name
#             return task_context
        
#         # Extract agent from task context
#         agent_name = task_context.get('model', task_context.get('agent', 'edumentor_agent'))
#         input_type = task_context.get('input_type', 'text')
        
#         # Route based on input type if no specific agent
#         if agent_name == 'edumentor_agent' and input_type != 'text':
#             type_mapping = {
#                 'pdf': 'archive_agent',
#                 'image': 'image_agent', 
#                 'audio': 'audio_agent'
#             }
#             agent_name = type_mapping.get(input_type, 'edumentor_agent')
        
#         return agent_name
    
#     def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
#         """Get agent configuration by name."""
#         return self.agents.get(agent_name)
    
#     def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
#         """Get agent configuration by name (alias for get_agent_config)."""
#         return self.get_agent_config(agent_name)
    
#     def list_agents(self) -> Dict[str, Any]:
#         """List all available agents."""
#         return self.agents
    
#     def register_agent(self, agent_name: str, config: Dict[str, Any]):
#         """Register a new agent configuration."""
#         self.agents[agent_name] = config
#         logger.info(f"Registered agent: {agent_name}")
    
#     def is_agent_available(self, agent_name: str) -> bool:
#         """Check if an agent is available."""
#         return agent_name in self.agents

# # Global agent registry instance
# agent_registry = AgentRegistry()


import json
import os
import uuid
from typing import Dict, Any, Optional
from utils.logger import get_logger
from reinforcement.agent_selector import AgentSelector
from reinforcement.rl_context import RLContext

logger = get_logger(__name__)

class AgentRegistry:
    """Registry for managing agent configurations and routing with RL support."""
    
    def __init__(self, config_file: str = "config/agent_configs.json"):
        self.config_file = config_file
        self.agents = {}
        self.agent_selector = AgentSelector()
        self.rl_context = RLContext()
        self.load_agents()
    
    def load_agents(self):
        """Load agent configurations from JSON file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.agents = json.load(f)
                logger.info(f"Loaded {len(self.agents)} agents from {self.config_file}")
            else:
                logger.warning(f"Agent config file not found: {self.config_file}")
                self.agents = {
                    "edumentor_agent": {
                        "connection_type": "python_module",
                        "module_path": "agents.stream_transformer_agent",
                        "class_name": "StreamTransformerAgent",
                        "id": "edumentor_agent",
                        "tags": ["summarize", "pdf", "text"],
                        "weight": 0.8
                    },
                    "archive_agent": {
                        "connection_type": "python_module",
                        "module_path": "agents.archive_agent",
                        "class_name": "ArchiveAgent",
                        "id": "archive_agent",
                        "tags": ["archive", "search", "pdf"],
                        "weight": 0.7
                    },
                    "knowledge_agent": {
                        "connection_type": "python_module",
                        "module_path": "agents.KnowledgeAgent",
                        "class_name": "KnowledgeAgent",
                        "id": "knowledge_agent",
                        "tags": ["semantic_search", "vedabase"],
                        "weight": 0.9
                    }
                }
                self.save_agents()
        except Exception as e:
            logger.error(f"Error loading agent configs: {e}")
            self.agents = {}
    
    def save_agents(self):
        """Save agent configurations to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.agents, f, indent=2)
            logger.info(f"Saved agent configurations to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving agent configs: {e}")
    
    def find_agent(self, task_context: Dict[str, Any]) -> str:
        """Find appropriate agent based on task context with RL support."""
        import random
        task_id = task_context.get("task_id", str(uuid.uuid4()))
        task = task_context.get("task", "summarize")

        # Check if user explicitly requested a specific agent
        requested_agent = task_context.get('agent') or task_context.get('model')
        user_requested = bool(requested_agent and self.is_agent_available(requested_agent))

        # Use RL-based selection if enabled in settings
        from config.settings import RL_CONFIG
        use_rl = RL_CONFIG.get("use_rl", False)
        exploration_rate = RL_CONFIG.get("exploration_rate", 0.2)

        rl_selected_agent = None
        if use_rl:
            rl_selected_agent = self.agent_selector.select_agent(task_context)
            if self.is_agent_available(rl_selected_agent):
                self.rl_context.log_action(
                    task_id=task_id,
                    agent=rl_selected_agent,
                    model="none",
                    action="rl_agent_selection",
                    metadata={"task": task, "input_type": task_context.get("input_type", "text")}
                )

        # Decision logic: RL can override user request based on exploration rate
        final_agent = requested_agent if user_requested else rl_selected_agent

        if use_rl and user_requested and rl_selected_agent and rl_selected_agent != requested_agent:
            # Allow RL to override user request with exploration probability
            if random.random() < exploration_rate:
                final_agent = rl_selected_agent
                logger.info(f"🎲 RL EXPLORATION: Overriding user request '{requested_agent}' with RL selection '{rl_selected_agent}'")
                self.rl_context.log_action(
                    task_id=task_id,
                    agent=final_agent,
                    model="none",
                    action="rl_override_user_request",
                    metadata={"original_request": requested_agent, "rl_selection": rl_selected_agent, "exploration": True}
                )
            else:
                logger.info(f"✅ Respecting user request: {requested_agent} (RL suggested: {rl_selected_agent})")
                self.rl_context.log_action(
                    task_id=task_id,
                    agent=final_agent,
                    model="none",
                    action="user_request_respected",
                    metadata={"user_request": requested_agent, "rl_suggestion": rl_selected_agent}
                )
        elif rl_selected_agent and not user_requested:
            final_agent = rl_selected_agent
            logger.info(f"🤖 RL selected agent: {final_agent} for task: {task}")
        elif user_requested:
            final_agent = requested_agent
            logger.info(f"👤 User requested agent: {final_agent}")
            self.rl_context.log_action(
                task_id=task_id,
                agent=final_agent,
                model="none",
                action="user_selected_agent",
                metadata={"task": task, "user_requested": True}
            )

        # If still no agent selected, fallback to deterministic routing
        if not final_agent:
            final_agent = self._fallback_agent_selection(task_context, task_id)

        return final_agent

    def _fallback_agent_selection(self, task_context: Dict[str, Any], task_id: str) -> str:
        """Fallback agent selection when RL and user request fail."""
        task = task_context.get("task", "summarize")

        # Fallback to deterministic routing
        if isinstance(task_context, str):
            return task_context

        # Extract agent from task context (default to edumentor_agent)
        agent_name = task_context.get('model', task_context.get('agent', 'edumentor_agent'))
        input_type = task_context.get('input_type', 'text')
        tags = task_context.get('tags', [])

        # Route based on tags if provided
        if tags:
            for agent_name_candidate, config in self.agents.items():
                if any(tag in config.get("tags", []) for tag in tags):
                    self.rl_context.log_action(
                        task_id=task_id,
                        agent=agent_name_candidate,
                        model="none",
                        action="select_agent_by_tag",
                        metadata={"task": task, "tags": tags}
                    )
                    logger.info(f"Selected agent: {agent_name_candidate} for tags: {tags}")
                    return agent_name_candidate

        # Route based on input type if no specific agent
        if agent_name == 'edumentor_agent' and input_type != 'text':
            type_mapping = {
                'pdf': 'archive_agent',
                'image': 'image_agent',
                'audio': 'audio_agent',
                'semantic_search': 'knowledge_agent',
                'vedabase': 'knowledge_agent'
            }
            agent_name = type_mapping.get(input_type, 'edumentor_agent')

        self.rl_context.log_action(
            task_id=task_id,
            agent=agent_name,
            model="none",
            action="select_agent_by_type",
            metadata={"task": task, "input_type": input_type}
        )
        logger.info(f"Selected agent: {agent_name} for task: {task}, input_type: {input_type}")
        return agent_name
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration by name."""
        return self.agents.get(agent_name)
    
    def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration by name (alias for get_agent_config)."""
        return self.get_agent_config(agent_name)
    
    def list_agents(self) -> Dict[str, Any]:
        """List all available agents."""
        return self.agents
    
    def register_agent(self, agent_name: str, config: Dict[str, Any]):
        """Register a new agent configuration."""
        self.agents[agent_name] = config
        self.save_agents()
        logger.info(f"Registered agent: {agent_name}")
    
    def is_agent_available(self, agent_name: str) -> bool:
        """Check if an agent is available."""
        return agent_name in self.agents

# Global agent registry instance
agent_registry = AgentRegistry()