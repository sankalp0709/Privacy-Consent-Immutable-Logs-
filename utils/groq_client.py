#!/usr/bin/env python3
"""
Groq API Client for LLM Enhancement
Provides professional LLM enhancement for all agents with proper error handling.
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

class GroqClient:
    """Professional Groq API client for LLM enhancement."""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.base_url = base_url or "https://api.groq.com/openai/v1"
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.timeout = int(os.getenv("GROQ_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("GROQ_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("GROQ_RETRY_DELAY", "1.0"))

        if not self.api_key:
            logger.warning("⚠️ GROQ_API_KEY not found in environment variables")
        else:
            logger.info(f"✅ Groq client initialized with model: {self.model}")

    def generate_response(self, prompt: str, max_tokens: int = 1000,
                         temperature: float = 0.7) -> Tuple[str, bool]:
        """
        Generate response using Groq API with retry logic.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Creativity parameter (0.0 to 1.0)

        Returns:
            Tuple of (response_text, success_boolean)
        """
        if not self.api_key:
            logger.error("❌ GROQ_API_KEY not configured")
            return "", False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "stream": False
        }

        for attempt in range(self.max_retries):
            try:
                logger.info(f"🤖 Calling Groq API (attempt {attempt + 1}/{self.max_retries})")

                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and result["choices"]:
                        content = result["choices"][0]["message"]["content"]
                        logger.info("✅ Groq response generated successfully")
                        return content.strip(), True
                    else:
                        logger.warning("⚠️ No choices in Groq response")
                        return "", False

                elif response.status_code == 429:  # Rate limit
                    logger.warning(f"⚠️ Rate limit hit, retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue

                else:
                    logger.error(f"❌ Groq API error: {response.status_code} - {response.text}")
                    return "", False

            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ Groq API timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return "", False

            except Exception as e:
                logger.error(f"❌ Groq API exception: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return "", False

        logger.error("❌ All Groq API attempts failed")
        return "", False

    def enhance_with_persona(self, agent_name: str, query: str,
                           knowledge_context: str = "") -> Tuple[str, bool]:
        """
        Enhance response with agent-specific persona.

        Args:
            agent_name: Name of the agent (vedas_agent, edumentor_agent, etc.)
            query: User's query
            knowledge_context: Knowledge base context (optional)

        Returns:
            Tuple of (enhanced_response, success_boolean)
        """
        # Define agent personas
        personas = {
            "vedas_agent": {
                "role": "Vedic Wisdom Guide",
                "style": "spiritual, wise, compassionate, traditional",
                "prefix": "As a guide to Vedic wisdom and spiritual knowledge",
                "enhancement": "Draw from ancient Vedic teachings, Bhagavad Gita, Upanishads, and spiritual principles"
            },
            "edumentor_agent": {
                "role": "Educational Mentor",
                "style": "patient, encouraging, structured, knowledgeable",
                "prefix": "As an educational mentor and guide",
                "enhancement": "Focus on clear explanations, learning objectives, and practical applications"
            },
            "wellness_agent": {
                "role": "Wellness Advisor",
                "style": "caring, holistic, balanced, supportive",
                "prefix": "As a wellness and health advisor",
                "enhancement": "Consider physical, mental, emotional, and spiritual well-being"
            },
            "knowledge_agent": {
                "role": "Knowledge Facilitator",
                "style": "comprehensive, accurate, helpful, informative",
                "prefix": "As a knowledge base specialist",
                "enhancement": "Provide thorough, well-structured information with proper context"
            }
        }

        persona = personas.get(agent_name, personas["knowledge_agent"])

        # Build enhancement prompt
        prompt = f"""{persona['prefix']}, I need to provide a helpful response to: "{query}"

{persona['enhancement']}

{f'Knowledge Context: {knowledge_context}' if knowledge_context else 'Please provide comprehensive information on this topic.'}

Please respond in a {persona['style']} manner that is:
- Professional and respectful
- Comprehensive but concise
- Helpful and actionable
- Culturally appropriate

Response:"""

        return self.generate_response(prompt, max_tokens=1500, temperature=0.7)

    def health_check(self) -> Dict[str, Any]:
        """Check Groq API health and availability."""
        health_status = {
            "service": "groq_api",
            "available": False,
            "model": self.model,
            "configured": bool(self.api_key),
            "response_time": None,
            "error": None
        }

        if not self.api_key:
            health_status["error"] = "API key not configured"
            return health_status

        try:
            start_time = time.time()
            # Simple test prompt
            test_prompt = "Hello, this is a test message. Please respond with 'OK'."
            response, success = self.generate_response(test_prompt, max_tokens=10)

            health_status["response_time"] = round(time.time() - start_time, 2)
            health_status["available"] = success

            if not success:
                health_status["error"] = "API call failed"

        except Exception as e:
            health_status["error"] = str(e)

        return health_status


# Global instance
groq_client = GroqClient()