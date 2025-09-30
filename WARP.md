# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

BHIV Core Third Installment is an advanced multi-modal AI pipeline with reinforcement learning, knowledge-base retrieval (multi-folder vector search + NAS + FAISS + file retriever), a production-ready FastAPI layer, web interface, and an enhanced CLI.

## Common Development Commands

### Environment Setup
```powershell
# Create and activate virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install NLP model for enhanced processing
python -m spacy download en_core_web_sm
```

### Service Management
```powershell
# Start services in separate terminals (recommended ports):

# Terminal 1: Simple API (agents, KB endpoints) - Port 8001
python simple_api.py --port 8001

# Terminal 2: MCP Bridge (task router, RL, registry) - Port 8002
python mcp_bridge.py

# Terminal 3: Web Interface - Port 8003
python integration/web_interface.py
```

### Development Commands
```powershell
# CLI testing - single file processing
python cli_runner.py summarize "Analyze this file" edumentor_agent --file sample_documents/ayurveda_basics.txt

# CLI testing - batch processing with CSV output
python cli_runner.py summarize "Process folder" edumentor_agent --batch ./sample_documents --output results.csv --output-format csv

# RL-enabled processing with statistics
python cli_runner.py summarize "Learning test" edumentor_agent --use-rl --rl-stats --exploration-rate 0.3

# Test multi-folder vector search functionality
python test_multi_folder_search.py

# Demo of multi-folder system
python demo_multi_folder.py

# Blackhole demo pipeline
python blackhole_demo.py
```

### Testing
```powershell
# Run all tests
pytest -q

# Run specific test suites
pytest tests/test_web_interface_integration.py -q
```

### Health Checks and Debugging
```powershell
# Check service health
curl http://localhost:8002/health  # MCP Bridge
curl http://localhost:8001/health  # Simple API

# Check port usage (Windows)
netstat -ano | findstr :8001
netstat -ano | findstr :8002
netstat -ano | findstr :8003
```

## High-Level Architecture

The system follows a three-tier architecture with specialized components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   CLI Runner    │    │  Simple API     │
│   (Port 8003)   │    │  (Enhanced)     │    │  (Port 8001)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └──────────────┬────────┴──────────────┬────────┘
                        │                       │
                   ┌───────────────┐       ┌───────────────┐
                   │  MCP Bridge   │       │  Knowledge KB │
                   │  (Port 8002)  │       │  (Multi-Folder)│
                   └───────────────┘       └───────────────┘
                              │
                 ┌────────────┴────────────┐
                 │  Agent Registry + RL    │
                 │  (text/pdf/image/audio) │
                 └──────────────────────────┘
```

### Core Service Layers

1. **Presentation Layer** (Port 8003)
   - Web interface with Bootstrap UI
   - Basic authentication (admin/secret, user/secret)
   - File upload and real-time processing
   - Dashboard with analytics and task monitoring

2. **API Gateway Layer** (Port 8001)
   - Simple API with specialized endpoints
   - Model providers (Ollama integration)
   - Knowledge base endpoints (Vedas, EduMentor, Wellness)
   - Health monitoring and metrics

3. **Processing Layer** (Port 8002)
   - MCP Bridge - central task router
   - Agent registry with RL-based selection
   - Multi-modal processing orchestration
   - Reinforcement learning context logging

### Agent System Architecture

The agent system is built around a registry pattern with dynamic routing:

- **Base Agent**: Memory scaffold with key-value storage
- **Specialized Agents**: 
  - `TextAgent`: Text processing and summarization
  - `ArchiveAgent`: PDF processing and document analysis
  - `ImageAgent`: Computer vision and image analysis
  - `AudioAgent`: Speech recognition and audio processing
  - `KnowledgeAgent`: Semantic search and knowledge retrieval
  - `StreamTransformerAgent`: General-purpose streaming processor

### Reinforcement Learning Layer

The RL system operates as a non-intrusive observational layer:

- **Agent Selector**: UCB-based algorithm for optimal agent routing
- **Model Selector**: Dynamic model selection with fallback chains
- **Reward Functions**: Quality metrics based on output, timing, and success rates
- **Replay Buffer**: Decision history for learning and analytics
- **RL Context**: Comprehensive logging of all decisions and outcomes

### Knowledge Base Architecture

Multi-tier knowledge retrieval with intelligent fallbacks:

1. **Multi-folder Vector Search** (Primary)
   - Searches across multiple Qdrant instances simultaneously
   - Folder priority weights (new_data: 1.0, fourth_data: 0.9, data: 0.8, legacy_data: 0.7)
   - Combined and ranked results from entire knowledge base

2. **NAS+Qdrant Retriever** (Secondary)
   - Network-attached storage integration
   - Qdrant vector database for semantic search
   - Document chunking and embedding storage

3. **FAISS Vector Stores** (Tertiary)
   - Local FAISS indices for offline search
   - Sentence transformer embeddings (all-MiniLM-L6-v2)

4. **File-based Retriever** (Final fallback)
   - Direct file system search
   - Pattern matching and keyword extraction

## Key Components and Patterns

### Agent Registry Pattern
The `agent_registry.py` implements dynamic agent discovery and routing:
- Agents are configured via JSON with connection types (python_module, http_api)
- RL-based selection when enabled, with deterministic fallback
- Tag-based routing for semantic matching
- Health checking and availability monitoring

### Multi-Modal Processing Pipeline
Each input type follows a standardized processing pattern:
1. Input type detection (text, pdf, image, audio)
2. Agent selection via registry (with RL optimization)
3. Specialized processing via dedicated agents
4. Response formatting and metadata enrichment
5. Logging and RL feedback collection

### Fallback Chain Architecture
Robust error handling with intelligent fallbacks:
```
Primary Model → Fallback Models → Default Agent → Error Response
     ↓                ↓               ↓              ↓
RL Learning    RL Learning    RL Learning    Error Logging
```

### Multi-Folder Vector Search System
Comprehensive knowledge retrieval across multiple Qdrant instances:
- Environment-driven configuration (`QDRANT_URLS`, `QDRANT_INSTANCE_NAMES`)
- Automatic collection discovery and health monitoring
- Weighted result combination with folder priorities
- Graceful degradation to alternative retrieval methods

## Environment Configuration

### Required Environment Variables
```bash
# Core API Configuration
MONGO_URI=mongodb://localhost:27017
USE_RL=true
RL_EXPLORATION_RATE=0.2

# Model API Keys (Optional - depends on agents used)
GROQ_API_KEY=your_key_if_used
GEMINI_API_KEY=your_key_if_used

# Single Qdrant instance (fallback)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=vedas_knowledge_base
QDRANT_VECTOR_SIZE=384

# Multi-Folder Vector Configuration (primary)
QDRANT_URLS=http://localhost:6333  # Comma-separated URLs
QDRANT_INSTANCE_NAMES=qdrant_data,qdrant_fourth_data,qdrant_legacy_data,qdrant_new_data

# NAS Configuration (optional)
NAS_PATH=\\\\192.168.0.94\\Guruukul_DB

# Timeout Configuration
DEFAULT_TIMEOUT=120
IMAGE_PROCESSING_TIMEOUT=180
AUDIO_PROCESSING_TIMEOUT=240
PDF_PROCESSING_TIMEOUT=150
FILE_UPLOAD_TIMEOUT=300
```

### Agent Configuration
Agent endpoints are configured in `agent_configs.json` and `config/settings.py`:
- Each agent specifies connection type, endpoint, headers, and capabilities
- Health check endpoints for availability monitoring
- Keyword and pattern matching for automatic routing
- Input/output type specifications

## Development Patterns

### Adding New Agents
1. Create agent class inheriting from `BaseAgent`
2. Implement required methods (process, run)
3. Add configuration to `agent_configs.json`
4. Update agent registry routing logic if needed
5. Add health check endpoint
6. Update tests and documentation

### RL Integration
All components can leverage RL through:
- `rl_context.log_action()` for decision logging
- `agent_selector.select_agent()` for RL-based routing
- `model_selector.select_model()` for optimal model choice
- Reward feedback via `replay_buffer.add_run()`

### Error Handling Patterns
- Graceful degradation with fallback chains
- Comprehensive error logging to MongoDB
- RL learning from failures
- User-friendly error messages with task IDs

### Testing Strategies
- Unit tests for individual components
- Integration tests for service interactions
- End-to-end tests for complete workflows
- RL system validation with synthetic data

## Common Issues and Solutions

### Multi-folder Vector Search
If you see "0 vector stores" during startup, this is normal - it refers to FAISS indices, not Qdrant collections. The system will use multi-folder vector search as the primary method.

### Port Conflicts
Services must run on specific ports to match configuration:
- Simple API: 8001 (matches `agent_configs.json`)
- MCP Bridge: 8002 (central routing)
- Web Interface: 8003 (user interface)

### RL System
- Start with higher exploration rates (0.2-0.3) for new deployments
- Monitor performance via learning dashboard
- Verify reward signals are meaningful for your use case
- Check fallback chains work correctly under load

### Knowledge Base Integration
- Ensure both `QDRANT_URLS` and `QDRANT_INSTANCE_NAMES` are configured
- Test multi-folder functionality with `test_multi_folder_search.py`
- Verify NAS connectivity if using network storage
- Check Qdrant instance health and collection availability

## File Structure Context

Key directories and their purposes:
- `agents/`: All agent implementations and registry
- `config/`: Environment settings and agent configurations
- `integration/`: Web interface and external system adapters
- `reinforcement/`: RL components (selectors, context, rewards)
- `utils/`: Shared utilities (logging, file handling, MongoDB)
- `docs/`: Comprehensive documentation and guides
- `example/`: Setup examples and integration guides
- `tests/`: Test suites and validation scripts

The codebase follows a modular architecture where each component can be developed and tested independently while maintaining clear interfaces for integration.