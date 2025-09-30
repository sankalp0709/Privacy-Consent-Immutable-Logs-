#!/usr/bin/env python3
"""
Clean Uniguru-LM Service Startup
Starts the service without creating additional files
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Start Uniguru-LM service cleanly"""
    print("🚀 Starting Uniguru-LM Service (Clean Mode)")
    print("=" * 50)
    
    try:
        # Import and start the service directly
        from uniguru_lm_service import app, service
        import uvicorn
        
        # Display service info
        print(f"✅ Service initialized successfully")
        print(f"🌐 Starting on: http://localhost:{service.config.service_port}")
        print(f"🔑 API Key: {service.config.api_key}")
        print(f"🤖 LLMs: Ollama + Gemini")
        print(f"📚 Knowledge: NAS + File fallback")
        print(f"🎯 Features: Multi-language, RL, TTS")
        print("=" * 50)
        
        # Start the service
        uvicorn.run(
            app,
            host=service.config.service_host,
            port=service.config.service_port,
            log_level="info",
            reload=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")
    except Exception as e:
        print(f"❌ Error starting service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()