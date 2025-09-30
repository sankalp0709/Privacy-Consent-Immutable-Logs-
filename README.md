📋 API Key: uniguru-dev-key-2025
### BHIV Core - Ultimate AI Agent System

An advanced multi-modal AI pipeline featuring **Vaani Sentinel X integration**, external RAG API with Groq-powered answers, reinforcement learning, comprehensive knowledge retrieval, production-ready FastAPI services, web interface, and enhanced CLI.

> **Note:** This system integrates multiple AI technologies including Groq, Gemini, Ollama, and Vaani Sentinel X for comprehensive content generation and knowledge retrieval.

### Key Features
- **🤖 Multi-Agent System**: Specialized agents for education, wellness, spiritual guidance, and knowledge retrieval
- **🌐 Vaani Sentinel X Integration**: Complete AI content generation suite with multilingual support, platform adaptation, voice synthesis, and security analysis
- **🧠 External RAG API + Groq**: Advanced knowledge retrieval with AI-powered answers
- **🎯 Reinforcement Learning**: Adaptive agent/model selection with comprehensive logging and analytics
- **📱 Multi-Modal Processing**: Text, PDF, image, audio, and voice content generation
- **🔄 Intelligent Fallbacks**: Robust fallback mechanisms for all services
- **📊 Web Dashboard**: Authenticated uploads, real-time monitoring, and analytics
- **💻 Enhanced CLI**: Single/batch processing with multiple output formats
- **🛡️ Production Ready**: Health monitoring, MongoDB logging, error handling, and Docker deployment
- **🎵 Voice Integration**: Real-time voice content generation with multiple languages and tones
- **🔒 Content Security**: Automatic safety analysis and compliance checking

### What's New in Latest Version
- **🤖 Advanced Multi-Agent System**: Specialized agents with intelligent Vaani tool integration
- **🌐 Vaani Sentinel X Integration**: Complete AI content generation with 10+ languages, platform adaptation, voice synthesis
- **🧠 Groq + External RAG API**: AI-powered knowledge retrieval with intelligent answers
- **🎵 Real-Time Voice Generation**: Multiple languages, tones, and voice options
- **🔒 Content Security Analysis**: Automatic safety checking and compliance
- **📱 Platform-Optimized Content**: Twitter, Instagram, LinkedIn, Spotify integration
- **🎯 Intelligent Agent Selection**: RL-powered agent routing based on query context
- **📊 Enhanced Analytics**: Comprehensive logging, performance metrics, and insights
- **🔄 Robust Fallback System**: Multiple fallback layers for all services
- **🚀 Production-Ready Architecture**: Docker deployment, health monitoring, error handling

### Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                        🌐 BHIV Core System                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  Web Interface  │  │   CLI Runner    │  │  Simple API     │     │
│  │   (Port 8003)   │  │  (Enhanced)     │  │  (Port 8001)    │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│           │                        │                        │      │
│           └─────────────┬───────────┴────────────┬───────────┘      │
│                         │                        │                  │
│            ┌────────────▼────────────┐  ┌────────▼────────────┐     │
│            │      MCP Bridge         │  │   External RAG      │     │
│            │    (Port 8002)          │  │   API + Groq        │     │
│            │  ┌─────────────────┐    │  │  ┌─────────────┐    │     │
│            │  │ Agent Registry  │    │  │  │  Knowledge  │    │     │
│            │  │     + RL        │    │  │  │  Retrieval  │    │     │
│            │  └─────────────────┘    │  │  └─────────────┘    │     │
│            └─────────────────────────┘  └─────────────────────┘     │
│                         │                                           │
│            ┌────────────▼────────────────────────────────────────────┐
│            │                 🤖 MULTI-AGENT SYSTEM                  │
│            ├─────────────────────────────────────────────────────────┤
│            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│            │  │ 🕉️ Vedas    │  │ 🎓 EduMentor │  │ 🌿 Wellness │     │
│            │  │   Agent     │  │   Agent      │  │   Agent     │     │
│            │  └─────────────┘  └─────────────┘  └─────────────┘     │
│            │                                                         │
│            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│            │  │ 📚 Knowledge │  │ 🖼️ Image     │  │ 🎵 Audio     │     │
│            │  │   Agent     │  │   Agent      │  │   Agent     │     │
│            │  └─────────────┘  └─────────────┘  └─────────────┘     │
│            └─────────────────────────────────────────────────────────┘
│                         │                                           │
│            ┌────────────▼────────────────────────────────────────────┐
│            │            🎯 VAANI SENTINEL X INTEGRATION              │
│            ├─────────────────────────────────────────────────────────┤
│            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│            │  │ 🌐 Multi-   │  │ 📱 Platform │  │ 🎵 Voice     │     │
│            │  │   lingual   │  │   Content   │  │   Content   │     │
│            │  └─────────────┘  └─────────────┘  └─────────────┘     │
│            │                                                         │
│            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│            │  │ 🔒 Security  │  │ 📊 Analytics│  │ 🎯 Auto-    │     │
│            │  │   Analysis   │  │   & Insights│  │   Detection │     │
│            │  └─────────────┘  └─────────────┘  └─────────────┘     │
│            └─────────────────────────────────────────────────────────┘
│                         │                                           │
│            ┌────────────▼────────────────────────────────────────────┐
│            │              🔧 SUPPORTING INFRASTRUCTURE               │
│            ├─────────────────────────────────────────────────────────┤
│            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│            │  │ 🗄️ MongoDB  │  │ 📝 Logging  │  │ 🔄 RL       │     │
│            │  │   Storage   │  │   System    │  │   Engine    │     │
│            │  └─────────────┘  └─────────────┘  └─────────────┘     │
│            └─────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────┘
```

## 🤖 Agent System Overview

### Core Agents

#### 🕉️ **VedasAgent**
**Purpose**: Spiritual guidance and Vedic wisdom
**Capabilities**:
- Multilingual spiritual content (Hindi, Sanskrit, Marathi)
- Devotional voice generation for mantras and chants
- Platform-adapted spiritual posts for social media
- Cultural context preservation and translation
- Sacred text analysis and interpretation

**Usage Examples**:
```bash
# Spiritual guidance in Hindi with voice
python cli_runner.py explain "dharma in Hindi with devotional voice" vedas_agent

# Social media spiritual content
python cli_runner.py create "Share Bhagavad Gita wisdom on Instagram" vedas_agent
```

#### 🎓 **EduMentorAgent**
**Purpose**: Educational content creation and learning support
**Capabilities**:
- Platform-specific educational content (Twitter, Instagram, LinkedIn)
- Multilingual educational materials (10+ Indian languages)
- Content security analysis for student safety
- Interactive learning content generation
- Academic content adaptation

**Usage Examples**:
```bash
# Educational content for Twitter
python cli_runner.py explain "Machine learning basics for Twitter" edumentor_agent

# Safe educational content
python cli_runner.py create "Student-safe AI explanation in Hindi" edumentor_agent
```

#### 🌿 **WellnessAgent**
**Purpose**: Mental health and wellness guidance
**Capabilities**:
- Guided meditation voice content generation
- Uplifting wellness posts for social media
- Secure mental health content handling
- Stress management and mindfulness content
- Holistic wellness recommendations

**Usage Examples**:
```bash
# Guided meditation with voice
python cli_runner.py create "Guided meditation for stress relief" wellness_agent

# Wellness content for Instagram
python cli_runner.py explain "Daily wellness tips for Instagram" wellness_agent
```

#### 📚 **KnowledgeAgent**
**Purpose**: Comprehensive knowledge retrieval and analysis
**Capabilities**:
- External RAG API integration with Groq enhancement
- Multi-source knowledge synthesis
- Intelligent answer generation
- Fallback to file-based retrieval
- Cross-domain knowledge integration

**Usage Examples**:
```bash
# Knowledge retrieval with AI enhancement
python cli_runner.py query "Explain quantum computing" knowledge_agent

# Multi-source analysis
python cli_runner.py analyze "Compare different AI approaches" knowledge_agent
```

#### 🖼️ **ImageAgent**
**Purpose**: Image analysis and description
**Capabilities**:
- Advanced image understanding
- Detailed image descriptions
- Visual content analysis
- Image-based learning content
- Accessibility support

#### 🎵 **AudioAgent**
**Purpose**: Audio processing and transcription
**Capabilities**:
- Speech-to-text transcription
- Audio content analysis
- Voice synthesis integration
- Audio-based learning content
- Multi-language audio processing

### Agent Selection Intelligence

The system uses **Reinforcement Learning** to automatically select the best agent based on:
- **Query Content Analysis**: Keywords, context, and intent detection
- **Language Detection**: Automatic language routing for multilingual content
- **Platform Requirements**: Social media platform optimization
- **Content Type**: Text, voice, or multimedia requirements
- **Security Context**: Safe content generation for sensitive topics

## Quick Start

### Prerequisites
- Python 3.11+
- Optional: MongoDB 5.0+ for logging/analytics
- Optional: Docker for vector DBs/services

### Install
```bash
git clone <repository-url>
cd BHIV-Third-Installment
python -m venv .venv && .venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
# Optional NLP model
python -m spacy download en_core_web_sm
```

### Environment Setup

#### 1. Copy Environment Template
```bash
cp .env.example .env
```

#### 2. Configure Your API Keys
Edit the `.env` file and add your actual API keys:
```env
# 🤖 Required AI API Keys
GROQ_API_KEY=gsk_your_actual_groq_key_here
GEMINI_API_KEY=AIzaSy_your_actual_gemini_key_here

# 🔄 Optional API Keys (for fallback)
GEMINI_API_KEY_BACKUP=your_backup_gemini_key_here
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.1

# 🎯 Vaani Sentinel X Configuration
VAANI_USERNAME=admin
VAANI_PASSWORD=secret
VAANI_ENDPOINT=https://vaani-sentinel-gs6x.onrender.com
MOCK_VAANI_TTS=false
```

#### 3. Configure Other Settings
```env
# MongoDB (optional)
MONGO_URI=mongodb://localhost:27017/bhiv_core

# RAG API Configuration (Primary knowledge retrieval)
RAG_API_URL=https://819d053306f2.ngrok-free.app/rag
RAG_DEFAULT_TOP_K=5
RAG_TIMEOUT=30

# Reinforcement Learning
USE_RL=true
RL_EXPLORATION_RATE=0.2

# Ollama (optional fallback)
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.1
```

#### ⚠️ Security Warning
- **Never commit actual API keys** to version control
- The `.env` file is automatically ignored by `.gitignore`
- Use `.env.example` as a template for required environment variables
- Keep your API keys secure and rotate them regularly

> **Important**: The RAG API is now the primary knowledge retrieval method. The system will automatically fall back to local file-based retrieval if the RAG API is unavailable.

### Run Services (recommended ports)
```powershell
# Terminal 1: Simple API (agents, KB endpoints)
python simple_api.py --port 8001

# Terminal 2: MCP Bridge (task router, RL, registry)
python mcp_bridge.py  # serves on port 8002

# Terminal 3: Web Interface (auth: admin/secret, user/secret)
python integration/web_interface.py  # serves on port 8003
```

### Endpoints
- Web UI: `http://localhost:8003`
- MCP Bridge health: `http://localhost:8002/health`
- Simple API docs: `http://localhost:8001/docs`

## Usage

### CLI Usage Examples

#### 🤖 **Multi-Agent CLI Commands**

```bash
# 🕉️ Vedas Agent - Spiritual Content
python cli_runner.py explain "dharma in Hindi with devotional voice" vedas_agent
python cli_runner.py create "Bhagavad Gita wisdom for Instagram" vedas_agent
python cli_runner.py translate "spiritual guidance in Sanskrit" vedas_agent

# 🎓 EduMentor Agent - Educational Content
python cli_runner.py explain "machine learning for Twitter" edumentor_agent
python cli_runner.py create "AI basics in Hindi for students" edumentor_agent
python cli_runner.py analyze "safe educational content" edumentor_agent

# 🌿 Wellness Agent - Wellness Content
python cli_runner.py create "guided meditation for stress" wellness_agent
python cli_runner.py explain "mindfulness tips for Instagram" wellness_agent
python cli_runner.py generate "uplifting wellness voice content" wellness_agent

# 📚 Knowledge Agent - Knowledge Retrieval
python cli_runner.py query "quantum computing explained" knowledge_agent
python cli_runner.py analyze "compare AI approaches" knowledge_agent
python cli_runner.py search "latest research in machine learning" knowledge_agent

# 🖼️ Image Agent - Visual Content
python cli_runner.py analyze "describe this image" image_agent --file image.jpg
python cli_runner.py process "educational diagram analysis" image_agent

# 🎵 Audio Agent - Audio Processing
python cli_runner.py transcribe "convert speech to text" audio_agent --file audio.wav
python cli_runner.py process "audio content analysis" audio_agent
```

#### 📊 **Advanced CLI Options**

```bash
# Multi-format output
python cli_runner.py explain "AI concepts" edumentor_agent --output results.json --output-format json
python cli_runner.py create "content" vedas_agent --output results.csv --output-format csv

# Batch processing with Vaani features
python cli_runner.py process "folder" knowledge_agent --batch ./documents --multilingual --voice

# RL-powered agent selection
python cli_runner.py auto "explain quantum physics in simple terms" --use-rl --rl-stats

# Platform-specific content generation
python cli_runner.py create "educational content for LinkedIn" edumentor_agent --platform linkedin
python cli_runner.py generate "spiritual post for Instagram" vedas_agent --platform instagram
```

### MCP Bridge API (port 8002)
```bash
# JSON task
curl -X POST http://localhost:8002/handle_task \
  -H "Content-Type: application/json" \
  -d '{"agent":"edumentor_agent","input":"Explain machine learning","input_type":"text"}'

# Multi-task
curl -X POST http://localhost:8002/handle_multi_task \
  -H "Content-Type: application/json" \
  -d '{"files":[{"path":"test.pdf","type":"pdf","data":"Analyze"}],"agent":"edumentor_agent","task_type":"summarize"}'
```

### Simple API Endpoints (port 8001)

#### 🤖 **Agent-Specific Endpoints**

```bash
# 🕉️ Vedas Agent - Spiritual Guidance
curl -X POST http://localhost:8001/ask-vedas \
  -H "Content-Type: application/json" \
  -d '{"query":"what is dharma", "language":"hi", "voice_enabled":true}'

# 🎓 EduMentor Agent - Educational Content
curl -X POST http://localhost:8001/edumentor \
  -H "Content-Type: application/json" \
  -d '{"query":"explain AI", "platform":"twitter", "language":"hi"}'

# 🌿 Wellness Agent - Wellness Guidance
curl -X POST http://localhost:8001/wellness \
  -H "Content-Type: application/json" \
  -d '{"query":"stress relief", "voice_enabled":true, "tone":"calm"}'

# 📚 Knowledge Agent - Knowledge Retrieval
curl -X POST http://localhost:8001/query-kb \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning", "max_results":5}'
```

#### 🎯 **Vaani Integration Endpoints**

```bash
# 🌐 Multilingual Content Generation
curl -X POST http://localhost:8001/vaani/multilingual \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world", "target_languages":["hi","sa","mr"]}'

# 📱 Platform Content Generation
curl -X POST http://localhost:8001/vaani/platform \
  -H "Content-Type: application/json" \
  -d '{"content":"AI explanation", "platform":"instagram", "tone":"educational"}'

# 🎵 Voice Content Generation
curl -X POST http://localhost:8001/vaani/voice \
  -H "Content-Type: application/json" \
  -d '{"text":"Meditation guide", "language":"hi", "tone":"devotional"}'

# 🔒 Content Security Analysis
curl -X POST http://localhost:8001/vaani/security \
  -H "Content-Type: application/json" \
  -d '{"content":"Educational material for analysis"}'
```

#### 📊 **System Endpoints**

```bash
# Health Check with Component Status
curl http://localhost:8001/health

# System Statistics
curl -X GET http://localhost:8001/stats \
  -H "X-API-Key: uniguru-dev-key-2025"

# Agent Status
curl http://localhost:8001/agents/status

# Vaani Integration Status
curl http://localhost:8001/vaani/status
```

### 🤖 **Agent Orchestrator API (Port 8080)**

The Agent Orchestrator provides intelligent agent routing and coordination with automatic intent classification.

```bash
# 🎯 Intelligent Query Processing with Auto Agent Selection
curl -X POST "http://localhost:8080/ask" \
  -H "X-API-Key: uniguru-dev-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize the key concepts of machine learning",
    "user_id": "user123",
    "session_id": "session456",
    "input_type": "text"
  }'

# 🚨 System Alerts and Flagged Activities
curl -X GET "http://localhost:8080/alerts?limit=5&flagged_only=true" \
  -H "X-API-Key: uniguru-dev-key-2025"

# 📋 User Consent Management
# Get consent status
curl -X GET "http://localhost:8080/consent?user_id=user123" \
  -H "X-API-Key: uniguru-dev-key-2025"

# Update consent
curl -X POST "http://localhost:8080/consent" \
  -H "X-API-Key: uniguru-dev-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "consent_type": "privacy_policy",
    "granted": true,
    "consent_details": "User agreed to privacy policy v1.0"
  }'

# 🔍 Agent Health and Status
curl -X GET "http://localhost:8080/agents/status" \
  -H "X-API-Key: uniguru-dev-key-2025"
```

### Web Interface (port 8003)
- Login with Basic Auth (`admin/secret` or `user/secret`)
- Upload files at `/` → processed via MCP Bridge
- Dashboard at `/dashboard` → recent tasks, NLO stats
- Download NLOs: `/download_nlo/{task_id}?format=json`

### Demo Pipeline
```bash
python blackhole_demo.py  # edit defaults within to point to your input
```

## Configuration
- Agent endpoints and options: `config/settings.py` and `agent_configs.json`
- RL configuration: `config/settings.py` (`RL_CONFIG`)
- Timeouts: `config/settings.py` (`TIMEOUT_CONFIG`)
- RAG API configuration: `config/settings.py` (`RAG_CONFIG`)
- Knowledge base utilities: `utils/rag_client.py`, `utils/file_based_retriever.py`
- External RAG API integration: `utils/rag_client.py`

## External RAG API Integration
The system now uses an external RAG API for comprehensive knowledge retrieval with Groq-powered answers:

### How It Works
1. **Query Processing**: User queries are sent to the external RAG API
2. **Knowledge Retrieval**: API searches across comprehensive knowledge base
3. **Groq Enhancement**: Retrieved content is processed by Groq for intelligent answers
4. **Response Generation**: System returns both retrieved chunks and enhanced answers

### API Response Format
```json
{
  "retrieved_chunks": [
    {
      "content": "Retrieved knowledge content...",
      "file": "source_document.pdf",
      "score": 0.85,
      "index": 1
    }
  ],
  "groq_answer": "Comprehensive answer generated by Groq AI..."
}
```

### Fallback Strategy
1. **Primary**: External RAG API with Groq answers
2. **Fallback 1**: File-based retriever (local documents)
3. **Fallback 2**: Generic responses when all else fails

### Understanding Startup Messages
When you see:
```
✅ RAG API client initialized successfully
📊 RAG API URL: https://819d053306f2.ngrok-free.app/rag
```
This indicates:
- The RAG API client is properly configured
- Connection to external RAG service is established
- System is ready for enhanced knowledge retrieval

## Vaani Sentinel X Integration
The system now integrates with **Vaani Sentinel X** - a comprehensive AI content generation platform with multilingual support, platform adaptation, voice synthesis, and security analysis.

### Vaani Features Available to Agents

#### 🎯 **Multilingual Content Generation**
- Generate content in **10+ Indian languages** (Hindi, Sanskrit, Marathi, Gujarati, Tamil, Telugu, Kannada, Malayalam, Bengali)
- Automatic language detection and translation
- Cultural context preservation

#### 📱 **Platform-Specific Content**
- **Twitter**: Optimized for 280-character limit with hashtags
- **Instagram**: Engaging captions with emojis and calls-to-action
- **LinkedIn**: Professional content with industry insights
- **Spotify**: Audio content integration

#### 🎵 **Voice Content Generation**
- Generate audio content with different tones:
  - **Devotional**: For spiritual and wellness content
  - **Educational**: Clear and informative delivery
  - **Uplifting**: Motivational and positive content
- Multiple voice options (male/female, regional accents)

#### 🔒 **Content Security Analysis**
- Automatic profanity and sensitive content detection
- Risk assessment for different platforms
- Content safety recommendations
- Compliance checking for various regions

#### 📊 **Analytics & Insights**
- Engagement metrics prediction
- Performance insights for different content types
- Platform-specific optimization suggestions

### How Agents Use Vaani Tools

Agents automatically detect when Vaani features are needed based on query context:

#### 🕉️ **VedasAgent Triggers:**
- **"Explain in Hindi/Sanskrit"** → Multilingual spiritual content
- **"Voice chanting/mantra"** → Devotional voice generation
- **"Share on social media"** → Platform-adapted spiritual content

#### 🎓 **EduMentorAgent Triggers:**
- **"Create for Twitter/Instagram"** → Platform-specific educational content
- **"In Hindi/Marathi"** → Multilingual educational materials
- **"Safe for students"** → Content security analysis

#### 🌿 **WellnessAgent Triggers:**
- **"Guided meditation"** → Voice wellness content
- **"Share on Instagram"** → Uplifting wellness posts
- **"Mental health support"** → Secure, sensitive content handling

### Vaani Integration Response Format
```json
{
  "response": "Enhanced answer with spiritual wisdom...",
  "vaani_enhanced": true,
  "vaani_data": {
    "multilingual": {
      "original_content": "Spiritual guidance...",
      "translations": {
        "hi": "आध्यात्मिक मार्गदर्शन...",
        "sa": "आध्यात्मिक मार्गदर्शन..."
      }
    },
    "voice": {
      "language": "hi",
      "tone": "devotional",
      "voice_tag": "hi_in_female_devotional"
    }
  },
  "metadata": {
    "vaani_features_used": ["multilingual", "voice"]
  }
}
```

### Vaani Configuration
Add to your `.env` file:
```env
# Vaani Sentinel X Configuration
VAANI_USERNAME=admin
VAANI_PASSWORD=secret
VAANI_ENDPOINT=https://vaani-sentinel-gs6x.onrender.com
```

### Testing Vaani Integration
```bash
# Test Vaani tools
python test_vaani_integration.py

# Test with specific agent
python cli_runner.py explain "dharma in Hindi with voice" vedas_agent
```

Notes
- Start Simple API on port 8001 to match `agent_configs.json` and `MODEL_CONFIG` endpoints.
- For audio/image/PDF processing, ensure system deps like `ffmpeg`/`libsndfile` are available.

## Testing
```bash
pytest -q
# Or run focused suites
pytest tests/test_web_interface_integration.py -q
```

## 🔧 Troubleshooting Guide

### 🤖 **Agent System Issues**

#### Agent Not Responding
```bash
# Check agent status
curl http://localhost:8001/agents/status

# Test specific agent
python cli_runner.py test "hello" vedas_agent

# Check agent configuration
python -c "from agents.agent_registry import agent_registry; print(agent_registry.list_agents())"
```

#### Vaani Integration Problems
```bash
# Test Vaani connection
python test_vaani_integration.py

# Check Vaani status
curl http://localhost:8001/vaani/status

# Verify Vaani credentials in .env
cat .env | grep VAANI
```

### 🌐 **API & Service Issues**

#### Service Health Checks
```bash
# Check all services
curl http://localhost:8001/health    # Simple API
curl http://localhost:8002/health    # MCP Bridge
curl http://localhost:8003/          # Web Interface

# Check component status
curl http://localhost:8001/health | jq .components
```

#### Port Conflicts (Windows)
```powershell
# Check port usage
netstat -ano | findstr :8001
netstat -ano | findstr :8002
netstat -ano | findstr :8003

# Kill process using port (replace PID)
taskkill /PID <PID> /F
```

### 🧠 **AI & RAG Issues**

#### RAG API Problems
```bash
# Test RAG API connectivity
curl https://819d053306f2.ngrok-free.app/rag

# Run RAG integration test
python test_rag_integration.py

# Check RAG configuration
cat .env | grep RAG
```

#### LLM API Issues
```bash
# Test Groq API
python -c "from utils.groq_client import groq_client; print(groq_client.test_connection())"

# Test Gemini API
python -c "from utils.gemini_client import gemini_client; print(gemini_client.test_connection())"

# Check API keys
cat .env | grep -E "(GROQ|GEMINI)_API_KEY"
```

### 📊 **Database & Logging Issues**

#### MongoDB Connection
```bash
# Test MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); print(client.admin.command('ping'))"

# Check MongoDB logs
# Windows: Check MongoDB service status
Get-Service MongoDB

# Linux/Mac: Check MongoDB status
brew services list | grep mongodb
```

#### Logging Issues
```bash
# Check log files
ls -la logs/
tail -f logs/blackhole_$(date +%Y%m%d).log

# Test logging system
python -c "from utils.logger import get_logger; logger = get_logger('test'); logger.info('Test log')"
```

### 🎯 **Performance Issues**

#### Slow Responses
```bash
# Check system resources
# Windows
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10

# Linux/Mac
top -o %CPU

# Check API timeouts
cat config/settings.py | grep TIMEOUT
```

#### Memory Issues
```bash
# Check memory usage
# Windows
Get-Process | Sort-Object WS -Descending | Select-Object -First 10

# Linux/Mac
ps aux --sort=-%mem | head

# Clear caches
python -c "import gc; gc.collect()"
```

### 🔄 **Common Error Solutions**

#### "VaaniTTSClient not defined"
- ✅ **Fixed**: Import structure updated
- **Solution**: Restart services after code changes

#### "RAG API connection failed"
- **Check**: `.env` file has correct `RAG_API_URL`
- **Test**: `curl https://819d053306f2.ngrok-free.app/rag`
- **Fallback**: System automatically uses file-based retriever

#### "Agent selection failed"
- **Check**: RL configuration in `config/settings.py`
- **Test**: `python cli_runner.py auto "test query" --use-rl`
- **Reset**: Clear RL logs in `logs/` directory

#### "Port already in use"
- **Find**: `netstat -ano | findstr :PORT`
- **Kill**: `taskkill /PID <PID> /F`
- **Alternative**: Use different ports in configuration

### 🚀 **Quick Recovery Commands**

```bash
# Full system restart
# Stop all services (Ctrl+C in terminals)

# Restart in order
python simple_api.py --port 8001          # Terminal 1
python mcp_bridge.py                      # Terminal 2
python integration/web_interface.py       # Terminal 3

# Quick health check
curl http://localhost:8001/health && echo "✅ API OK"
curl http://localhost:8002/health && echo "✅ Bridge OK"

# Test full pipeline
python cli_runner.py explain "test query" vedas_agent
```

## 🚀 What's New in Latest Update

### 🤖 **Advanced Multi-Agent System**
- **Specialized Agents**: VedasAgent, EduMentorAgent, WellnessAgent, KnowledgeAgent, ImageAgent, AudioAgent
- **Intelligent Agent Selection**: RL-powered routing based on query context and content type
- **Agent-Specific Capabilities**: Each agent optimized for its domain with Vaani tool integration

### 🌐 **Vaani Sentinel X Integration**
- **Complete AI Content Suite**: Multilingual generation, platform adaptation, voice synthesis, security analysis
- **10+ Indian Languages**: Hindi, Sanskrit, Marathi, Gujarati, Tamil, Telugu, Kannada, Malayalam, Bengali
- **Platform Optimization**: Twitter, Instagram, LinkedIn, Spotify content adaptation
- **Voice Generation**: Multiple tones (devotional, educational, uplifting) and voice options
- **Content Security**: Automatic safety analysis and compliance checking

### 🧠 **Enhanced AI Capabilities**
- **Groq Integration**: High-performance AI responses for knowledge enhancement
- **External RAG API**: Comprehensive knowledge retrieval with intelligent answers
- **Multi-LLM Support**: Groq, Gemini, Ollama with automatic fallback
- **Context-Aware Responses**: AI understands query intent and provides relevant answers

### 🔧 **System Improvements**
- **Production-Ready Architecture**: Docker deployment, health monitoring, comprehensive logging
- **Robust Fallback System**: Multiple fallback layers for all services and APIs
- **Enhanced Error Handling**: Graceful degradation and user-friendly error messages
- **Performance Optimization**: Async processing, connection pooling, caching mechanisms

### 📊 **Analytics & Monitoring**
- **Comprehensive Logging**: MongoDB-based logging with detailed trace information
- **Real-Time Metrics**: Performance monitoring, usage statistics, agent performance
- **RL Analytics**: Learning progress tracking, agent selection statistics
- **Health Monitoring**: System health checks, component status, error tracking

### 🎯 **Developer Experience**
- **Enhanced CLI**: Rich command-line interface with agent-specific commands
- **Comprehensive API**: RESTful APIs for all agent interactions
- **Testing Framework**: Automated testing for all components and integrations
- **Documentation**: Complete API documentation and usage examples

## 📚 Documentation & Resources

### 📖 **Core Documentation**
- `docs/complete_usage_guide.md` - Comprehensive usage guide
- `docs/deployment.md` - Production deployment guide
- `docs/agent_commands.md` - Agent-specific command reference
- `docs/reinforcement.md` - RL system documentation

### 🔧 **Technical References**
- `utils/rag_client.py` - External RAG API integration
- `utils/groq_client.py` - Groq AI client implementation
- `utils/vaani_client.py` - Vaani Sentinel X integration
- `agents/agent_registry.py` - Agent management system
- `config/settings.py` - System configuration

### 🧪 **Testing & Examples**
- `test_agent_system.py` - Agent system testing
- `test_vaani_integration.py` - Vaani integration testing
- `test_rag_integration.py` - RAG API testing
- `example/` - Usage examples and templates

### 🚀 **Quick Start Resources**
- `QUICK_START.md` - Fast setup guide
- `example/quick_setup_guide.md` - Step-by-step setup
- `smoke_test.sh` - System validation script

## 🎯 System Capabilities Summary

### 🤖 **Multi-Agent Intelligence**
- **6 Specialized Agents**: Vedas, EduMentor, Wellness, Knowledge, Image, Audio
- **Intelligent Routing**: RL-powered agent selection based on context
- **Vaani Integration**: Automatic tool usage based on query requirements

### 🌐 **Vaani Sentinel X Features**
- **10+ Languages**: Complete Indian language support
- **4 Platforms**: Twitter, Instagram, LinkedIn, Spotify optimization
- **Voice Synthesis**: Multiple tones and voice options
- **Security Analysis**: Content safety and compliance
- **Analytics**: Performance insights and recommendations

### 🧠 **AI & Knowledge Systems**
- **Groq Integration**: High-performance AI responses
- **External RAG API**: Comprehensive knowledge retrieval
- **Multi-LLM Support**: Groq, Gemini, Ollama with fallbacks
- **Intelligent Answers**: Context-aware response generation

### 🛡️ **Production Features**
- **Health Monitoring**: Comprehensive system health checks
- **Error Handling**: Graceful degradation and recovery
- **Logging**: Detailed MongoDB-based logging system
- **Docker Support**: Containerized deployment ready
- **Security**: API key authentication and content safety

## 🚀 **Ready for Production**

Your **BHIV Core Ultimate AI Agent System** is now fully operational with:

✅ **Complete Vaani Sentinel X Integration**
✅ **Advanced Multi-Agent System**
✅ **Groq + External RAG API**
✅ **Production-Ready Architecture**
✅ **Comprehensive Documentation**
✅ **Robust Testing Framework**

**Start using your AI agents today! 🎉**

---

*Built with ❤️ for the future of AI-powered content creation and knowledge systems*
