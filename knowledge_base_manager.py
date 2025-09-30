#!/usr/bin/env python3
"""
Knowledge Base Manager for BHIV - NAS Integration
Manages knowledge base files on the company NAS server
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NASKnowledgeBaseManager:
    """Manages knowledge base files on the NAS server"""
    
    def __init__(self, nas_path: str):
        """
        Initialize the NAS Knowledge Base Manager
        
        Args:
            nas_path: Windows UNC path to the NAS share (e.g., \\192.168.0.94\Guruukul_DB)
        """
        self.nas_path = Path(nas_path)
        self.knowledge_base_path = self.nas_path / "knowledge_base"
        self.documents_path = self.knowledge_base_path / "documents"
        self.metadata_path = self.knowledge_base_path / "metadata"
        self.index_file = self.knowledge_base_path / "index.json"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories on the NAS"""
        try:
            self.knowledge_base_path.mkdir(exist_ok=True)
            self.documents_path.mkdir(exist_ok=True)
            self.metadata_path.mkdir(exist_ok=True)
            logger.info(f"Knowledge base directories ensured at: {self.knowledge_base_path}")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test connection to the NAS"""
        try:
            # Attempt to mount/connect if credentials provided (Windows UNC)
            nas_user = os.getenv("NAS_USERNAME")
            nas_pass = os.getenv("NAS_PASSWORD")
            nas_domain = os.getenv("NAS_DOMAIN", "")
            # If credentials exist and path not accessible, try mapping via 'net use'
            if nas_user and nas_pass and not self.nas_path.exists():
                try:
                    # net use \\server\share password /user:domain\user
                    share = str(self.nas_path)
                    user_spec = f"{nas_domain}\\{nas_user}" if nas_domain else nas_user
                    cmd = [
                        "net", "use", share, nas_pass, f"/user:{user_spec}", "/persistent:no"
                    ]
                    import subprocess
                    subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                except Exception as e:
                    logger.warning(f"Failed to map NAS share via 'net use': {e}")
            # Test basic access
            if not self.nas_path.exists():
                logger.error(f"NAS path does not exist: {self.nas_path}")
                return False
            
            # Test write access
            test_file = self.nas_path / "connection_test.tmp"
            test_file.write_text("Connection test")
            test_file.unlink()  # Delete test file
            
            logger.info("✅ NAS connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ NAS connection test failed: {e}")
            return False
    
    def upload_document(self, local_file_path: str, document_id: Optional[str] = None) -> str:
        """
        Upload a document to the knowledge base
        
        Args:
            local_file_path: Path to the local file to upload
            document_id: Optional custom document ID
            
        Returns:
            Document ID of the uploaded file
        """
        local_path = Path(local_file_path)
        
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_file_path}")
        
        # Generate document ID if not provided
        if not document_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            document_id = f"{local_path.stem}_{timestamp}"
        
        # Copy file to NAS
        nas_file_path = self.documents_path / f"{document_id}{local_path.suffix}"
        shutil.copy2(local_path, nas_file_path)
        
        # Create metadata
        metadata = {
            "document_id": document_id,
            "original_filename": local_path.name,
            "file_size": local_path.stat().st_size,
            "upload_date": datetime.now().isoformat(),
            "file_extension": local_path.suffix,
            "nas_path": str(nas_file_path)
        }
        
        # Save metadata
        metadata_file = self.metadata_path / f"{document_id}.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Update index
        self._update_index(document_id, metadata)
        
        logger.info(f"✅ Document uploaded: {document_id}")
        return document_id
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the knowledge base"""
        try:
            if not self.index_file.exists():
                return []
            
            index_data = json.loads(self.index_file.read_text())
            return list(index_data.get("documents", {}).values())
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    def get_document_path(self, document_id: str) -> Optional[Path]:
        """Get the NAS path for a document"""
        try:
            metadata_file = self.metadata_path / f"{document_id}.json"
            if not metadata_file.exists():
                return None
            
            metadata = json.loads(metadata_file.read_text())
            return Path(metadata["nas_path"])
            
        except Exception as e:
            logger.error(f"Failed to get document path for {document_id}: {e}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the knowledge base"""
        try:
            # Get document path
            doc_path = self.get_document_path(document_id)
            if doc_path and doc_path.exists():
                doc_path.unlink()
            
            # Delete metadata
            metadata_file = self.metadata_path / f"{document_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Update index
            self._remove_from_index(document_id)
            
            logger.info(f"✅ Document deleted: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def _update_index(self, document_id: str, metadata: Dict):
        """Update the main index file"""
        try:
            # Load existing index
            if self.index_file.exists():
                index_data = json.loads(self.index_file.read_text())
            else:
                index_data = {"documents": {}, "last_updated": None}
            
            # Update index
            index_data["documents"][document_id] = metadata
            index_data["last_updated"] = datetime.now().isoformat()
            
            # Save index
            self.index_file.write_text(json.dumps(index_data, indent=2))
            
        except Exception as e:
            logger.error(f"Failed to update index: {e}")
    
    def _remove_from_index(self, document_id: str):
        """Remove a document from the index"""
        try:
            if not self.index_file.exists():
                return
            
            index_data = json.loads(self.index_file.read_text())
            if document_id in index_data.get("documents", {}):
                del index_data["documents"][document_id]
                index_data["last_updated"] = datetime.now().isoformat()
                self.index_file.write_text(json.dumps(index_data, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to remove from index: {e}")
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        try:
            documents = self.list_documents()
            total_size = sum(doc.get("file_size", 0) for doc in documents)
            
            return {
                "total_documents": len(documents),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "nas_path": str(self.nas_path),
                "knowledge_base_path": str(self.knowledge_base_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

def main():
    """Test the NAS Knowledge Base Manager"""
    
    # Load configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    nas_path = os.getenv("NAS_PATH", r"\\192.168.0.94\Guruukul_DB")
    
    # Initialize manager
    kb_manager = NASKnowledgeBaseManager(nas_path)
    
    # Test connection
    if not kb_manager.test_connection():
        print("❌ Failed to connect to NAS")
        return
    
    # Show stats
    stats = kb_manager.get_stats()
    print("\n📊 Knowledge Base Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # List existing documents
    documents = kb_manager.list_documents()
    print(f"\n📚 Existing Documents ({len(documents)}):")
    for doc in documents:
        print(f"  - {doc['document_id']}: {doc['original_filename']}")

if __name__ == "__main__":
    main()
