#!/usr/bin/env python3
"""
Vaani Sentinel X Client
Handles authentication and API communication with Vaani Sentinel X service.
"""

import os
import uuid
import requests
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class VaaniClient:
    """Comprehensive client for Vaani Sentinel X service"""

    def __init__(self, config=None):
        self.config = config
        # Use localhost as per documentation, fallback to environment
        self.base_url = os.getenv("VAANI_ENDPOINT", "http://localhost:8000")
        self.username = os.getenv("VAANI_USERNAME", "admin")
        self.password = os.getenv("VAANI_PASSWORD", "secret")
        self.api_key = os.getenv("VAANI_API_KEY", "")
        self.token = None
        self.session = requests.Session()
        self.authenticated = False

        # Try authentication, but don't fail if it doesn't work
        try:
            self._authenticate()
        except Exception as e:
            logger.warning(f"⚠️ Vaani authentication failed during init: {str(e)}")
            logger.info("🔄 Vaani client will work in fallback mode")

    def _authenticate(self):
        """Authenticate with Vaani and get JWT token - Following API documentation"""
        try:
            # Try JWT token authentication first if API key is available
            if self.api_key:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                })
                self.token = self.api_key
                self.authenticated = True
                logger.info("✅ Vaani authenticated with API key")
                return

            # Try username/password authentication following documentation
            auth_url = f"{self.base_url}/api/v1/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }

            logger.info(f"🔐 Attempting Vaani authentication with username: {self.username}")
            logger.info(f"🌐 Auth URL: {auth_url}")

            response = self.session.post(auth_url, json=payload, timeout=30)

            logger.info(f"📡 Auth response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"📄 Auth response data: {data}")

                self.token = data.get("access_token")
                if self.token:
                    # Set authorization header as per documentation
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    })
                    self.authenticated = True
                    logger.info("✅ Vaani authentication successful")
                    logger.info(f"🎫 Token received: {self.token[:20]}...")
                else:
                    logger.error("❌ Vaani authentication response missing access_token")
                    logger.error(f"📄 Full response: {data}")
                    self.authenticated = False
            else:
                logger.warning(f"⚠️ Vaani authentication failed: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.warning(f"❌ Auth error details: {error_data}")
                except:
                    logger.warning(f"❌ Auth error text: {response.text[:200]}")
                logger.info("🔄 Vaani client will work in fallback mode")
                self.authenticated = False

        except Exception as e:
            logger.warning(f"⚠️ Vaani authentication error: {str(e)}")
            logger.info("🔄 Vaani client will work in fallback mode")
            self.authenticated = False

    def _ensure_authenticated(self):
        """Ensure we have a valid token"""
        if not self.authenticated:
            self._authenticate()

    def _create_content_first(self, text: str, content_type: str = "tweet",
                              language: str = "en") -> Optional[str]:
        """Create content first as required by Vaani API - Following documentation exactly"""
        try:
            create_url = f"{self.base_url}/api/v1/content/create"
            payload = {
                "text": text,
                "content_type": content_type,
                "language": language,
                "metadata": {"source": "bhiv_agent"}
            }

            logger.info(f"📝 Creating content with type: {content_type}, language: {language}")
            logger.info(f"📄 Content preview: {text[:100]}...")
            logger.info(f"🔗 Create URL: {create_url}")
            logger.info(f"📨 Payload: {payload}")

            response = self.session.post(create_url, json=payload, timeout=30)

            logger.info(f"📡 Content creation response status: {response.status_code}")
            logger.info(f"📡 Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"📄 Full response data: {data}")

                content_id = data.get("content_id") or data.get("id")
                if content_id:
                    logger.info(f"✅ Content created successfully with ID: {content_id}")
                    logger.info(f"📊 Content details: type={content_type}, language={language}")
                    return content_id
                else:
                    logger.error("❌ Content creation response missing content_id or id")
                    logger.error(f"📄 Available keys: {list(data.keys())}")
                    return None
            else:
                # Log detailed error information
                logger.error(f"❌ Content creation failed with status {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"❌ Error details: {error_details}")
                    logger.error(f"❌ Error detail: {error_details.get('detail', 'No detail provided')}")
                except:
                    logger.error(f"❌ Raw error response: {response.text[:500]}")

                return None

        except Exception as e:
            logger.error(f"❌ Content creation error: {str(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None

    def generate_content(self, text: str, platforms: List[str] = None,
                        tone: str = "neutral", language: str = "en") -> Dict[str, Any]:
        """Generate platform-specific content using Vaani - Based on API documentation"""
        # Check if we're authenticated, if not, provide fallback
        if not self.authenticated:
            logger.warning("⚠️ Vaani not authenticated, using fallback content generation")
            return self._generate_fallback_content(text, platforms, tone, language)

        try:
            # First create content
            content_id = self._create_content_first(text, "tweet", language)
            if not content_id:
                logger.warning("⚠️ Failed to create content, using fallback")
                return self._generate_fallback_content(text, platforms, tone, language)

            # Use the exact API structure from documentation
            generate_url = f"{self.base_url}/api/v1/agents/generate-content"
            generate_payload = {
                "content_id": content_id,
                "platforms": platforms or ["twitter", "instagram", "linkedin"],
                "tone": tone,
                "language": language
            }

            logger.info(f"📱 Generating content for platforms: {platforms or ['twitter', 'instagram', 'linkedin']}")
            logger.info(f"🎭 Using tone: {tone}, language: {language}")

            generate_response = self.session.post(
                generate_url,
                json=generate_payload,
                timeout=60
            )

            logger.info(f"📡 Vaani generate-content response status: {generate_response.status_code}")

            if generate_response.status_code == 200:
                result = generate_response.json()
                logger.info("✅ Vaani content generation successful")

                # Validate response structure matches documentation
                if "generated_content" in result:
                    logger.info(f"📦 Generated content for platforms: {list(result['generated_content'].keys())}")
                else:
                    logger.warning("⚠️ Response missing 'generated_content' field")

                return result
            else:
                # Log detailed error information
                try:
                    error_details = generate_response.json()
                    logger.error(f"❌ Vaani API error details: {error_details}")
                    logger.error(f"❌ Error detail: {error_details.get('detail', 'No detail provided')}")
                except:
                    logger.error(f"❌ Vaani API error (no JSON): {generate_response.text[:500]}")

                logger.warning("⚠️ Vaani API failed, using fallback content generation")
                return self._generate_fallback_content(text, platforms, tone, language)

        except Exception as e:
            logger.error(f"❌ Vaani content generation error: {str(e)}")
            logger.warning("⚠️ Using fallback content generation")
            return self._generate_fallback_content(text, platforms, tone, language)

    def _generate_fallback_content(self, text: str, platforms: List[str] = None,
                                  tone: str = "neutral", language: str = "en") -> Dict[str, Any]:
        """Generate fallback content when Vaani API is not available"""
        try:
            platforms = platforms or ["twitter", "instagram", "linkedin"]

            # Simple content adaptation based on platform
            generated_content = {}

            for platform in platforms:
                if platform.lower() == "twitter":
                    # Twitter has character limits
                    content = text[:240] if len(text) > 240 else text
                    generated_content["twitter"] = {
                        "content": content,
                        "tone": tone,
                        "language": language,
                        "platform": "twitter",
                        "character_count": len(content)
                    }
                elif platform.lower() == "instagram":
                    # Instagram can be longer
                    content = text
                    generated_content["instagram"] = {
                        "content": content,
                        "tone": tone,
                        "language": language,
                        "platform": "instagram",
                        "hashtags": ["#AI", "#Technology"]  # Add some default hashtags
                    }
                elif platform.lower() == "linkedin":
                    # LinkedIn professional tone
                    content = f"Professional Insight: {text}"
                    generated_content["linkedin"] = {
                        "content": content,
                        "tone": "professional",
                        "language": language,
                        "platform": "linkedin"
                    }
                else:
                    # Generic content for other platforms
                    generated_content[platform] = {
                        "content": text,
                        "tone": tone,
                        "language": language,
                        "platform": platform
                    }

            logger.info(f"✅ Generated fallback content for platforms: {list(generated_content.keys())}")

            return {
                "generated_content": generated_content,
                "fallback": True,
                "message": "Content generated using fallback method - Vaani API not available"
            }

        except Exception as e:
            logger.error(f"❌ Fallback content generation error: {str(e)}")
            return {"error": f"Fallback content generation failed: {str(e)}"}

    def translate_content(self, text: str, target_languages: List[str],
                        tone: str = "neutral") -> Dict[str, Any]:
        """Translate content using Vaani - Based on API documentation"""
        self._ensure_authenticated()

        try:
            # Create content first
            content_id = self._create_content_first(text, "tweet", "en")
            if not content_id:
                return {"error": "Failed to create content"}

            # Use the exact API structure from documentation
            translate_url = f"{self.base_url}/api/v1/multilingual/translate"
            translate_payload = {
                "content_id": content_id,
                "target_languages": target_languages,
                "tone": tone
            }

            logger.info(f"🌐 Translating content to languages: {target_languages}")
            logger.info(f"🎭 Using tone: {tone}")

            translate_response = self.session.post(
                translate_url,
                json=translate_payload,
                timeout=60
            )

            logger.info(f"📡 Vaani translate response status: {translate_response.status_code}")

            if translate_response.status_code == 200:
                result = translate_response.json()
                logger.info("✅ Vaani translation successful")

                # Validate response structure
                if "translations" in result or "translated_content" in result:
                    logger.info(f"📦 Generated translations for languages: {target_languages}")
                else:
                    logger.warning("⚠️ Response missing translation fields")

                return result
            else:
                # Log detailed error information
                try:
                    error_details = translate_response.json()
                    logger.error(f"❌ Vaani translation API error details: {error_details}")
                    logger.error(f"❌ Error detail: {error_details.get('detail', 'No detail provided')}")
                except:
                    logger.error(f"❌ Vaani translation API error (no JSON): {translate_response.text[:500]}")

                return {"error": f"Translation failed with status {translate_response.status_code}"}

        except Exception as e:
            logger.error(f"❌ Vaani translation error: {str(e)}")
            return {"error": str(e)}

    def generate_voice(self, text: str, language: str = "hi",
                      tone: str = "devotional", voice_tag: str = "hi_in_female_devotional") -> Dict[str, Any]:
        """Generate voice content using Vaani"""
        self._ensure_authenticated()

        try:
            # Create content first
            content_id = self._create_content_first(text, "voice_script", language)
            if not content_id:
                return {"error": "Failed to create content"}

            # Generate voice
            voice_url = f"{self.base_url}/api/v1/agents/generate-voice"
            voice_payload = {
                "content_id": content_id,
                "language": language,
                "tone": tone,
                "voice_tag": voice_tag
            }

            voice_response = self.session.post(voice_url, json=voice_payload, timeout=60)

            if voice_response.status_code == 200:
                result = voice_response.json()
                logger.info("✅ Vaani voice generation successful")
                return result
            else:
                logger.error(f"❌ Vaani voice generation failed: {voice_response.status_code}")
                return {"error": "Voice generation failed"}

        except Exception as e:
            logger.error(f"❌ Vaani voice generation error: {str(e)}")
            return {"error": str(e)}

    def analyze_content_security(self, text: str) -> Dict[str, Any]:
        """Analyze content security using Vaani"""
        self._ensure_authenticated()

        try:
            # Create content first
            content_id = self._create_content_first(text, "tweet", "en")
            if not content_id:
                return {"error": "Failed to create content"}

            # Analyze security
            security_url = f"{self.base_url}/api/v1/security/analyze-content"
            security_payload = {"content_id": content_id}

            security_response = self.session.post(security_url, json=security_payload, timeout=30)

            if security_response.status_code == 200:
                result = security_response.json()
                logger.info("✅ Vaani security analysis successful")
                return result
            else:
                logger.error(f"❌ Vaani security analysis failed: {security_response.status_code}")
                return {"error": "Security analysis failed"}

        except Exception as e:
            logger.error(f"❌ Vaani security analysis error: {str(e)}")
            return {"error": str(e)}

    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language using Vaani"""
        self._ensure_authenticated()

        try:
            detect_url = f"{self.base_url}/api/v1/multilingual/detect-language"
            payload = {"content": text}

            response = self.session.post(detect_url, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Vaani language detection successful")
                return result
            else:
                logger.error(f"❌ Vaani language detection failed: {response.status_code}")
                return {"error": "Language detection failed"}

        except Exception as e:
            logger.error(f"❌ Vaani language detection error: {str(e)}")
            return {"error": str(e)}

    async def generate_audio(self, text: str, language: str = "hi",
                            voice: str = "female") -> Optional[str]:
        """Generate audio using Vaani TTS (legacy method for compatibility)"""
        try:
            # Use the new voice generation method
            voice_result = self.generate_voice(text, language, "devotional", f"{language}_in_female_devotional")

            if "error" not in voice_result:
                # Return a mock URL for now (Vaani might provide actual audio URL)
                audio_id = str(uuid.uuid4())
                return f"/audio/{audio_id}.wav"
            else:
                logger.warning("⚠️ Vaani voice generation failed, using fallback")
                return None

        except Exception as e:
            logger.error(f"❌ Error generating audio: {str(e)}")
            return None

    def get_supported_platforms(self) -> List[str]:
        """Get supported platforms from Vaani"""
        self._ensure_authenticated()

        try:
            platforms_url = f"{self.base_url}/api/v1/agents/platforms"
            response = self.session.get(platforms_url, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                # Return default platforms
                return ["twitter", "instagram", "linkedin", "spotify"]

        except Exception as e:
            logger.error(f"❌ Error getting platforms: {str(e)}")
            return ["twitter", "instagram", "linkedin", "spotify"]

    def get_supported_languages(self) -> List[str]:
        """Get supported languages from Vaani"""
        self._ensure_authenticated()

        try:
            languages_url = f"{self.base_url}/api/v1/agents/languages"
            response = self.session.get(languages_url, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                # Return default languages
                return ["en", "hi", "sa", "mr", "gu", "ta", "te", "kn", "ml", "bn"]

        except Exception as e:
            logger.error(f"❌ Error getting languages: {str(e)}")
            return ["en", "hi", "sa", "mr", "gu", "ta", "te", "kn", "ml", "bn"]