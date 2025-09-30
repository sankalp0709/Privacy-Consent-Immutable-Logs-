# 🚀 Quick Setup Guide: NAS + Qdrant + BHIV

## **Step-by-Step Setup Instructions**

### **Step 1: Prerequisites**

```bash
# Make sure you're in the BHIV project directory
cd c:\Users\abc1\Downloads\BHIV-Third-Installment

# Install required packages
pip install qdrant-client sentence-transformers

# Check if Docker is installed (for Qdrant)
docker --version
```

### **Step 2: One-Click Setup (Easiest)**

```bash
# Run the complete deployment script
python example/deploy_bhiv_nas.py
```

**When prompted, enter:**
- **Qdrant deployment**: `1` (Docker)
- **NAS address**: Your NAS IP (e.g., `192.168.1.100`) or name (e.g., `company-nas`)
- **NAS share**: `bhiv_knowledge`
- **Domains**: `vedas,education,wellness`
- **Data path**: Leave empty for now (we'll add documents later)
- **Continue on errors**: `y`
- **Skip tests**: `n`

### **Step 3: Manual Setup (If you prefer control)**

**3.1 Deploy Qdrant**
```bash
python example/qdrant_deployment.py
# Choose option 1 (Docker)
```

**3.2 Test NAS Integration**
```bash
python example/test_nas_integration.py
# Enter: vedas
```

### **Step 4: Test Queries**

**4.1 Test with Example Script**
```bash
python example/example_usage.py
# Choose option 2 (Interactive mode)
# Select domain: vedas
# Ask: "What is dharma?"
```

**4.2 Test with Your BHIV API**
```bash
# Start BHIV API
python simple_api.py

# In another terminal:
curl -X POST "http://localhost:8001/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is dharma?", "domain": "vedas"}'
```

**4.3 Test with CLI**
```bash
python cli_runner.py explain "What is dharma?" knowledge_agent
```

### **Step 5: Add Your Documents (Optional)**

If you have documents to process:

```bash
# Create directories
mkdir -p data\vedas_texts
mkdir -p data\education_content

# Copy your .txt files to these directories
# Then run:
python example/setup_nas_embeddings.py
```

## **🔧 Configuration Files**

After setup, you'll have these config files:
- `config/qdrant_deployment.json` - Qdrant settings
- `config/bhiv_nas_deployment.json` - Complete deployment config

## **🧪 Testing Your Setup**

### **Test 1: Check Qdrant**
```bash
# Check if Qdrant is running
curl http://localhost:6333/collections
```

### **Test 2: Check NAS Retriever**
```bash
python -c "
from example.nas_retriever import NASKnowledgeRetriever
retriever = NASKnowledgeRetriever('vedas')
print(retriever.get_stats())
"
```

### **Test 3: Query Test**
```bash
python -c "
from example.nas_retriever import NASKnowledgeRetriever
retriever = NASKnowledgeRetriever('vedas')
results = retriever.query('What is wisdom?', top_k=3)
print(f'Found {len(results)} results')
for r in results[:2]:
    print(f'- {r.get(\"filename\", \"Unknown\")}: {r.get(\"score\", 0):.3f}')
"
```

## **🔗 Integration with Your Existing System**

### **Option 1: Use NAS Retriever Directly**

Create a new file `agents/enhanced_knowledge_agent.py`:

```python
from example.nas_retriever import NASKnowledgeRetriever
from utils.logger import get_logger
import uuid
from datetime import datetime

logger = get_logger(__name__)

class EnhancedKnowledgeAgent:
    def __init__(self, domain="vedas"):
        self.nas_retriever = NASKnowledgeRetriever(domain)
        self.domain = domain
    
    def query(self, query_text: str, filters: dict = None, task_id: str = None) -> dict:
        task_id = task_id or str(uuid.uuid4())
        
        try:
            # Query NAS+Qdrant
            results = self.nas_retriever.query(query_text, top_k=5, filters=filters)
            
            if results:
                return {
                    "query_id": task_id,
                    "query": query_text,
                    "response": [r.get('content', '') for r in results],
                    "sources": [r.get('filename', 'Unknown') for r in results],
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": "enhanced_knowledge",
                    "status": 200,
                    "metadata": {
                        "retriever": "nas_qdrant",
                        "domain": self.domain,
                        "total_results": len(results)
                    }
                }
            else:
                return {
                    "query_id": task_id,
                    "query": query_text,
                    "response": ["No specific information found in knowledge base."],
                    "sources": [],
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": "enhanced_knowledge",
                    "status": 200,
                    "metadata": {"fallback": True}
                }
                
        except Exception as e:
            logger.error(f"Enhanced knowledge query failed: {e}")
            return {
                "query_id": task_id,
                "query": query_text,
                "response": ["Error retrieving information."],
                "sources": [],
                "timestamp": datetime.now().isoformat(),
                "endpoint": "enhanced_knowledge",
                "status": 500,
                "error": str(e)
            }
    
    def run(self, input_path: str, live_feed: str = "", model: str = "enhanced_knowledge", input_type: str = "text", task_id: str = None):
        """Compatible with existing agent interface."""
        return self.query(input_path, task_id=task_id)
```

### **Option 2: Update Agent Config**

Add to `config/agent_configs.json`:

```json
{
  "enhanced_knowledge_agent": {
    "name": "Enhanced Knowledge Agent",
    "description": "NAS+Qdrant powered knowledge retrieval",
    "connection_type": "python_module",
    "module_path": "agents.enhanced_knowledge_agent",
    "class_name": "EnhancedKnowledgeAgent",
    "input_types": ["text"],
    "rl_enabled": true,
    "nas_enabled": true,
    "qdrant_enabled": true
  }
}
```

## **🚨 Troubleshooting**

### **Common Issues:**

1. **Qdrant not starting**:
   ```bash
   docker ps  # Check if container is running
   docker logs bhiv-qdrant  # Check logs
   ```

2. **NAS not accessible**:
   - Check network connection
   - Verify NAS address and credentials
   - Try accessing NAS manually

3. **No results from queries**:
   - Check if collections exist: `curl http://localhost:6333/collections`
   - Verify documents were processed
   - Check logs for errors

### **Debug Commands:**

```bash
# Check Qdrant collections
curl http://localhost:6333/collections

# Check collection info
curl http://localhost:6333/collections/vedas_knowledge_base

# Test NAS retriever
python example/test_nas_integration.py

# Check logs
tail -f logs/bhiv_*.log
```

## **🎯 Next Steps**

1. **Add your documents** to the system
2. **Test queries** with your specific content
3. **Integrate** with your existing agents
4. **Monitor performance** and adjust as needed
5. **Scale up** by adding more domains/collections

## **📞 Quick Commands Reference**

```bash
# Start everything
python example/deploy_bhiv_nas.py

# Test queries
python example/example_usage.py

# Check status
python example/test_nas_integration.py

# Start BHIV API
python simple_api.py

# Test API
curl -X POST "http://localhost:8001/query" -H "Content-Type: application/json" -d '{"query": "test", "domain": "vedas"}'
```

Your NAS + Qdrant + BHIV system is now ready! 🎉
