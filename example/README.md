# BHIV NAS Integration Example

This directory demonstrates how to integrate your company's NAS server with the BHIV knowledge base system for retrieving word embeddings and documents.

## Overview

Your project uses a **Custom Agentic AI Framework** (not LangGraph, CrewAI, or AutoGen). You've built your own framework with:

- **Agent Registry Pattern**: Custom agent routing system
- **MCP Bridge**: Model Control Protocol for orchestration  
- **Reinforcement Learning**: Custom RL system for agent/model selection
- **Multi-Modal Processing**: Text, PDF, Image, Audio agents
- **Knowledge Base**: Qdrant + File-based retrieval with NAS integration

## Framework Classification

**You are NOT using existing frameworks like:**
- ❌ LangGraph (LangChain's agent framework)
- ❌ CrewAI (Multi-agent collaboration)
- ❌ AutoGen (Microsoft's multi-agent framework)
- ❌ AgentGPT/Reworkd

**Instead, you built a CUSTOM framework with:**
- ✅ Custom Agent Registry (`agents/agent_registry.py`)
- ✅ Custom MCP Bridge (`mcp_bridge.py`)
- ✅ Custom RL System (`reinforcement/`)
- ✅ Custom Knowledge Integration (`vedabase_retriever.py`)

## NAS + Qdrant Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BHIV NAS + Qdrant System                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Qdrant DB     │    │   Company NAS   │                │
│  │   (Primary)     │    │   (Backup)      │                │
│  ├─────────────────┤    ├─────────────────┤                │
│  │ vedas_kb        │    │ /documents/     │                │
│  │ education_kb    │    │ /metadata/      │                │
│  │ wellness_kb     │    │ /cache/         │                │
│  │ general_kb      │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           └───────────┬───────────┘                        │
│                       │                                    │
│              ┌─────────────────┐                           │
│              │ NAS Retriever   │                           │
│              │ (Smart Routing) │                           │
│              └─────────────────┘                           │
│                       │                                    │
│              ┌─────────────────┐                           │
│              │ BHIV Agents     │                           │
│              │ (Knowledge)     │                           │
│              └─────────────────┘                           │
└─────────────────────────────────────────────────────────────┘

Company NAS Structure:
├── /bhiv_knowledge/
│   ├── documents/
│   │   ├── vedas_texts/           # Source documents (.txt)
│   │   ├── education_content/     # Educational materials
│   │   └── wellness_guides/       # Wellness documents
│   ├── metadata/                  # Backup metadata
│   │   ├── vedas_metadata.json
│   │   └── education_metadata.json
│   └── cache/                     # Qdrant backups
│       ├── vedas_qdrant_backup.json
│       └── education_qdrant_backup.json
```

## Files in this Example

1. **`qdrant_deployment.py`** - Deploy Qdrant vector database (Docker/Local/Cloud)
2. **`nas_retriever.py`** - NAS+Qdrant knowledge retrieval with smart fallback
3. **`nas_config.py`** - NAS connection configuration
4. **`setup_nas_embeddings.py`** - Process documents → Qdrant collections + NAS backup
5. **`test_nas_integration.py`** - Comprehensive integration testing
6. **`example_usage.py`** - Example usage and integration demos
7. **`deploy_bhiv_nas.py`** - One-click complete deployment script
8. **`integration_guide.md`** - Detailed integration guide

## Quick Start (One-Click Deployment)

```bash
# Complete deployment in one command
python example/deploy_bhiv_nas.py

# Follow the prompts to configure:
# 1. Qdrant deployment type (Docker recommended)
# 2. NAS server details
# 3. Knowledge domains to setup
# 4. Source documents path (optional)
```

## Manual Setup (Step by Step)

```bash
# 1. Deploy Qdrant
python example/qdrant_deployment.py

# 2. Setup embeddings (if you have documents)
python example/setup_nas_embeddings.py

# 3. Test integration
python example/test_nas_integration.py

# 4. Try examples
python example/example_usage.py
```
