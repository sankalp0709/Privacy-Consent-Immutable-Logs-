#!/usr/bin/env python3
"""
File Search Agent - Document and File Search Specialist
Provides intelligent file search, document retrieval, and content discovery.
"""

import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger
from utils.rag_client import rag_client
from utils.groq_client import groq_client
from utils.file_based_retriever import file_retriever
from reinforcement.rl_context import RLContext

logger = get_logger(__name__)

class FileSearchAgent:
    """Agent specialized in searching and retrieving information from files and documents."""

    def __init__(self):
        self.name = "FileSearchAgent"
        self.description = "Intelligent file and document search and retrieval"
        self.rl_context = RLContext()
        self.persona = "information_retriever"

        # Search keywords
        self.search_keywords = [
            "search", "find", "locate", "retrieve", "lookup", "discover",
            "file", "document", "folder", "directory", "path", "content"
        ]

        logger.info("✅ FileSearchAgent initialized with RAG API and file search capabilities")

    def _get_knowledge_context(self, query: str) -> str:
        """Get relevant knowledge from RAG API for search context."""
        try:
            # Enhance query with search context
            enhanced_query = f"Information retrieval and search strategies: {query}"

            # Query RAG API
            response = rag_client.query(enhanced_query, top_k=3)

            if response.get("status") == "success" and response.get("results"):
                # Combine relevant results
                contexts = []
                for result in response["results"][:2]:  # Top 2 results
                    if isinstance(result, dict) and "content" in result:
                        contexts.append(result["content"])

                return " ".join(contexts) if contexts else ""

            logger.warning("⚠️ No search context retrieved from RAG API")
            return ""

        except Exception as e:
            logger.error(f"❌ Error getting search context: {str(e)}")
            return ""

    def _search_files(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search through files using file-based retriever."""
        try:
            # Use file-based retriever for local file search
            results = file_retriever.search(query, limit=max_results)

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("text", ""),
                    "source": result.get("source", "unknown"),
                    "score": result.get("similarity_score", 0.0),
                    "file_name": Path(result.get("source", "")).name,
                    "search_type": "semantic_similarity"
                })

            return formatted_results

        except Exception as e:
            logger.error(f"❌ File search error: {str(e)}")
            return []

    def _search_with_rag(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using RAG API for broader knowledge retrieval."""
        try:
            response = rag_client.query(query, top_k=max_results)

            if response.get("status") == "success" and response.get("results"):
                formatted_results = []
                for result in response["results"]:
                    if isinstance(result, dict) and "content" in result:
                        formatted_results.append({
                            "content": result["content"],
                            "source": result.get("source", "rag_api"),
                            "score": result.get("score", 0.0),
                            "file_name": result.get("document_id", "unknown"),
                            "search_type": "knowledge_base"
                        })

                return formatted_results

            return []

        except Exception as e:
            logger.error(f"❌ RAG search error: {str(e)}")
            return []

    def _enhance_with_groq(self, query: str, search_results: List[Dict[str, Any]],
                          knowledge_context: str = "") -> tuple[str, bool]:
        """Enhance response using Groq with search expertise."""
        try:
            # Prepare search results summary
            results_summary = ""
            if search_results:
                results_summary = "\n".join([
                    f"- {result['file_name']}: {result['content'][:100]}..."
                    for result in search_results[:3]
                ])
            else:
                results_summary = "No relevant files found."

            # Build search enhancement prompt
            prompt = f"""As an expert information retrieval specialist, provide comprehensive search results and analysis for: "{query}"

{f'Relevant Context: {knowledge_context}' if knowledge_context else 'Apply information retrieval best practices.'}

Search Results Found:
{results_summary}

Please respond as a professional search specialist who:
- Analyzes and synthesizes information from multiple sources
- Provides clear, organized results with proper attribution
- Identifies the most relevant and authoritative information
- Offers additional search strategies if needed
- Maintains accuracy and relevance in results

Your search analysis should include:
- Summary of key findings and relevant information
- Source attribution and credibility assessment
- Recommendations for further investigation if needed
- Clear organization of results by relevance and type

Search Results Analysis:"""

            response, success = groq_client.generate_response(prompt, max_tokens=1200, temperature=0.6)

            if success and response:
                return response, True
            else:
                logger.warning("⚠️ Groq enhancement failed, using fallback")
                return self._fallback_search_results(query, search_results, knowledge_context), False

        except Exception as e:
            logger.error(f"❌ Groq enhancement error: {str(e)}")
            return self._fallback_search_results(query, search_results, knowledge_context), False

    def _fallback_search_results(self, query: str, search_results: List[Dict[str, Any]],
                               knowledge_context: str = "") -> str:
        """Provide fallback search results when Groq is unavailable."""
        base_response = f"Search Results for '{query}':\n\n"

        if search_results:
            base_response += "Found the following relevant information:\n\n"
            for i, result in enumerate(search_results[:5], 1):
                base_response += f"{i}. **{result['file_name']}** (Relevance: {result['score']:.2f})\n"
                base_response += f"   {result['content'][:200]}...\n\n"
        else:
            base_response += "No relevant files or documents were found matching your search criteria.\n\n"
            base_response += "Suggestions:\n"
            base_response += "• Try using different keywords\n"
            base_response += "• Check spelling and terminology\n"
            base_response += "• Consider broader or more specific search terms\n"

        if knowledge_context:
            base_response += f"\nAdditional Context: {knowledge_context[:300]}..."

        return base_response

    def _detect_search_type(self, query: str) -> str:
        """Detect the type of search requested."""
        query_lower = query.lower()

        if any(word in query_lower for word in ["file", "document", "folder", "directory"]):
            return "file_system"
        elif any(word in query_lower for word in ["knowledge", "information", "data", "facts"]):
            return "knowledge_base"
        elif any(word in query_lower for word in ["specific", "exact", "particular"]):
            return "exact_match"
        else:
            return "general_search"

    def process_query(self, query: str, task_id: str = None) -> Dict[str, Any]:
        """Process a file search query."""
        task_id = task_id or str(uuid.uuid4())

        try:
            logger.info(f"🔍 FileSearchAgent processing query: '{query[:100]}...'")

            # Detect search type
            search_type = self._detect_search_type(query)

            # Step 1: Get knowledge context from RAG API
            knowledge_context = self._get_knowledge_context(query)

            # Step 2: Perform searches based on type
            search_results = []

            if search_type in ["file_system", "general_search"]:
                # Search local files
                file_results = self._search_files(query, max_results=3)
                search_results.extend(file_results)

            # Always search knowledge base for broader context
            kb_results = self._search_with_rag(query, max_results=3)
            search_results.extend(kb_results)

            # Remove duplicates and sort by score
            seen_sources = set()
            unique_results = []
            for result in sorted(search_results, key=lambda x: x.get("score", 0), reverse=True):
                if result["source"] not in seen_sources:
                    seen_sources.add(result["source"])
                    unique_results.append(result)

            search_results = unique_results[:5]  # Limit to top 5

            # Step 3: Enhance with Groq using search expertise
            enhanced_response, groq_used = self._enhance_with_groq(query, search_results, knowledge_context)

            # Step 4: Log RL context
            self.rl_context.log_action(
                task_id=task_id,
                agent=self.name,
                model="groq" if groq_used else "fallback",
                action="file_search",
                metadata={
                    "query": query,
                    "search_type": search_type,
                    "results_found": len(search_results),
                    "knowledge_retrieved": bool(knowledge_context),
                    "groq_enhanced": groq_used,
                    "persona": self.persona
                }
            )

            # Step 5: Prepare response
            response_data = {
                "response": enhanced_response,
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "persona": self.persona,
                "search_type": search_type,
                "search_results": search_results,
                "knowledge_context_used": bool(knowledge_context),
                "groq_enhanced": groq_used,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "metadata": {
                    "search_keywords": [kw for kw in self.search_keywords if kw in query.lower()],
                    "processing_type": "file_search",
                    "enhancement_method": "groq" if groq_used else "fallback",
                    "total_results": len(search_results),
                    "search_sources": list(set(result["source"] for result in search_results))
                }
            }

            logger.info(f"✅ FileSearchAgent completed processing for task {task_id} - found {len(search_results)} results")
            return response_data

        except Exception as e:
            logger.error(f"❌ FileSearchAgent error: {str(e)}")

            # Return error response
            return {
                "response": "I apologize, but I'm experiencing difficulties searching for files at this moment. Please try again later.",
                "query_id": task_id,
                "query": query,
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run(self, input_path: str, live_feed: str = "", model: str = "file_search_agent",
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
            "file_retriever_available": False,
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

        # Check file retriever
        try:
            file_stats = file_retriever.get_stats()
            health_status["file_retriever_available"] = file_stats.get("total_chunks", 0) > 0
        except Exception as e:
            logger.warning(f"File retriever health check failed: {e}")

        # Overall status
        services_available = sum([
            health_status["rag_api_available"],
            health_status["groq_api_available"],
            health_status["file_retriever_available"]
        ])

        if services_available == 0:
            health_status["status"] = "degraded"
        elif services_available < 2:
            health_status["status"] = "partial"

        return health_status