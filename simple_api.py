#!/usr/bin/env python3
"""
Simple Orchestration API - Three endpoints with GET and POST methods
Integrates with RAG API for knowledge retrieval and Groq for AI-powered answers
"""

import os
import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Local imports
from utils.logger import get_logger
from utils.rag_client import rag_client
from compliance.api import router as compliance_router  # Import compliance router
from compliance.consent_manager import consent_manager
from compliance.audit_logger import audit_logger

logger = get_logger(__name__)

class ModelProvider:
    def __init__(self, model_config: Dict[str, Any], endpoint: str):
        # Read Ollama settings from environment for production usage
        self.model_name = os.getenv("OLLAMA_MODEL", model_config.get("model_name", "llama3.1"))
        # Default to local Ollama; can be overridden by env
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.endpoint = endpoint
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))
        logger.info(f"Initialized Ollama model: {self.model_name} for {self.endpoint} at {self.ollama_url}")
    
    def generate_response(self, prompt: str, fallback: str) -> str:
        """Generate response using Ollama API"""
        import requests
        
        try:
            # Prepare the request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            # Make the API call
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=self.timeout
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                return result.get("response", fallback)
            else:
                logger.warning(f"Ollama API returned status code {response.status_code}")
                return fallback
                
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return fallback

class SimpleOrchestrationEngine:
    """Simple orchestration engine for handling different types of queries"""
    
    def __init__(self):
        # Initialize model providers for each endpoint
        self.model_providers = {
            "ask-vedas": ModelProvider({"model_name": "llama3.1"}, "ask-vedas"),
            "edumentor": ModelProvider({"model_name": "llama3.1"}, "edumentor"),
            "wellness": ModelProvider({"model_name": "llama3.1"}, "wellness")
        }
        
        # Initialize vector stores
        self.vector_stores = {}
        
        logger.info("SimpleOrchestrationEngine initialized")
    
    def initialize_vector_stores(self):
        """Initialize vector stores for document retrieval"""
        logger.info("Vector stores initialized")
    
    def generate_response(self, prompt: str, fallback: str, endpoint: str) -> tuple[str, int]:
        return self.model_providers[endpoint].generate_response(prompt, fallback)
    
    def search_documents(self, query: str, store_type: str = "unified") -> list:
        """Search documents using RAG API"""
        try:
            logger.info(f"🔍 Searching RAG API for: '{query}'")

            # Query the RAG API
            rag_result = rag_client.query(query, top_k=3)

            if rag_result["status"] == 200 and rag_result.get("response"):
                # Format results to match expected structure
                formatted_results = [
                    {
                        "text": chunk["content"][:500],
                        "source": chunk["source"],
                        "groq_answer": rag_result.get("groq_answer", "")  # Include groq_answer in first result
                    }
                    for chunk in rag_result["response"]
                ]
                logger.info(f"RAG API found {len(formatted_results)} results for '{query}'")
                return formatted_results
            else:
                logger.warning("⚠️ RAG API returned no results")
                return []

        except Exception as e:
            logger.error(f"RAG API search error: {str(e)}")

            # Fallback to file-based retriever if RAG API fails
            try:
                from utils.file_based_retriever import file_retriever
                results = file_retriever.search(query, limit=3)
                formatted_results = [{"text": doc["text"][:500], "source": doc.get("source", "file_based_kb")} for doc in results]
                logger.info(f"File-based retriever found {len(formatted_results)} results")
                return formatted_results
            except Exception as fallback_error:
                logger.error(f"File-based retriever error: {str(fallback_error)}")
                return []

# Global engine instance
engine = SimpleOrchestrationEngine()

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"

class SimpleResponse(BaseModel):
    query_id: str
    query: str
    response: str
    sources: list
    timestamp: str
    endpoint: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Simple Orchestration API...")
    engine.initialize_vector_stores()
    logger.info("Simple Orchestration API ready with RAG integration!")
    yield
    logger.info("Shutting down Simple Orchestration API...")

app = FastAPI(
    title="Simple Orchestration API",
    description="Three simple endpoints: ask-vedas, edumentor, wellness with GET and POST methods",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the compliance router
app.include_router(compliance_router)

# Health check data
health_data = {
    "startup_time": datetime.now(),
    "total_requests": 0,
    "successful_requests": 0
}

# ==================== ASK-VEDAS ENDPOINTS ====================

@app.get("/ask-vedas")
async def ask_vedas_get(
    query: str = Query(..., description="Your spiritual question"),
    user_id: str = Query("anonymous", description="User ID")
):
    """GET method for Vedas spiritual wisdom"""
    return await process_vedas_query(query, user_id)

@app.post("/ask-vedas")
async def ask_vedas_post(request: QueryRequest):
    """POST method for Vedas spiritual wisdom"""
    return await process_vedas_query(request.query, request.user_id)

async def process_vedas_query(query: str, user_id: str):
    """Process Vedas query and return spiritual wisdom"""
    try:
        # Update health check data
        health_data["total_requests"] += 1
        
        # Search relevant documents
        sources = engine.search_documents(query, "vedas")
        context = "\n".join([doc["text"] for doc in sources[:2]])
        
        # Generate response
        prompt = f"""You are a wise spiritual teacher. Based on ancient Vedic wisdom, provide profound guidance for this question: "{query}"

Context from sacred texts:
{context}

Respond with deep spiritual insights in a compassionate, wise tone. Include relevant Sanskrit terms where appropriate.
"""
        
        fallback = f"Thank you for your spiritual question about '{query}'. The ancient Vedic texts offer profound wisdom on this topic. They teach us that inner peace comes from understanding our true nature beyond material existence. The concept of 'Sat-Chit-Ananda' (existence-consciousness-bliss) reminds us that our essence is divine. I recommend reflecting on this question during meditation, as the answers often emerge from within. May you find the wisdom you seek on your spiritual journey."
        
        response_text = engine.generate_response(prompt, fallback, "ask-vedas")
        
        # Update successful requests count
        health_data["successful_requests"] += 1
        
        return SimpleResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            response=response_text,
            sources=sources,
            timestamp=datetime.now().isoformat(),
            endpoint="ask-vedas"
        )
        
    except Exception as e:
        logger.error(f"Error in ask-vedas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== EDUMENTOR ENDPOINTS ====================

@app.get("/edumentor")
async def edumentor_get(
    query: str = Query(..., description="Your educational question"),
    user_id: str = Query("anonymous", description="User ID")
):
    """GET method for educational content"""
    return await process_edumentor_query(query, user_id)

@app.post("/edumentor")
async def edumentor_post(request: QueryRequest):
    """POST method for educational content"""
    return await process_edumentor_query(request.query, request.user_id)

async def process_edumentor_query(query: str, user_id: str):
    """Process educational query and return learning content"""
    try:
        # Update health check data
        health_data["total_requests"] += 1
        
        # Search relevant documents
        sources = engine.search_documents(query, "education")
        context = "\n".join([doc["text"] for doc in sources[:2]])
        
        # Generate response
        prompt = f"""You are an expert educational mentor. Provide clear, informative guidance for this question: "{query}"

Reference material:
{context}

Respond with educational insights in a clear, structured format. Include examples and analogies to aid understanding.
"""
        
        fallback = f"Thank you for your question about '{query}'. This is an interesting educational topic. When approaching this subject, it's helpful to break it down into key components. First, understand the fundamental concepts. Then, explore how these concepts connect to form a broader understanding. Learning is most effective when we relate new information to what we already know. I encourage you to explore this topic further through practice and application, as that's how knowledge becomes truly meaningful."
        
        response_text = engine.generate_response(prompt, fallback, "edumentor")
        
        # Update successful requests count
        health_data["successful_requests"] += 1
        
        return SimpleResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            response=response_text,
            sources=sources,
            timestamp=datetime.now().isoformat(),
            endpoint="edumentor"
        )
        
    except Exception as e:
        logger.error(f"Error in edumentor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WELLNESS ENDPOINTS ====================

@app.get("/wellness")
async def wellness_get(
    query: str = Query(..., description="Your wellness question"),
    user_id: str = Query("anonymous", description="User ID")
):
    """GET method for wellness advice"""
    return await process_wellness_query(query, user_id)

@app.post("/wellness")
async def wellness_post(request: QueryRequest):
    """POST method for wellness advice"""
    return await process_wellness_query(request.query, request.user_id)

async def process_wellness_query(query: str, user_id: str):
    """Process wellness query and return health advice"""
    try:
        # Update health check data
        health_data["total_requests"] += 1
        
        # Search relevant documents
        sources = engine.search_documents(query, "wellness")
        context = "\n".join([doc["text"] for doc in sources[:2]])
        
        # Generate response
        prompt = f"""You are a compassionate wellness guide. Provide holistic health advice for this question: "{query}"

Reference material:
{context}

Respond with balanced wellness insights that address physical, mental, and emotional aspects. Use a supportive, encouraging tone.
"""
        
        fallback = f"Thank you for reaching out about '{query}'. It's important to take care of your wellbeing. Here are some gentle suggestions: Take time for self-care, practice deep breathing, stay connected with supportive people, and remember that small steps can lead to big improvements. If you're facing significant challenges, consider speaking with a healthcare professional who can provide personalized guidance. Wellness is a journey, not a destination, and each day offers a new opportunity to nurture yourself."
        
        response_text = engine.generate_response(prompt, fallback, "wellness")
        
        # Update successful requests count
        health_data["successful_requests"] += 1
        
        return SimpleResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            response=response_text,
            sources=sources,
            timestamp=datetime.now().isoformat(),
            endpoint="wellness"
        )
        
    except Exception as e:
        logger.error(f"Error in wellness: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HEALTH CHECK ENDPOINT ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - health_data["startup_time"]).total_seconds()
    
    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "total_requests": health_data["total_requests"],
        "successful_requests": health_data["successful_requests"],
        "success_rate": health_data["successful_requests"] / health_data["total_requests"] if health_data["total_requests"] > 0 else 0,
        "timestamp": datetime.now().isoformat()
    }

# ==================== ROOT ENDPOINT ====================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Simple Orchestration API",
        "version": "1.0.0",
        "endpoints": {
            "ask-vedas": {
                "GET": "/ask-vedas?query=your_question&user_id=optional",
                "POST": "/ask-vedas with JSON body"
            },
            "edumentor": {
                "GET": "/edumentor?query=your_question&user_id=optional", 
                "POST": "/edumentor with JSON body"
            },
            "wellness": {
                "GET": "/wellness?query=your_question&user_id=optional",
                "POST": "/wellness with JSON body"
            },
            "compliance": {
                "GET/POST": "/compliance/consent - Manage user consent",
                "GET": "/compliance/consent/{employee_id} - Get specific consent",
                "POST": "/compliance/audit-logs - Access audit logs",
                "POST": "/compliance/apply-retention - Apply retention policies"
            }
        },
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser(description="Simple Orchestration API")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on (default: 0.0.0.0)")
    args = parser.parse_args()
    print("\n" + "="*60)
    print("  SIMPLE ORCHESTRATION API")
    print("="*60)
    print(f" Server URL: http://{args.host}:{args.port}")
    print(f" API Documentation: http://{args.host}:{args.port}/docs")
    print("\n Endpoints:")
    print("   GET/POST /ask-vedas - Spiritual wisdom")
    print("   GET/POST /edumentor - Educational content")
    print("   GET/POST /wellness - Health advice")
    print("   GET/POST /compliance/* - Privacy & audit controls")
    print("="*60)
    uvicorn.run(app, host=args.host, port=args.port)
# ==================== STARTUP TASKS ====================

@app.on_event("startup")
async def start_retention_worker():
    async def retention_worker():
        retention_days = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "90"))
        while True:
            try:
                # Apply consent retention
                consent_deleted = consent_manager.apply_retention_policy()
                # Apply audit log retention
                result = audit_logger.apply_retention_policy(retention_days=retention_days)
                logs_deleted = result.get("logs_deleted", 0)
                # Log a summary event
                audit_logger.log_access(
                    actor="system",
                    action="daily_retention",
                    resource="system",
                    reason="scheduled",
                    purpose="retention_enforcement",
                    via_endpoint="startup_worker",
                    extra={
                        "consent_records_deleted": consent_deleted,
                        "log_files_deleted": logs_deleted,
                        "retention_days": retention_days
                    }
                )
            except Exception as e:
                logger.error(f"Retention worker error: {e}")
            # Sleep ~24 hours
            await asyncio.sleep(24 * 60 * 60)

    asyncio.create_task(retention_worker())
