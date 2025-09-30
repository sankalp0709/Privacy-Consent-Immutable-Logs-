from utils.rag_client import rag_client
from utils.logger import get_logger
import uuid
import os
from datetime import datetime
from reinforcement.rl_context import RLContext
from reinforcement.reward_functions import get_reward_from_output
from typing import Dict, Any

logger = get_logger(__name__)

class KnowledgeAgent:
    """Agent for handling knowledge base queries using external RAG API."""

    def __init__(self):
        """Initialize the KnowledgeAgent with RAG API client."""
        self.name = "KnowledgeAgent"
        self.description = "Agent for comprehensive knowledge retrieval using external RAG API"

        # Initialize RAG client
        self.rag_client = rag_client
        logger.info("✅ KnowledgeAgent initialized with RAG API client")
    
    def query(self, query_text: str, top_k: int = 5, agent_filter: str = None) -> Dict[str, Any]:
        """
        Query knowledge base using external RAG API.

        Args:
            query_text: The query to search for
            top_k: Number of top results to return

        Returns:
            Dictionary with response and sources
        """
        logger.info(f"🔍 KnowledgeAgent query: '{query_text}'")

        try:
            # Apply agent-specific filtering to the query
            filtered_query = self._apply_agent_filter(query_text, agent_filter)

            # Query the external RAG API with filtered query
            rag_result = self.rag_client.query(filtered_query, top_k=top_k)

            if rag_result["status"] == 200 and rag_result.get("response"):
                # Extract content from chunks
                response = [chunk["content"] for chunk in rag_result["response"]]
                sources = [chunk["source"] for chunk in rag_result["response"]]

                logger.info(f"✅ RAG API found {len(response)} results")

                # Return formatted response with both chunks and Groq answer
                return {
                    "response": response,
                    "sources": sources,
                    "method": "rag_api",
                    "folder_count": 1,
                    "total_results": len(response),
                    "status": 200,
                    "timestamp": datetime.now().isoformat(),
                    "groq_answer": rag_result.get("groq_answer", ""),
                    "metadata": {
                        "tags": ["semantic_search", "rag_api", "groq_enhanced"],
                        "retriever": "external_rag_api",
                        "total_results": len(response),
                        "has_groq_answer": bool(rag_result.get("groq_answer"))
                    }
                }
            else:
                logger.warning("⚠️ RAG API returned no results or error")
                return self._create_fallback_response(query_text)

        except Exception as e:
            logger.error(f"❌ Error querying RAG API: {str(e)}")
            return self._create_fallback_response(query_text)

    def _create_fallback_response(self, query_text: str) -> Dict[str, Any]:
        """Create a fallback response when RAG API is unavailable."""
        logger.warning("🆘 Creating fallback response")

        return {
            "response": [f"I apologize, but I'm currently unable to access the knowledge base. Your query was: '{query_text}'"],
            "sources": ["fallback"],
            "method": "fallback",
            "folder_count": 0,
            "total_results": 1,
            "status": 503,
            "timestamp": datetime.now().isoformat(),
            "groq_answer": f"I apologize, but I'm currently unable to access the knowledge base to provide a comprehensive answer to your query: '{query_text}'. Please try again later.",
            "metadata": {
                "tags": ["fallback", "error"],
                "retriever": "none",
                "total_results": 1,
                "has_groq_answer": True
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the RAG API."""
        health = self.rag_client.health_check()
        return {
            "rag_api_status": health["status"],
            "rag_api_url": health["api_url"],
            "response_time": health.get("response_time", "unknown")
        }

    def health_check(self) -> Dict[str, Any]:
        """Check health of the RAG API."""
        return {
            "rag_client": self.rag_client.health_check()["status"] == "healthy"
        }

    def _apply_agent_filter(self, query_text: str, agent_filter: str = None) -> str:
        """Apply agent-specific filtering to the query."""
        if not agent_filter:
            return query_text

        # Agent-specific query modifications
        agent_filters = {
            "vedas_agent": [
                "vedas", "vedic", "hindu scripture", "sanskrit", "mantra", "yajna",
                "brahman", "karma", "dharma", "samsara", "moksha", "bhagavad gita",
                "upanishad", "purana", "ramayana", "mahabharata", "spiritual wisdom"
            ],
            "wellness_agent": [
                "wellness", "health", "yoga", "meditation", "ayurveda", "pranayama",
                "mindfulness", "stress relief", "holistic health", "natural healing",
                "spiritual wellness", "mental health", "physical health", "emotional balance"
            ],
            "edumentor_agent": [
                "education", "learning", "teaching", "study", "academic", "knowledge",
                "curriculum", "pedagogy", "educational technology", "student development"
            ],
            "knowledge_agent": [
                "semantic search", "information retrieval", "knowledge base",
                "data mining", "information extraction", "content analysis"
            ]
        }

        # Get filter terms for the agent
        filter_terms = agent_filters.get(agent_filter, [])

        if filter_terms:
            # Enhance query with agent-specific terms
            enhanced_query = f"{query_text} {' '.join(filter_terms[:3])}"  # Add top 3 relevant terms
            logger.info(f"🔍 Applied {agent_filter} filter to query: '{query_text}' -> '{enhanced_query}'")
            return enhanced_query
        else:
            logger.info(f"🔍 No specific filter for agent: {agent_filter}")
            return query_text

    def enhance_with_llm(self, query: str, knowledge_context: str, groq_answer: str = None) -> str:
        """Enhanced response using Groq answer from RAG API or Ollama fallback."""
        try:
            # If we have a Groq answer from RAG API, use it directly
            if groq_answer and groq_answer.strip():
                logger.info("✅ Using Groq answer from RAG API")
                return groq_answer

            # Try Ollama when configured as fallback
            import requests
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3-8b-8192")
            if ollama_url and ollama_model:
                prompt = (
                    "You are a helpful assistant. Use the following knowledge context if available to answer the query.\n\n"
                    f"Query: {query}\n\n"
                    f"Knowledge Context:\n{knowledge_context}\n\n"
                    "If the context is empty or irrelevant, give a general helpful answer. Keep it clear and concise."
                )
                payload = {"model": ollama_model, "prompt": prompt, "stream": False}
                headers = {"Content-Type": "application/json"}
                r = requests.post(ollama_url, json=payload, headers=headers, timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")))
                if r.status_code == 200:
                    data = r.json()
                    text = data.get("response") or data.get("message", {}).get("content")
                    if text:
                        return text.strip()

            # Fallback: local formatting and summarization
            if knowledge_context.strip():
                # Simple summarization: find sentences with the most query words
                query_words = set(query.lower().split())
                sentences = knowledge_context.split('.')
                sentence_scores = []
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    sentence_words = set(sentence.lower().split())
                    score = len(query_words.intersection(sentence_words))
                    sentence_scores.append((score, sentence))

                sentence_scores.sort(key=lambda x: x[0], reverse=True)

                # Return the top 3 sentences
                top_sentences = [s for score, s in sentence_scores[:3] if score > 0]

                if top_sentences:
                    return ". ".join(top_sentences).strip() + "."

                else:
                    # If no sentences have query words, return the first 3 sentences
                    return ". ".join(sentences[:3]).strip() + "."

            return f"I don't have specific information about '{query}' in the knowledge base."
        except Exception as e:
            logger.error(f"LLM enhancement failed: {str(e)}")
            return knowledge_context if knowledge_context.strip() else "Unable to process your query at this time."
    def run(self, input_path: str, live_feed: str = "", model: str = "knowledge_agent", input_type: str = "text", task_id: str = None) -> Dict[str, Any]:
        """Main entry point for agent execution - compatible with existing agent interface."""
        task_id = task_id or str(uuid.uuid4())
        logger.info(f"KnowledgeAgent processing task {task_id}, query: {input_path}")

        # Use input_path as the query text
        query_result = self.query(input_path, top_k=5)

        # Format response to match expected agent output format
        if query_result.get("status", 200) == 200 and query_result.get("response"):
            # Combine knowledge base results
            if isinstance(query_result["response"], list) and query_result["response"]:
                combined_text = "\n\n".join(query_result["response"][:3])
            else:
                combined_text = str(query_result["response"])

            # Get Groq answer from RAG API response
            groq_answer = query_result.get("groq_answer", "")

            # Enhance with LLM for better formatting and context (will use Groq answer if available)
            enhanced_response = self.enhance_with_llm(input_path, combined_text, groq_answer)

            return {
                "response": enhanced_response,
                "query_id": task_id,
                "query": input_path,
                "sources": query_result.get("sources", []),
                "metadata": query_result.get("metadata", {}),
                "timestamp": query_result.get("timestamp", datetime.now().isoformat()),
                "status": 200,
                "model": model,
                "knowledge_base_results": len(query_result.get("response", [])) if isinstance(query_result.get("response"), list) else 1,
                "groq_answer": groq_answer,
                "endpoint": "knowledge_agent"
            }
        else:
            # Fallback to LLM only if no knowledge base results
            try:
                fallback_response = self.enhance_with_llm(input_path, "No specific knowledge found in database.")
                return {
                    "response": fallback_response,
                    "query_id": task_id,
                    "query": input_path,
                    "sources": [],
                    "metadata": {},
                    "timestamp": datetime.now().isoformat(),
                    "status": 200,
                    "model": model,
                    "knowledge_base_results": 0,
                    "fallback": True,
                    "endpoint": "knowledge_agent"
                }
            except Exception:
                return {
                    "response": "I couldn't find relevant information in the knowledge base for your query.",
                    "query_id": task_id,
                    "query": input_path,
                    "sources": [],
                    "metadata": {},
                    "timestamp": datetime.now().isoformat(),
                    "status": 404,
                    "model": model,
                    "error": query_result.get("error", "No results found"),
                    "endpoint": "knowledge_agent"
                }