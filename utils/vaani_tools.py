#!/usr/bin/env python3
"""
Vaani Tools Integration
Provides comprehensive Vaani Sentinel X integration as tools for agents.
"""

import os
import uuid
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from utils.vaani_client import VaaniClient

logger = get_logger(__name__)

class VaaniTools:
    """Vaani Sentinel X tools for agent integration"""

    def __init__(self):
        # Import config from the main service
        from uniguru_lm_service import UniGuruConfig
        self.config = UniGuruConfig()
        self.vaani_client = VaaniClient(self.config)

    def generate_multilingual_content(self, query: str, target_languages: List[str] = None) -> Dict[str, Any]:
        """Generate content in multiple languages using Vaani"""
        try:
            if not target_languages:
                target_languages = ["hi", "en"]  # Default to Hindi and English

            logger.info(f"🌐 Generating multilingual content for: {query[:50]}...")

            # Generate content using Vaani
            result = self.vaani_client.generate_content(
                text=query,
                platforms=["twitter", "instagram"],
                tone="neutral",
                language="en"
            )

            if "error" not in result:
                # Translate to target languages
                translations = self.vaani_client.translate_content(
                    text=query,
                    target_languages=target_languages,
                    tone="neutral"
                )

                return {
                    "original_content": result,
                    "translations": translations,
                    "languages": target_languages,
                    "method": "vaani_multilingual",
                    "status": "success"
                }
            else:
                return {"error": "Content generation failed", "status": "error"}

        except Exception as e:
            logger.error(f"❌ Multilingual content generation error: {str(e)}")
            return {"error": str(e), "status": "error"}

    def generate_platform_content(self, content: str, platforms: List[str] = None,
                                tone: str = "neutral") -> Dict[str, Any]:
        """Generate platform-specific content using Vaani"""
        try:
            if not platforms:
                platforms = ["twitter", "instagram", "linkedin"]

            logger.info(f"📱 Generating platform content for: {content[:50]}...")

            result = self.vaani_client.generate_content(
                text=content,
                platforms=platforms,
                tone=tone,
                language="en"
            )

            if "error" not in result:
                return {
                    "platform_content": result.get("generated_content", {}),
                    "platforms": platforms,
                    "tone": tone,
                    "method": "vaani_platform",
                    "status": "success"
                }
            else:
                return {"error": "Platform content generation failed", "status": "error"}

        except Exception as e:
            logger.error(f"❌ Platform content generation error: {str(e)}")
            return {"error": str(e), "status": "error"}

    def analyze_content_security(self, content: str) -> Dict[str, Any]:
        """Analyze content security using Vaani"""
        try:
            logger.info(f"🔒 Analyzing content security for: {content[:50]}...")

            result = self.vaani_client.analyze_content_security(content)

            if "error" not in result:
                return {
                    "security_analysis": result,
                    "risk_level": result.get("risk_level", "unknown"),
                    "flags_count": result.get("flags_count", 0),
                    "recommendations": result.get("recommendations", []),
                    "method": "vaani_security",
                    "status": "success"
                }
            else:
                return {"error": "Security analysis failed", "status": "error"}

        except Exception as e:
            logger.error(f"❌ Content security analysis error: {str(e)}")
            return {"error": str(e), "status": "error"}

    def detect_and_translate(self, content: str, target_language: str = "en") -> Dict[str, Any]:
        """Detect language and translate content using Vaani"""
        try:
            logger.info(f"🔍 Detecting language and translating: {content[:50]}...")

            # Detect language
            detection = self.vaani_client.detect_language(content)

            if "error" not in detection:
                detected_lang = detection.get("language", "unknown")

                # Translate if different from target
                if detected_lang != target_language:
                    translation = self.vaani_client.translate_content(
                        text=content,
                        target_languages=[target_language],
                        tone="neutral"
                    )

                    return {
                        "original_content": content,
                        "detected_language": detected_lang,
                        "target_language": target_language,
                        "translation": translation,
                        "method": "vaani_translate",
                        "status": "success"
                    }
                else:
                    return {
                        "original_content": content,
                        "detected_language": detected_lang,
                        "message": "Content already in target language",
                        "method": "vaani_translate",
                        "status": "success"
                    }
            else:
                return {"error": "Language detection failed", "status": "error"}

        except Exception as e:
            logger.error(f"❌ Language detection/translation error: {str(e)}")
            return {"error": str(e), "status": "error"}

    def generate_voice_content(self, content: str, language: str = "hi",
                             tone: str = "devotional") -> Dict[str, Any]:
        """Generate voice content using Vaani"""
        try:
            logger.info(f"🎵 Generating voice content for: {content[:50]}...")

            result = self.vaani_client.generate_voice(
                text=content,
                language=language,
                tone=tone,
                voice_tag=f"{language}_in_female_{tone}"
            )

            if "error" not in result:
                return {
                    "voice_content": result,
                    "language": language,
                    "tone": tone,
                    "voice_tag": f"{language}_in_female_{tone}",
                    "method": "vaani_voice",
                    "status": "success"
                }
            else:
                return {"error": "Voice content generation failed", "status": "error"}

        except Exception as e:
            logger.error(f"❌ Voice content generation error: {str(e)}")
            return {"error": str(e), "status": "error"}

    def get_supported_features(self) -> Dict[str, Any]:
        """Get all supported Vaani features"""
        try:
            platforms = self.vaani_client.get_supported_platforms()
            languages = self.vaani_client.get_supported_languages()

            return {
                "platforms": platforms,
                "languages": languages,
                "features": [
                    "content_generation",
                    "multilingual_processing",
                    "voice_generation",
                    "security_analysis",
                    "language_detection",
                    "translation",
                    "platform_adaptation"
                ],
                "tones": ["formal", "casual", "devotional", "neutral", "uplifting"],
                "method": "vaani_features",
                "status": "success"
            }

        except Exception as e:
            logger.error(f"❌ Error getting supported features: {str(e)}")
            return {"error": str(e), "status": "error"}

# Global Vaani tools instance
vaani_tools = VaaniTools()

def use_vaani_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to use Vaani tools"""
    try:
        if tool_name == "multilingual_content":
            return vaani_tools.generate_multilingual_content(**kwargs)
        elif tool_name == "platform_content":
            return vaani_tools.generate_platform_content(**kwargs)
        elif tool_name == "security_analysis":
            return vaani_tools.analyze_content_security(**kwargs)
        elif tool_name == "translate":
            return vaani_tools.detect_and_translate(**kwargs)
        elif tool_name == "voice_content":
            return vaani_tools.generate_voice_content(**kwargs)
        elif tool_name == "features":
            return vaani_tools.get_supported_features()
        else:
            return {"error": f"Unknown tool: {tool_name}", "status": "error"}

    except Exception as e:
        logger.error(f"❌ Vaani tool error: {str(e)}")
        return {"error": str(e), "status": "error"}