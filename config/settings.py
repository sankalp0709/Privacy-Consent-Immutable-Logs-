# from dotenv import load_dotenv
# import os

# load_dotenv()

# MODEL_CONFIG = {
#     "llama": {
#         "api_url": "http://localhost:1234/v1/chat/completions",
#         "model_name": "llama-3.1-8b-instruct"
#     },
#     "vedas_agent": {
#         "endpoint": "http://localhost:8001/ask-vedas",
#         "headers": {"Content-Type": "application/json"},
#         "api_key": os.getenv("GEMINI_API_KEY"),
#         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
#     },
#     "edumentor_agent": {
#         "endpoint": "http://localhost:8001/edumentor",
#         "headers": {"Content-Type": "application/json"},
#         "api_key": os.getenv("GEMINI_API_KEY"),
#         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
#     },
#     "wellness_agent": {
#         "endpoint": "http://localhost:8001/wellness",
#         "headers": {"Content-Type": "application/json"},
#         "api_key": os.getenv("GEMINI_API_KEY"),
#         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
#     }
# }

# MONGO_CONFIG = {
#     "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
#     "database": "bhiv_core",
#     "collection": "task_logs"
# }

# # Timeout Configuration
# TIMEOUT_CONFIG = {
#     "default_timeout": int(os.getenv("DEFAULT_TIMEOUT", 120)),
#     "image_processing_timeout": int(os.getenv("IMAGE_PROCESSING_TIMEOUT", 180)),
#     "audio_processing_timeout": int(os.getenv("AUDIO_PROCESSING_TIMEOUT", 240)),
#     "pdf_processing_timeout": int(os.getenv("PDF_PROCESSING_TIMEOUT", 150)),
#     "llm_timeout": int(os.getenv("LLM_TIMEOUT", 120)),
#     "file_upload_timeout": int(os.getenv("FILE_UPLOAD_TIMEOUT", 300))
# }

# RL_CONFIG = {
#     "use_rl": os.getenv("USE_RL", "true").lower() == "true",
#     "exploration_rate": float(os.getenv("RL_EXPLORATION_RATE", 0.2)),
#     "buffer_file": "logs/learning_log.json",
#     "model_log_file": "logs/model_logs.json",
#     "agent_log_file": "logs/agent_logs.json",
#     "memory_size": int(os.getenv("RL_MEMORY_SIZE", 1000)),
#     "min_exploration_rate": float(os.getenv("RL_MIN_EXPLORATION", 0.05)),
#     "exploration_decay": float(os.getenv("RL_EXPLORATION_DECAY", 0.995)),
#     "confidence_threshold": float(os.getenv("RL_CONFIDENCE_THRESHOLD", 0.7)),
#     "enable_ucb": os.getenv("RL_ENABLE_UCB", "true").lower() == "true",
#     "enable_fallback_learning": os.getenv("RL_ENABLE_FALLBACK_LEARNING", "true").lower() == "true",
#     "log_to_mongo": os.getenv("RL_LOG_TO_MONGO", "true").lower() == "true"
# }


# # from dotenv import load_dotenv
# # import os

# # load_dotenv()

# # MODEL_CONFIG = {
# #     "llama": {
# #         "api_url": "http://localhost:1234/v1/chat/completions",
# #         "model_name": "llama-3.1-8b-instruct"
# #     },
# #     "vedas_agent": {
# #         "endpoint": "http://localhost:8001/ask-vedas",
# #         "headers": {"Content-Type": "application/json"},
# #         "api_key": os.getenv("GEMINI_API_KEY"),
# #         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
# #     },
# #     "edumentor_agent": {
# #         "endpoint": "http://localhost:8001/edumentor",
# #         "headers": {"Content-Type": "application/json"},
# #         "api_key": os.getenv("GEMINI_API_KEY"),
# #         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
# #     },
# #     "wellness_agent": {
# #         "endpoint": "http://localhost:8001/wellness",
# #         "headers": {"Content-Type": "application/json"},
# #         "api_key": os.getenv("GEMINI_API_KEY"),
# #         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
# #     }
# # }

# # MONGO_CONFIG = {
# #     "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
# #     "database": "bhiv_core",
# #     "collection": "task_logs"
# # }


from dotenv import load_dotenv
import os

load_dotenv()

MODEL_CONFIG = {
    "llama": {
        "api_url": "http://localhost:1234/v1/chat/completions",
        "model_name": "llama-3.1-8b-instruct"
    },
    "vedas_agent": {
        "endpoint": os.getenv("VEDAS_ENDPOINT", "http://localhost:8001/ask-vedas"),
        "headers": {"Content-Type": "application/json"},
        "api_key": os.getenv("GEMINI_API_KEY"),
        "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
    },
    "edumentor_agent": {
        "endpoint": os.getenv("EDUMENTOR_ENDPOINT", "http://localhost:8001/edumentor"),
        "headers": {"Content-Type": "application/json"},
        "api_key": os.getenv("GEMINI_API_KEY"),
        "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
    },
    "wellness_agent": {
        "endpoint": os.getenv("WELLNESS_ENDPOINT", "http://localhost:8001/wellness"),
        "headers": {"Content-Type": "application/json"},
        "api_key": os.getenv("GEMINI_API_KEY"),
        "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
    },
    "knowledge_agent": {
        "connection_type": "python_module",
        "module_path": "agents.knowledge_agent",
        "class_name": "KnowledgeAgent",
        "qdrant_collection": "vedas_knowledge_base",
        "tags": ["semantic_search", "vedabase"]
    }
}

MONGO_CONFIG = {
    "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    "database": "bhiv_core",
    "collection": "task_logs"
}

RAG_CONFIG = {
    "api_url": os.getenv("RAG_API_URL", "https://819d053306f2.ngrok-free.app/rag"),
    "default_top_k": int(os.getenv("RAG_DEFAULT_TOP_K", 5)),
    "timeout": int(os.getenv("RAG_TIMEOUT", 30))
}

TIMEOUT_CONFIG = {
    "default_timeout": int(os.getenv("DEFAULT_TIMEOUT", 120)),
    "image_processing_timeout": int(os.getenv("IMAGE_PROCESSING_TIMEOUT", 180)),
    "audio_processing_timeout": int(os.getenv("AUDIO_PROCESSING_TIMEOUT", 240)),
    "pdf_processing_timeout": int(os.getenv("PDF_PROCESSING_TIMEOUT", 150)),
    "llm_timeout": int(os.getenv("LLM_TIMEOUT", 120)),
    "file_upload_timeout": int(os.getenv("FILE_UPLOAD_TIMEOUT", 300)),
    "qdrant_query_timeout": int(os.getenv("QDRANT_QUERY_TIMEOUT", 60))
}

RL_CONFIG = {
    "use_rl": os.getenv("USE_RL", "true").lower() == "true",
    "exploration_rate": float(os.getenv("RL_EXPLORATION_RATE", 0.2)),
    "buffer_file": "logs/learning_log.json",
    "model_log_file": "logs/model_logs.json",
    "agent_log_file": "logs/agent_logs.json",
    "memory_size": int(os.getenv("RL_MEMORY_SIZE", 1000)),
    "min_exploration_rate": float(os.getenv("RL_MIN_EXPLORATION", 0.05)),
    "exploration_decay": float(os.getenv("RL_EXPLORATION_DECAY", 0.995)),
    "confidence_threshold": float(os.getenv("RL_CONFIDENCE_THRESHOLD", 0.7)),
    "enable_ucb": os.getenv("RL_ENABLE_UCB", "true").lower() == "true",
    "enable_fallback_learning": os.getenv("RL_ENABLE_FALLBACK_LEARNING", "true").lower() == "true",
    "log_to_mongo": os.getenv("RL_LOG_TO_MONGO", "true").lower() == "true",
    "semantic_search_reward_weight": float(os.getenv("RL_SEMANTIC_SEARCH_REWARD_WEIGHT", 1.5)),
    "vedabase_query_reward_weight": float(os.getenv("RL_VEDABASE_QUERY_REWARD_WEIGHT", 1.8))
}

# Groq API Configuration
GROQ_CONFIG = {
    "api_key": os.getenv("GROQ_API_KEY", ""),
    "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    "timeout": int(os.getenv("GROQ_TIMEOUT", "30")),
    "max_retries": int(os.getenv("GROQ_MAX_RETRIES", "3")),
    "retry_delay": float(os.getenv("GROQ_RETRY_DELAY", "1.0"))
}

# Update to current Groq model if using deprecated one
if GROQ_CONFIG["model"] == "llama-3.1-8b-instant":
    GROQ_CONFIG["model"] = "llama3.1-8b-instant"
    # Import logger here to avoid circular import
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.warning("Updated deprecated Groq model 'llama3-8b-8192' to 'llama3.1-8b-instant'")

# from dotenv import load_dotenv
# import os

# load_dotenv()

# MODEL_CONFIG = {
#     "llama": {
#         "api_url": "http://localhost:1234/v1/chat/completions",
#         "model_name": "llama-3.1-8b-instruct"
#     },
#     "vedas_agent": {
#         "endpoint": "http://localhost:8001/ask-vedas",
#         "headers": {"Content-Type": "application/json"},
#         "api_key": os.getenv("GEMINI_API_KEY"),
#         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
#     },
#     "edumentor_agent": {
#         "endpoint": "http://localhost:8001/edumentor",
#         "headers": {"Content-Type": "application/json"},
#         "api_key": os.getenv("GEMINI_API_KEY"),
#         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
#     },
#     "wellness_agent": {
#         "endpoint": "http://localhost:8001/wellness",
#         "headers": {"Content-Type": "application/json"},
#         "api_key": os.getenv("GEMINI_API_KEY"),
#         "backup_api_key": os.getenv("GEMINI_API_KEY_BACKUP")
#     }
# }

# MONGO_CONFIG = {
#     "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
#     "database": "bhiv_core",
#     "collection": "task_logs"
# }