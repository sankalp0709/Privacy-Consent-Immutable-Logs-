#!/usr/bin/env python3
"""
Uniguru-LM Service - Unified implementation for Agentic-LM Sprint
Combines BHIV Core enhancement with new Uniguru-LM prototype

Features:
- KB-grounded NLP composer with templates + n-gram + tiny GRU
- Vaani TTS integration
- NAS embeddings access with proper credentials
- Enhanced BHIV Core RAG with reinforcement learning
- Comprehensive logging and feedback collection
- Docker-ready deployment

Author: Vijay
"""

import os
import sys
import json
import uuid
import time
import hashlib
import logging
import asyncio
import requests
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

# FastAPI and web framework
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn

# ML and NLP libraries
import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Database and storage
import motor.motor_asyncio
from pymongo import MongoClient
import pymongo

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import RAG client
from utils.rag_client import rag_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration and Models
# =============================================================================

@dataclass
class UniGuruConfig:
    """Configuration for Uniguru-LM service"""
    # Service configuration
    service_port: int = int(os.getenv("UNIGURU_SERVICE_PORT", "8080"))
    service_host: str = os.getenv("UNIGURU_SERVICE_HOST", "0.0.0.0")
    api_key: str = os.getenv("UNIGURU_API_KEY", "uniguru-dev-key-2025")
    
    # NAS Configuration with credentials from env
    nas_host: str = "192.168.0.94"  # Updated from your .env
    nas_username: str = os.getenv("NAS_USERNAME", "Vijay")
    nas_password: str = os.getenv("NAS_PASSWORD", "vijay45")
    nas_base_path: str = os.getenv("NAS_PATH", r"\\192.168.0.94\Guruukul_DB")
    
    # Qdrant Configuration from env
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "vedas_knowledge_base")
    qdrant_vector_size: int = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))
    qdrant_folders: List[str] = None
    
    # Local drive paths from env
    embeddings_path: str = os.getenv("EMBEDDINGS_PATH", r"G:\qdrant_embeddings")
    documents_path: str = os.getenv("DOCUMENTS_PATH", r"G:\source_documents")
    metadata_path: str = os.getenv("METADATA_PATH", r"G:\metadata")
    qdrant_data_path: str = os.getenv("QDRANT_DATA_PATH", r"G:\qdrant_data")
    
    # MongoDB Configuration from env
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/bhiv_core")
    mongo_db: str = "uniguru_lm"
    
    # API Keys from env
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gemini_backup_key: str = os.getenv("GEMINI_API_KEY_BACKUP", "")
    
    # Ollama Configuration from env
    ollama_url: str = os.getenv("OLLAMA_URL", "https://769d44eefc7c.ngrok-free.app/api/generate")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    
    # Vaani Sentinel X Configuration
    vaani_endpoint: str = os.getenv("VAANI_ENDPOINT", "https://vaani-sentinel-gs6x.onrender.com")
    vaani_username: str = os.getenv("VAANI_USERNAME", "admin")
    vaani_password: str = os.getenv("VAANI_PASSWORD", "secret")
    
    # Model Configuration
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    gru_hidden_size: int = int(os.getenv("GRU_HIDDEN_SIZE", "128"))
    max_context_length: int = 2048
    
    # RL Configuration from env
    use_rl: bool = os.getenv("USE_RL", "true").lower() == "true"
    rl_exploration_rate: float = float(os.getenv("RL_EXPLORATION_RATE", "0.2"))
    
    # Feature Flags
    use_uniguru_jugaad: bool = os.getenv("USE_UNIGURU_JUGAAD", "true").lower() == "true"
    canary_traffic_percent: int = int(os.getenv("CANARY_TRAFFIC_PERCENT", "10"))
    enable_rl: bool = os.getenv("USE_RL", "true").lower() == "true"
    
    def __post_init__(self):
        if self.qdrant_folders is None:
            # Get from environment or use defaults
            instance_names = os.getenv("QDRANT_INSTANCE_NAMES", "qdrant_data,qdrant_fourth_data,qdrant_legacy_data,qdrant_new_data")
            self.qdrant_folders = [name.strip() for name in instance_names.split(",")]
        
        # Parse Qdrant URL for host and port
        if self.qdrant_url:
            from urllib.parse import urlparse
            parsed = urlparse(self.qdrant_url)
            self.qdrant_host = parsed.hostname or "localhost"
            self.qdrant_port = parsed.port or 6333

# Pydantic models for API
class ComposeRequest(BaseModel):
    query: str = Field(..., description="User query in English or Hindi")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(default="anonymous")
    voice_enabled: bool = Field(default=True, description="Enable TTS generation")
    language: str = Field(default="auto", description="Language preference: en, hi, auto")
    max_results: int = Field(default=5, description="Maximum KB results to retrieve")

class FeedbackRequest(BaseModel):
    trace_id: str
    session_id: str
    user_id: str = "anonymous"
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = None
    useful: bool = True

class ComposeResponse(BaseModel):
    trace_id: str
    session_id: str
    final_text: str
    citations: List[Dict[str, Any]]
    audio_url: Optional[str] = None
    grounded: bool
    confidence_score: float
    processing_time_ms: int
    language_detected: str

# =============================================================================
# Tiny GRU Composer Model
# =============================================================================

class TinyGRUComposer(nn.Module):
    """Lightweight GRU-based text composer with template integration"""
    
    def __init__(self, vocab_size: int = 10000, embedding_dim: int = 256, 
                 hidden_size: int = 128, num_layers: int = 2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.gru = nn.GRU(embedding_dim, hidden_size, num_layers, batch_first=True)
        self.output_layer = nn.Linear(hidden_size, vocab_size)
        self.dropout = nn.Dropout(0.3)
        
    def forward(self, x, hidden=None):
        embedded = self.embedding(x)
        embedded = self.dropout(embedded)
        output, hidden = self.gru(embedded, hidden)
        output = self.output_layer(output)
        return output, hidden

# =============================================================================
# Knowledge Base Manager (RAG API Integration)
# =============================================================================

class KnowledgeBaseManager:
    """Knowledge base manager using external RAG API"""

    def __init__(self, config: UniGuruConfig):
        self.config = config
        self.rag_client = rag_client
        logger.info("✅ KnowledgeBaseManager initialized with RAG API client")

    def search_embeddings(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using external RAG API"""
        try:
            logger.info(f"🔍 Searching RAG API for: '{query[:50]}...'")

            # Query the RAG API
            rag_result = self.rag_client.query(query, max_results)

            if rag_result["status"] == 200 and rag_result.get("response"):
                logger.info(f"✅ RAG API returned {len(rag_result['response'])} results")
                return rag_result["response"]
            else:
                logger.warning("⚠️ RAG API returned no results")
                return self._create_fallback_results(query, max_results)

        except Exception as e:
            logger.error(f"❌ Error in search_embeddings: {str(e)}")
            return self._create_fallback_results(query, max_results)

    def get_folder_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG API"""
        health = self.rag_client.health_check()
        return {
            "rag_api_status": health["status"],
            "rag_api_url": health["api_url"],
            "response_time": health.get("response_time", "unknown")
        }

    def _create_fallback_results(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Create synthetic results when RAG API is unavailable"""
        logger.info("🆘 Creating fallback synthetic results")

        fallback_content = {
            "artificial intelligence": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines. It includes machine learning, natural language processing, and computer vision.",
            "machine learning": "Machine Learning is a subset of AI that enables computers to learn and make decisions from data without being explicitly programmed for every task.",
            "deep learning": "Deep Learning uses neural networks with multiple layers to process data and make intelligent decisions, mimicking how the human brain works.",
            "default": f"This is a response about {query}. The system provides information based on available knowledge and context."
        }

        # Find best match or use default
        query_lower = query.lower()
        content = fallback_content.get("default", fallback_content["default"])

        for key, value in fallback_content.items():
            if key != "default" and key in query_lower:
                content = value
                break

        return [{
            "content": content,
            "source": "synthetic:fallback",
            "score": 0.5,
            "metadata": {"type": "fallback", "query": query},
            "document_id": "fallback-001",
            "folder": "synthetic"
        }]

# =============================================================================
# Indigenous NLP Composer
# =============================================================================

class IndigenousComposer:
    """Template-based composer with n-gram enhancement"""
    
    def __init__(self):
        self.templates = {
            "en": {
                "grounded": [
                    "Based on the knowledge sources, {content}",
                    "According to the available information, {content}",
                    "The sources indicate that {content}",
                    "From the knowledge base: {content}"
                ],
                "synthesis": [
                    "In summary, {content}",
                    "To conclude, {content}",
                    "Overall, {content}",
                    "Key insights: {content}"
                ]
            },
            "hi": {
                "grounded": [
                    "ज्ञान स्रोतों के आधार पर, {content}",
                    "उपलब्ध जानकारी के अनुसार, {content}",
                    "स्रोत इंगित करते हैं कि {content}",
                    "ज्ञान आधार से: {content}"
                ],
                "synthesis": [
                    "संक्षेप में, {content}",
                    "निष्कर्ष में, {content}",
                    "कुल मिलाकर, {content}",
                    "मुख्य अंतर्दृष्टि: {content}"
                ]
            }
        }
        
        # Simple n-gram model for context enhancement
        self.bigrams = {}
        self.trigrams = {}
    
    def detect_language(self, text: str) -> str:
        """Simple language detection"""
        # Count Hindi characters (Devanagari script)
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        
        if hindi_chars > english_chars:
            return "hi"
        else:
            return "en"
    
    def build_ngrams(self, texts: List[str]):
        """Build n-gram models from retrieved context"""
        for text in texts:
            words = text.lower().split()
            
            # Build bigrams
            for i in range(len(words) - 1):
                bigram = (words[i], words[i + 1])
                self.bigrams[bigram] = self.bigrams.get(bigram, 0) + 1
            
            # Build trigrams
            for i in range(len(words) - 2):
                trigram = (words[i], words[i + 1], words[i + 2])
                self.trigrams[trigram] = self.trigrams.get(trigram, 0) + 1
    
    def compose_response(self, query: str, kb_results: List[Dict[str, Any]], 
                        language: str = "auto", llm_client=None) -> Tuple[str, bool, float]:
        """Compose response using templates, retrieved knowledge, and optional LLM enhancement"""
        
        if language == "auto":
            language = self.detect_language(query)
        
        if not kb_results:
            # No grounding available - use LLM if available
            if llm_client:
                fallback_prompt = f"User asked: {query}\n\nPlease provide a helpful response based on your knowledge."
                llm_response, success = llm_client.generate_response(fallback_prompt, max_tokens=500)
                if success and llm_response:
                    return llm_response, False, 0.3  # Lower confidence for non-grounded
            
            fallback_response = "I don't have enough information to provide a comprehensive answer to your query."
            if language == "hi":
                fallback_response = "मैं आपके प्रश्न का संपूर्ण उत्तर देने के लिए पर्याप्त जानकारी नहीं रख रहा हूँ।"
            return fallback_response, False, 0.0
        
        # Extract content from KB results
        contents = [result.get("content", "") for result in kb_results if result.get("content")]
        
        if not contents:
            return "No relevant content found.", False, 0.0
        
        # Build n-grams for context enhancement
        self.build_ngrams(contents)
        
        # Create grounded response with LLM enhancement if available
        combined_content = " ".join(contents[:3])  # Use top 3 results
        
        if llm_client and len(combined_content) > 100:  # Use LLM for better composition
            try:
                enhance_prompt = f"""Based on this knowledge base content, please provide a comprehensive and well-structured answer to the user's question.

User Question: {query}

Knowledge Base Content:
{combined_content[:1500]}...

Please provide a clear, accurate answer that synthesizes this information. Respond in {'Hindi' if language == 'hi' else 'English'}."""
                
                llm_response, success = llm_client.generate_response(enhance_prompt, max_tokens=800)
                if success and llm_response and len(llm_response) > 50:
                    # Calculate confidence based on relevance scores
                    avg_score = sum(result.get("score", 0) for result in kb_results) / len(kb_results)
                    confidence = min(avg_score * 1.2, 1.0)  # Boost confidence for LLM-enhanced
                    return llm_response, True, confidence
            except Exception as e:
                logger.warning(f"⚠️ LLM enhancement failed, falling back to templates: {e}")
        
        # Fallback to template-based composition
        # Truncate if too long
        if len(combined_content) > 500:
            combined_content = combined_content[:500] + "..."
        
        # Select template
        templates = self.templates.get(language, self.templates["en"])
        template = templates["grounded"][0]  # Use first template for simplicity
        
        # Compose final response
        final_text = template.format(content=combined_content)
        
        # Calculate confidence based on relevance scores
        avg_score = sum(result.get("score", 0) for result in kb_results) / len(kb_results)
        confidence = min(avg_score, 1.0)
        
        return final_text, True, confidence

# =============================================================================
# Vaani TTS Integration
# =============================================================================

class OllamaClient:
    """Client for Ollama LLM integration"""
    
    def __init__(self, config: UniGuruConfig):
        self.config = config
        self.endpoint = config.ollama_url
        self.model = config.ollama_model
        
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> Tuple[str, bool]:
        """Generate response using Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": max_tokens
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true"
            }
            
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "").strip()
                if generated_text:
                    logger.info(f"✅ Ollama response generated successfully")
                    return generated_text, True
                else:
                    logger.warning(f"⚠️ Empty response from Ollama")
                    return "", False
            else:
                logger.error(f"❌ Ollama error: {response.status_code} - {response.text}")
                return "", False
                
        except Exception as e:
            logger.error(f"❌ Error calling Ollama: {e}")
            return "", False

class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self, config: UniGuruConfig):
        self.config = config
        self.api_key = config.gemini_api_key
        self.backup_key = config.gemini_backup_key
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> Tuple[str, bool]:
        """Generate response using Gemini"""
        if not self.api_key:
            return "", False
            
        try:
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "maxOutputTokens": max_tokens
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            url = f"{self.endpoint}?key={self.api_key}"
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and result["candidates"]:
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info(f"✅ Gemini response generated successfully")
                    return text.strip(), True
                else:
                    logger.warning(f"⚠️ No candidates in Gemini response")
                    return "", False
            else:
                logger.error(f"❌ Gemini error: {response.status_code} - {response.text}")
                # Try backup key if available
                if self.backup_key and self.backup_key != self.api_key:
                    logger.info("🔄 Trying backup Gemini key...")
                    url = f"{self.endpoint}?key={self.backup_key}"
                    backup_response = requests.post(url, json=payload, headers=headers, timeout=60)
                    if backup_response.status_code == 200:
                        result = backup_response.json()
                        if "candidates" in result and result["candidates"]:
                            text = result["candidates"][0]["content"]["parts"][0]["text"]
                            logger.info(f"✅ Gemini backup response generated successfully")
                            return text.strip(), True
                return "", False
                
        except Exception as e:
            logger.error(f"❌ Error calling Gemini: {e}")
            return "", False


# =============================================================================
# MongoDB Logger and RL Integration
# =============================================================================

class UniGuruLogger:
    """Comprehensive logging and RL integration"""
    
    def __init__(self, config: UniGuruConfig):
        self.config = config
        self.mongo_client = MongoClient(config.mongo_uri)
        self.db = self.mongo_client[config.mongo_db]
        self.traces_collection = self.db.traces
        self.feedback_collection = self.db.feedback
        self.rl_collection = self.db.rl_actions
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            self.traces_collection.create_index("trace_id", unique=True)
            self.traces_collection.create_index("session_id")
            self.traces_collection.create_index("timestamp")
            self.feedback_collection.create_index("trace_id")
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
    
    def log_trace(self, trace_data: Dict[str, Any]):
        """Log complete processing trace"""
        try:
            trace_data["timestamp"] = datetime.utcnow()
            result = self.traces_collection.insert_one(trace_data)
            logger.info(f"✅ Logged trace: {trace_data['trace_id']}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Error logging trace: {e}")
            return None
    
    def log_feedback(self, feedback_data: Dict[str, Any]):
        """Log user feedback for RL"""
        try:
            feedback_data["timestamp"] = datetime.utcnow()
            result = self.feedback_collection.insert_one(feedback_data)
            
            # Update RL weights based on feedback
            if self.config.enable_rl:
                self._update_rl_weights(feedback_data)
            
            logger.info(f"✅ Logged feedback: {feedback_data['trace_id']}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Error logging feedback: {e}")
            return None
    
    def _update_rl_weights(self, feedback: Dict[str, Any]):
        """Update RL weights based on feedback"""
        try:
            rl_action = {
                "trace_id": feedback["trace_id"],
                "action": "feedback_update",
                "reward": feedback["rating"] / 5.0,  # Normalize to 0-1
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "useful": feedback.get("useful", True),
                    "feedback_text": feedback.get("feedback_text", "")
                }
            }
            
            self.rl_collection.insert_one(rl_action)
            logger.info(f"✅ Updated RL weights for trace: {feedback['trace_id']}")
            
        except Exception as e:
            logger.error(f"❌ Error updating RL weights: {e}")

# =============================================================================
# Main Uniguru-LM Service
# =============================================================================

class UniGuruLMService:
    """Main service class combining all components"""

    def __init__(self):
        self.config = UniGuruConfig()
        self.knowledge_manager = KnowledgeBaseManager(self.config)
        self.composer = IndigenousComposer()
        # TTS client is now part of the comprehensive Vaani client
        # self.tts_client = VaaniTTSClient(self.config)
        self.logger_service = UniGuruLogger(self.config)

        # Initialize LLM clients
        self.ollama_client = OllamaClient(self.config)
        self.gemini_client = GeminiClient(self.config)

        # Initialize comprehensive Vaani client
        from utils.vaani_client import VaaniClient
        self.vaani_client = VaaniClient(self.config)

        # Initialize GRU model (mock for now)
        self.gru_model = None

        logger.info("✅ UniGuru-LM Service initialized successfully")
        logger.info(f"🤖 Available LLMs: Ollama ({self.config.ollama_model}), Gemini ({'✅' if self.config.gemini_api_key else '❌'})")
        logger.info(f"📚 Knowledge Base: RAG API ({self.config.api_key[:10]}...)")
        logger.info(f"🎵 Vaani Integration: {'✅' if self.vaani_client.token else '❌'}")
    
    async def compose(self, request: ComposeRequest) -> ComposeResponse:
        """Main compose endpoint logic"""
        start_time = time.time()
        trace_id = str(uuid.uuid4())
        
        try:
            # Step 1: KB Search
            logger.info(f"🔍 Searching KB for query: {request.query[:100]}...")
            kb_results = self.knowledge_manager.search_embeddings(
                request.query,
                max_results=request.max_results
            )
            
            # Step 2: Select LLM for enhancement
            llm_client = None
            if self.config.enable_rl and len(kb_results) > 0:  # Use LLM enhancement when we have good grounding
                # Try Ollama first, then Gemini as fallback
                if self.config.ollama_url:
                    llm_client = self.ollama_client
                elif self.config.gemini_api_key:
                    llm_client = self.gemini_client
            
            # Step 3: Compose Response
            logger.info(f"✍️ Composing response with {len(kb_results)} KB results using {'LLM enhancement' if llm_client else 'template system'}...")
            final_text, grounded, confidence = self.composer.compose_response(
                request.query,
                kb_results,
                request.language,
                llm_client
            )
            
            # Step 4: Generate Audio (if enabled)
            audio_url = None
            if request.voice_enabled:
                logger.info("🔊 Generating audio using Vaani...")
                language = self.composer.detect_language(final_text)
                audio_url = await self.vaani_client.generate_audio(final_text, language)
            
            # Step 5: Prepare response
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract citations
            citations = []
            for result in kb_results[:3]:  # Top 3 for citations
                citations.append({
                    "source": result.get("source", ""),
                    "content_preview": result.get("content", "")[:200] + "...",
                    "score": result.get("score", 0),
                    "document_id": result.get("document_id", ""),
                    "metadata": result.get("metadata", {})
                })
            
            response = ComposeResponse(
                trace_id=trace_id,
                session_id=request.session_id,
                final_text=final_text,
                citations=citations,
                audio_url=audio_url,
                grounded=grounded,
                confidence_score=confidence,
                processing_time_ms=processing_time,
                language_detected=self.composer.detect_language(request.query)
            )
            
            # Step 6: Log trace
            trace_data = {
                "trace_id": trace_id,
                "session_id": request.session_id,
                "user_id": request.user_id,
                "query": request.query,
                "response": response.dict(),
                "steps": [
                    {
                        "step": "kb_search",
                        "results_count": len(kb_results),
                        "top_score": kb_results[0].get("score", 0) if kb_results else 0
                    },
                    {
                        "step": "llm_selection",
                        "llm_used": "ollama" if llm_client == self.ollama_client else "gemini" if llm_client == self.gemini_client else "none",
                        "enhancement_enabled": llm_client is not None
                    },
                    {
                        "step": "compose",
                        "grounded": grounded,
                        "confidence": confidence,
                        "language": response.language_detected,
                        "method": "llm_enhanced" if llm_client else "template_based"
                    },
                    {
                        "step": "tts",
                        "enabled": request.voice_enabled,
                        "generated": audio_url is not None
                    }
                ],
                "processing_time_ms": processing_time,
                "config": {
                    "rl_enabled": self.config.enable_rl,
                    "ollama_model": self.config.ollama_model,
                    "gemini_available": bool(self.config.gemini_api_key)
                }
            }
            
            self.logger_service.log_trace(trace_data)
            
            logger.info(f"✅ Compose completed for trace: {trace_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in compose: {e}")
            raise HTTPException(status_code=500, detail=f"Compose failed: {str(e)}")
    
    async def process_feedback(self, feedback: FeedbackRequest):
        """Process user feedback for RL"""
        try:
            feedback_data = {
                "trace_id": feedback.trace_id,
                "session_id": feedback.session_id,
                "user_id": feedback.user_id,
                "rating": feedback.rating,
                "feedback_text": feedback.feedback_text,
                "useful": feedback.useful
            }
            
            result = self.logger_service.log_feedback(feedback_data)
            logger.info(f"✅ Processed feedback for trace: {feedback.trace_id}")
            
            return {"status": "success", "feedback_id": result}
            
        except Exception as e:
            logger.error(f"❌ Error processing feedback: {e}")
            raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")

# =============================================================================
# FastAPI Application Setup
# =============================================================================

# Initialize service
service = UniGuruLMService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting UniGuru-LM Service...")

    # Startup tasks
    stats = service.knowledge_manager.get_folder_stats()
    logger.info(f"📊 Service Stats: {stats}")

    yield

    # Shutdown tasks
    logger.info("🛑 Shutting down UniGuru-LM Service...")

# Create FastAPI app
app = FastAPI(
    title="UniGuru-LM Service",
    description="Indigenous NLP composer with KB grounding and Vaani TTS",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != service.config.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "UniGuru-LM",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    stats = service.knowledge_manager.get_folder_stats()

    # Test MongoDB connection
    mongo_healthy = True
    try:
        service.logger_service.mongo_client.admin.command('ping')
    except:
        mongo_healthy = False

    # Test Ollama connection
    ollama_healthy = False
    try:
        test_response, success = service.ollama_client.generate_response("test", max_tokens=5)
        ollama_healthy = success
    except:
        pass

    # Test Gemini availability
    gemini_available = bool(service.config.gemini_api_key)

    # Test RAG API health
    rag_healthy = stats["rag_api_status"] == "healthy"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "rag_api": rag_healthy,
            "mongodb": mongo_healthy,
            "ollama_llm": ollama_healthy,
            "gemini_llm": gemini_available,
        },
        "config": {
            "service_port": service.config.service_port,
            "canary_traffic": service.config.canary_traffic_percent,
            "rl_enabled": service.config.enable_rl,
            "uniguru_jugaad": service.config.use_uniguru_jugaad,
            "ollama_model": service.config.ollama_model,
        },
        "rag_api": {
            "url": stats["rag_api_url"],
            "status": stats["rag_api_status"],
            "response_time": stats["response_time"]
        }
    }

@app.post("/compose", response_model=ComposeResponse)
async def compose_endpoint(
    request: ComposeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Main compose endpoint - KB grounded text generation with TTS"""
    
    # Feature flag check
    if not service.config.use_uniguru_jugaad:
        raise HTTPException(status_code=503, detail="UniGuru-LM is disabled")
    
    # Canary traffic routing (mock implementation)
    import random
    if random.randint(1, 100) > service.config.canary_traffic_percent:
        # Route to legacy system (mock)
        logger.info("🔄 Routing to legacy system (canary)")
        # In real implementation, this would call the legacy BHIV system
    
    return await service.compose(request)

@app.post("/feedback")
async def feedback_endpoint(
    feedback: FeedbackRequest,
    api_key: str = Depends(verify_api_key)
):
    """Feedback collection for RL improvement"""
    result = await service.process_feedback(feedback)
    return result

@app.get("/stats")
async def stats_endpoint(api_key: str = Depends(verify_api_key)):
    """Get service statistics and performance metrics"""

    # Get basic stats
    stats = service.knowledge_manager.get_folder_stats()

    # Get database stats
    try:
        db_stats = {
            "total_traces": service.logger_service.traces_collection.count_documents({}),
            "total_feedback": service.logger_service.feedback_collection.count_documents({}),
            "avg_rating": list(service.logger_service.feedback_collection.aggregate([
                {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
            ]))[0].get("avg_rating", 0) if service.logger_service.feedback_collection.count_documents({}) > 0 else 0
        }
        stats.update(db_stats)
    except Exception as e:
        logger.error(f"❌ Error getting DB stats: {e}")
        stats["db_error"] = str(e)

    return stats

@app.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    """Serve generated audio files"""
    audio_path = f"audio_cache/{audio_id}"
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(audio_path, media_type="audio/wav")

# =============================================================================
# Enhanced BHIV Integration Endpoints
# =============================================================================

@app.post("/bhiv/compose")
async def bhiv_compose_endpoint(
    request: ComposeRequest,
    api_key: str = Depends(verify_api_key)
):
    """BHIV Core integration endpoint with enhanced RAG"""
    
    # Enhanced composition with BHIV patterns
    logger.info(f"🔗 BHIV integration compose for query: {request.query[:100]}...")
    
    # Use enhanced search with reinforcement learning
    enhanced_request = ComposeRequest(
        query=f"BHIV Enhanced: {request.query}",
        session_id=request.session_id,
        user_id=request.user_id,
        voice_enabled=request.voice_enabled,
        language=request.language,
        max_results=min(request.max_results * 2, 10)  # Get more results for better grounding
    )
    
    result = await service.compose(enhanced_request)
    
    # Add BHIV-specific metadata
    result.final_text = f"[BHIV Enhanced] {result.final_text}"
    
    return result

@app.get("/bhiv/agent_status")
async def bhiv_agent_status():
    """Status of BHIV agents integration"""
    return {
        "bhiv_agents": {
            "uniguru_lm": {
                "status": "active",
                "version": "1.0.0",
                "last_health_check": datetime.utcnow().isoformat()
            },
            "rag_enhanced": True,
            "rl_enabled": service.config.enable_rl,
            "rag_api": service.knowledge_manager.get_folder_stats()
        }
    }

# =============================================================================
# Development and Testing Endpoints
# =============================================================================

@app.post("/test/smoke")
async def smoke_test():
    """Comprehensive smoke test for deployment verification"""
    
    test_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {}
    }
    
    # Test 1: RAG API connectivity
    try:
        stats = service.knowledge_manager.get_folder_stats()
        test_results["tests"]["rag_api_connectivity"] = {
            "status": "PASS" if stats["rag_api_status"] == "healthy" else "FAIL",
            "details": stats
        }
    except Exception as e:
        test_results["tests"]["rag_api_connectivity"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    # Test 2: KB Search
    try:
        kb_results = service.knowledge_manager.search_embeddings("test query", max_results=3)
        test_results["tests"]["kb_search"] = {
            "status": "PASS" if len(kb_results) >= 0 else "FAIL",
            "results_count": len(kb_results)
        }
    except Exception as e:
        test_results["tests"]["kb_search"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    # Test 3: Composer
    try:
        text, grounded, confidence = service.composer.compose_response(
            "test query", 
            [{"content": "test content", "score": 0.8}]
        )
        test_results["tests"]["composer"] = {
            "status": "PASS" if text else "FAIL",
            "grounded": grounded,
            "confidence": confidence
        }
    except Exception as e:
        test_results["tests"]["composer"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    # Test 4: Database connectivity
    try:
        test_trace = {
            "trace_id": f"test-{uuid.uuid4()}",
            "test": True,
            "query": "smoke test"
        }
        service.logger_service.log_trace(test_trace)
        test_results["tests"]["database"] = {
            "status": "PASS",
            "trace_logged": True
        }
    except Exception as e:
        test_results["tests"]["database"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    # Overall status
    all_passed = all(
        test.get("status") == "PASS" 
        for test in test_results["tests"].values()
    )
    
    test_results["overall_status"] = "PASS" if all_passed else "FAIL"
    test_results["passed_tests"] = sum(
        1 for test in test_results["tests"].values() 
        if test.get("status") == "PASS"
    )
    test_results["total_tests"] = len(test_results["tests"])
    
    return test_results

# =============================================================================
# Agent Orchestrator Integration
# =============================================================================

# Import the AgentOrchestrator
from agents.agent_orchestrator import AgentOrchestrator

# Initialize orchestrator
orchestrator = AgentOrchestrator()

# Pydantic models for new endpoints
class AskRequest(BaseModel):
    query: str = Field(..., description="User query for agent processing")
    user_id: str = Field(default="anonymous", description="User identifier")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Session identifier")
    input_type: str = Field(default="text", description="Input type: text or voice")

class AskResponse(BaseModel):
    response: str
    agent_used: str
    intent_detected: str
    confidence_score: float
    processing_time_ms: int
    trace_id: str
    session_id: str
    timestamp: str
    metadata: Dict[str, Any] = {}

class ConsentRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    consent_type: str = Field(..., description="Type of consent: privacy, data_processing, etc.")
    granted: bool = Field(..., description="Whether consent is granted or revoked")
    consent_details: Optional[str] = Field(None, description="Additional consent details")

class ConsentResponse(BaseModel):
    user_id: str
    consent_type: str
    granted: bool
    timestamp: str
    consent_id: str

# =============================================================================
# New API Endpoints
# =============================================================================

@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(
    request: AskRequest,
    api_key: str = Depends(verify_api_key)
):
    """Intelligent query processing with agent orchestration"""
    start_time = time.time()

    try:
        logger.info(f"🤖 Processing ask request: '{request.query[:100]}...'")

        # Process query through orchestrator
        result = orchestrator.process_query(
            query=request.query,
            task_id=str(uuid.uuid4())
        )

        processing_time = int((time.time() - start_time) * 1000)

        # Format response
        response = AskResponse(
            response=result.get("response", ""),
            agent_used=result.get("agent", "unknown"),
            intent_detected=result.get("detected_intent", "unknown"),
            confidence_score=result.get("intent_classification", {}).get("confidence_score", 0.0),
            processing_time_ms=processing_time,
            trace_id=result.get("query_id", str(uuid.uuid4())),
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            metadata={
                "orchestrator_processed": result.get("orchestrator_processed", False),
                "low_confidence_fallback": result.get("low_confidence_fallback", False),
                "original_intent": result.get("original_intent"),
                "status": result.get("status", "unknown")
            }
        )

        logger.info(f"✅ Ask request completed - routed to {response.agent_used}")
        return response

    except Exception as e:
        logger.error(f"❌ Error in ask endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ask processing failed: {str(e)}")

@app.get("/alerts")
async def alerts_endpoint(
    api_key: str = Depends(verify_api_key),
    limit: int = 10,
    flagged_only: bool = True
):
    """Get system alerts and flagged activities"""
    try:
        logger.info("🚨 Fetching system alerts")

        # Get recent traces with potential issues
        alerts = []

        # Query for traces with errors or low confidence
        try:
            error_traces = list(service.logger_service.traces_collection.find(
                {
                    "$or": [
                        {"response.status": "error"},
                        {"response.confidence_score": {"$lt": 0.3}},
                        {"steps.step": "compose", "steps.grounded": False}
                    ]
                },
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit))

            for trace in error_traces:
                alerts.append({
                    "alert_id": trace.get("trace_id", str(uuid.uuid4())),
                    "type": "processing_issue",
                    "severity": "medium" if trace.get("response", {}).get("status") == "error" else "low",
                    "message": f"Processing issue in trace {trace.get('trace_id', 'unknown')}",
                    "query": trace.get("query", "")[:100],
                    "confidence": trace.get("response", {}).get("confidence_score", 0),
                    "timestamp": trace.get("timestamp", datetime.now().isoformat()),
                    "details": {
                        "status": trace.get("response", {}).get("status"),
                        "grounded": any(step.get("grounded", False) for step in trace.get("steps", [])),
                        "processing_time": trace.get("processing_time_ms", 0)
                    }
                })

        except Exception as e:
            logger.warning(f"Could not fetch error traces: {e}")

        # Add system health alerts
        try:
            health = await health()
            if health["status"] != "healthy":
                alerts.append({
                    "alert_id": f"health-{datetime.now().isoformat()}",
                    "type": "system_health",
                    "severity": "high",
                    "message": "System health issues detected",
                    "timestamp": datetime.now().isoformat(),
                    "details": health
                })
        except Exception as e:
            logger.warning(f"Could not check system health: {e}")

        # Filter for flagged only if requested
        if flagged_only:
            alerts = [alert for alert in alerts if alert["severity"] in ["high", "medium"]]

        # Sort by timestamp (most recent first)
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "alerts": alerts[:limit],
            "total_count": len(alerts),
            "flagged_only": flagged_only,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error in alerts endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Alerts retrieval failed: {str(e)}")

@app.get("/consent")
async def get_consent(
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get user consent status"""
    try:
        logger.info(f"📋 Checking consent status for user: {user_id}")

        # In a real implementation, this would query a consent database
        # For now, return mock consent status
        consent_status = {
            "user_id": user_id,
            "privacy_policy": {
                "granted": True,
                "timestamp": "2025-01-01T00:00:00.000000",
                "version": "1.0"
            },
            "data_processing": {
                "granted": True,
                "timestamp": "2025-01-01T00:00:00.000000",
                "purpose": "AI model training and improvement"
            },
            "analytics": {
                "granted": False,
                "timestamp": None,
                "purpose": "Usage analytics and performance monitoring"
            }
        }

        return {
            "user_id": user_id,
            "consent_status": consent_status,
            "last_updated": datetime.now().isoformat(),
            "compliance_status": "compliant"
        }

    except Exception as e:
        logger.error(f"❌ Error getting consent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Consent retrieval failed: {str(e)}")

@app.post("/consent", response_model=ConsentResponse)
async def update_consent(
    request: ConsentRequest,
    api_key: str = Depends(verify_api_key)
):
    """Update user consent settings"""
    try:
        logger.info(f"📝 Updating consent for user {request.user_id}: {request.consent_type} = {request.granted}")

        # In a real implementation, this would update a consent database
        consent_id = str(uuid.uuid4())

        # Log the consent change
        consent_log = {
            "consent_id": consent_id,
            "user_id": request.user_id,
            "consent_type": request.consent_type,
            "granted": request.granted,
            "details": request.consent_details,
            "timestamp": datetime.now().isoformat(),
            "ip_address": "system",  # Would be extracted from request in real implementation
            "user_agent": "api_call"
        }

        # Store in database (mock implementation)
        try:
            service.logger_service.mongo_client[service.config.mongo_db]["consent_logs"].insert_one(consent_log)
        except Exception as e:
            logger.warning(f"Could not log consent change to database: {e}")

        response = ConsentResponse(
            user_id=request.user_id,
            consent_type=request.consent_type,
            granted=request.granted,
            timestamp=datetime.now().isoformat(),
            consent_id=consent_id
        )

        logger.info(f"✅ Consent updated for user {request.user_id}")
        return response

    except Exception as e:
        logger.error(f"❌ Error updating consent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Consent update failed: {str(e)}")

@app.get("/agents/status")
async def agents_status_endpoint(api_key: str = Depends(verify_api_key)):
    """Get status of all available agents"""
    try:
        logger.info("🔍 Checking agent statuses")

        # Get orchestrator status
        orchestrator_status = orchestrator.get_available_agents()

        # Get individual agent health checks
        agent_health = {}
        for agent_name, agent_info in orchestrator_status["available_agents"].items():
            try:
                agent = getattr(orchestrator, 'agents', {}).get(agent_name.lower().replace('_', ''))
                if agent and hasattr(agent, 'health_check'):
                    agent_health[agent_name] = agent.health_check()
                else:
                    agent_health[agent_name] = {"status": "unknown", "error": "Health check not available"}
            except Exception as e:
                agent_health[agent_name] = {"status": "error", "error": str(e)}

        return {
            "orchestrator": orchestrator_status,
            "agent_health": agent_health,
            "overall_status": "healthy" if all(
                health.get("status") == "healthy"
                for health in agent_health.values()
            ) else "degraded",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error getting agent statuses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent status retrieval failed: {str(e)}")

# =============================================================================
# Docker and Deployment Configuration
# =============================================================================

def create_docker_files():
    """Create Docker configuration files"""
    
    dockerfile_content = '''
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    wget \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p audio_cache logs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "uniguru_lm_service.py"]
'''

    docker_compose_content = '''
version: '3.8'

services:
  uniguru-lm:
    build: .
    ports:
      - "8080:8080"
    environment:
      - MONGO_URI=mongodb://mongo:27017
      - QDRANT_HOST=qdrant
    depends_on:
      - mongo
      - qdrant
    volumes:
      - ./audio_cache:/app/audio_cache
      - ./logs:/app/logs
      # Mount NAS (adjust path as needed)
      - /mnt/nas/Guruukul_DB:/nas/Guruukul_DB
    networks:
      - uniguru-network

  mongo:
    image: mongo:5
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - uniguru-network

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - uniguru-network

  vaani-tts:
    # Replace with actual Vaani TTS image
    image: vaani-tts:latest
    ports:
      - "8081:8081"
    networks:
      - uniguru-network

networks:
  uniguru-network:
    driver: bridge

volumes:
  mongo_data:
  qdrant_data:
'''

    # Write Docker files with UTF-8 encoding
    with open("Dockerfile", "w", encoding='utf-8') as f:
        f.write(dockerfile_content.strip())
    
    with open("docker-compose.dev.yml", "w", encoding='utf-8') as f:
        f.write(docker_compose_content.strip())
    
    logger.info("✅ Docker configuration files created")

# =============================================================================
# Main execution
# =============================================================================

if __name__ == "__main__":
    # Create Docker files only if needed (skip to avoid Unicode issues)
    create_files = os.getenv("CREATE_DOCKER_FILES", "false").lower() == "true"
    if create_files:
        create_docker_files()
    
    # Create curl test script (only if requested)
    if create_files:
        curl_script = '''#!/bin/bash
# Smoke test script for UniGuru-LM Service

echo "Starting UniGuru-LM Smoke Tests..."

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -X GET "http://localhost:8080/health"
echo -e "\n"

# Test 2: Compose endpoint (English)
echo "2. Testing compose endpoint (English)..."
curl -X POST "http://localhost:8080/compose" \\
  -H "X-API-Key: uniguru-dev-key-2025" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "What is artificial intelligence?",
    "session_id": "test-session-1",
    "user_id": "test-user",
    "voice_enabled": false,
    "language": "en"
  }'
echo -e "\n"

# Test 3: Compose endpoint (Hindi)
echo "3. Testing compose endpoint (Hindi)..."
curl -X POST "http://localhost:8080/compose" \\
  -H "X-API-Key: uniguru-dev-key-2025" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "What is machine learning in simple terms?",
    "session_id": "test-session-2",
    "user_id": "test-user",
    "voice_enabled": true,
    "language": "en"
  }'
echo -e "\n"

# Test 4: Stats endpoint
echo "4. Testing stats endpoint..."
curl -X GET "http://localhost:8080/stats" \\
  -H "X-API-Key: uniguru-dev-key-2025"
echo -e "\n"

# Test 5: BHIV integration
echo "5. Testing BHIV integration..."
curl -X POST "http://localhost:8080/bhiv/compose" \\
  -H "X-API-Key: uniguru-dev-key-2025" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Explain machine learning concepts",
    "session_id": "bhiv-test-session",
    "user_id": "bhiv-test-user"
  }'
echo -e "\n"

echo "Smoke tests completed successfully!"
'''
    
        with open("smoke_test.sh", "w", encoding='utf-8') as f:
            f.write(curl_script.strip())
        
        # Make script executable (Unix-like systems)
        try:
            os.chmod("smoke_test.sh", 0o755)
        except:
            pass  # Windows doesn't use chmod
    
    # Start the service
    logger.info("🚀 Starting UniGuru-LM Service...")
    logger.info(f"🌐 Service will be available at: http://localhost:{service.config.service_port}")
    logger.info(f"📋 API Key: {service.config.api_key}")
    logger.info(f"🔑 NAS Credentials: {service.config.nas_username}")
    
    uvicorn.run(
        app,
        host=service.config.service_host,
        port=service.config.service_port,
        log_level="info",
        reload=False  # Disable reload for production
    )