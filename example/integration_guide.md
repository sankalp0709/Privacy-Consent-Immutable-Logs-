# BHIV NAS Integration Guide

## Framework Analysis: You're Using a CUSTOM Agentic AI Framework

After analyzing your codebase, you are **NOT** using any existing agentic AI frameworks like:

- ❌ **LangGraph** (LangChain's agent framework)
- ❌ **CrewAI** (Multi-agent collaboration framework)  
- ❌ **AutoGen** (Microsoft's multi-agent conversation framework)
- ❌ **AgentGPT/Reworkd** (Web-based agent platforms)

### Instead, you built a **CUSTOM Agentic AI Framework** with:

✅ **Custom Agent Registry** (`agents/agent_registry.py`)
✅ **Custom MCP Bridge** (`mcp_bridge.py`) - Model Control Protocol
✅ **Custom Reinforcement Learning** (`reinforcement/` directory)
✅ **Custom Multi-Modal Processing** (Text, PDF, Image, Audio agents)
✅ **Custom Knowledge Integration** (`vedabase_retriever.py`, Qdrant)

## Your Custom Framework Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BHIV Custom Framework                    │
├─────────────────────────────────────────────────────────────┤
│  🎯 Agent Registry (Dynamic Routing)                       │
│  🌉 MCP Bridge (Orchestration Layer)                       │
│  🧠 RL System (Adaptive Selection)                         │
│  📚 Knowledge Base (Qdrant + NAS)                          │
│  🔄 Multi-Modal Processing                                 │
└─────────────────────────────────────────────────────────────┘
```

## NAS + Qdrant Integration Steps

### Step 1: Deploy Qdrant Vector Database

**Deploy Qdrant for production use:**

```bash
# Deploy Qdrant using Docker (recommended)
python example/qdrant_deployment.py

# Choose option 1 (Docker) when prompted
# This will:
# - Start Qdrant container
# - Create collections for your domains
# - Generate configuration files
```

**Alternative deployment options:**
- **Docker**: `docker run -p 6333:6333 qdrant/qdrant:latest`
- **Cloud**: Use Qdrant Cloud service
- **Local**: Install Qdrant server locally

### Step 2: Configure NAS Connection

1. **Update NAS Configuration**:
   ```python
   # In example/nas_config.py
   nas_config = {
       "nas_name": "your-company-nas.local",  # Your actual NAS address
       "share_name": "bhiv_knowledge",        # Your share name
       "username": "your_username",           # NAS username
       "password": "your_password"            # NAS password
   }
   ```

2. **Set Environment Variables**:
   ```bash
   # Add to your .env file
   NAS_USERNAME=your_nas_username
   NAS_PASSWORD=your_nas_password
   NAS_DOMAIN=your-company-nas.local
   NAS_SHARE=bhiv_knowledge
   ```

### Step 3: Setup NAS Directory Structure

Your team member should organize data on NAS like this:

```
\\your-company-nas\bhiv_knowledge\
├── documents/
│   ├── vedas_texts/                    # Original Vedic documents (.txt files)
│   ├── education_content/              # Educational materials (.txt files)
│   ├── wellness_guides/                # Wellness documents (.txt files)
│   └── general_knowledge/              # General documents (.txt files)
├── metadata/                           # Backup metadata (Qdrant is primary)
│   ├── vedas_metadata.json             # Document metadata backup
│   ├── education_metadata.json         # Educational metadata backup
│   ├── wellness_metadata.json          # Wellness metadata backup
│   └── general_metadata.json           # General metadata backup
└── cache/                              # Local cache backups
    ├── vedas_qdrant_backup.json        # Qdrant collection backup
    ├── education_qdrant_backup.json    # Educational collection backup
    └── wellness_qdrant_backup.json     # Wellness collection backup
```

**Note**: Embeddings are now stored in **Qdrant collections**, not FAISS files. NAS is used for:
- Original documents (source files)
- Metadata backups
- Cache/backup of Qdrant collections

### Step 4: Process Documents and Create Embeddings

**Setup embeddings from your documents:**

```bash
# Process local documents and upload to Qdrant + NAS
python example/setup_nas_embeddings.py

# When prompted:
# 1. Enter path to your local documents (e.g., ./data/vedic_texts/)
# 2. Choose domain (vedas, education, wellness, etc.)
# 3. Script will:
#    - Create embeddings using sentence-transformers
#    - Upload to Qdrant collection
#    - Backup documents to NAS
#    - Create metadata files
```

### Step 5: Integrate with Existing Agents

1. **Update KnowledgeAgent.py**:
   ```python
   # Add NAS+Qdrant support to your existing KnowledgeAgent
   from example.nas_retriever import NASKnowledgeRetriever

   class KnowledgeAgent:
       def __init__(self):
           # Existing code...
           self.nas_retriever = NASKnowledgeRetriever("vedas", qdrant_url="localhost:6333")

       def query(self, query_text: str, filters: dict = None, task_id: str = None):
           # Try NAS+Qdrant first for better performance
           try:
               nas_results = self.nas_retriever.query(query_text, top_k=5, filters=filters)
               if nas_results:
                   return self._format_nas_results(nas_results, task_id)
           except Exception as e:
               logger.warning(f"NAS+Qdrant retrieval failed, using fallback: {e}")

           # Fallback to existing retrieval methods
           return self._existing_retrieval_method(query_text, filters, task_id)
   ```

2. **Update Agent Configs**:
   ```json
   // In config/agent_configs.json
   {
     "vedas_agent": {
       "name": "Vedas Agent",
       "nas_enabled": true,
       "nas_domain": "vedas",
       "qdrant_enabled": true,
       "qdrant_url": "localhost:6333",
       "fallback_enabled": true,
       "connection_type": "python_module",
       "module_path": "agents.KnowledgeAgent",
       "class_name": "KnowledgeAgent"
     }
   }
   ```

### Step 4: Update MCP Bridge

```python
# In mcp_bridge.py, add NAS support
from example.nas_retriever import NASKnowledgeRetriever

async def handle_task_request(payload: TaskPayload) -> dict:
    agent_config = agent_registry.get_agent_config(payload.agent)
    
    # Check if agent supports NAS
    if agent_config.get('nas_enabled'):
        nas_domain = agent_config.get('nas_domain', 'general')
        try:
            nas_retriever = NASKnowledgeRetriever(nas_domain)
            # Use NAS retriever for knowledge queries
            if payload.input_type == "knowledge_query":
                nas_results = nas_retriever.query(payload.input, top_k=5)
                if nas_results:
                    return format_nas_response(nas_results, payload)
        except Exception as e:
            logger.warning(f"NAS retrieval failed: {e}")
    
    # Continue with existing agent processing...
```

### Step 5: Test Integration

1. **Run NAS Tests**:
   ```bash
   cd example/
   python test_nas_integration.py
   ```

2. **Test with CLI**:
   ```bash
   python cli_runner.py explain "What is dharma?" knowledge_agent
   ```

3. **Test with API**:
   ```bash
   curl -X POST "http://localhost:8001/query" \
        -H "Content-Type: application/json" \
        -d '{"query": "What is dharma?", "domain": "vedas"}'
   ```

## Performance Optimization

### Caching Strategy
```python
# Implement local caching for NAS embeddings
class CachedNASRetriever(NASKnowledgeRetriever):
    def __init__(self, domain: str):
        super().__init__(domain)
        self.cache_dir = Path("cache/nas_cache")
        self.cache_ttl = 3600  # 1 hour
        
    def query(self, query_text: str, top_k: int = 5):
        # Check local cache first
        cached_result = self._check_cache(query_text)
        if cached_result:
            return cached_result
            
        # Query NAS
        result = super().query(query_text, top_k)
        
        # Cache result
        self._cache_result(query_text, result)
        return result
```

### Load Balancing
```python
# Distribute queries across multiple NAS endpoints
class LoadBalancedNASRetriever:
    def __init__(self, domains: list):
        self.retrievers = {
            domain: NASKnowledgeRetriever(domain) 
            for domain in domains
        }
        self.current_retriever = 0
    
    def query(self, query_text: str, domain: str = None):
        if domain:
            return self.retrievers[domain].query(query_text)
        
        # Round-robin load balancing
        retriever = list(self.retrievers.values())[self.current_retriever]
        self.current_retriever = (self.current_retriever + 1) % len(self.retrievers)
        return retriever.query(query_text)
```

## Monitoring and Logging

```python
# Add NAS-specific logging to your existing logger
class NASLogger:
    def log_nas_query(self, query: str, domain: str, results_count: int, response_time: float):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "domain": domain,
            "results_count": results_count,
            "response_time": response_time,
            "source": "nas_retrieval"
        }
        
        # Add to your existing MongoDB logging
        mongo_logger.log_task(log_entry)
```

## Troubleshooting

### Common Issues:

1. **NAS Not Accessible**:
   - Check network connectivity
   - Verify credentials
   - Ensure share is mounted

2. **Embeddings Not Loading**:
   - Check file permissions
   - Verify FAISS index format
   - Check available disk space

3. **Slow Performance**:
   - Implement local caching
   - Use SSD storage on NAS
   - Optimize network bandwidth

### Debug Commands:
```bash
# Test NAS connectivity
python example/nas_config.py

# Test embeddings loading
python example/test_nas_integration.py

# Monitor performance
python example/example_usage.py
```

## Next Steps

1. **Setup NAS Server**: Configure your company NAS with the directory structure
2. **Generate Embeddings**: Have your team member create embeddings using `setup_nas_embeddings.py`
3. **Test Integration**: Run the test suite to verify everything works
4. **Deploy**: Integrate with your existing BHIV agents
5. **Monitor**: Set up logging and monitoring for NAS queries

Your custom framework is quite sophisticated and well-designed! The NAS integration will add powerful knowledge retrieval capabilities to your existing system.
