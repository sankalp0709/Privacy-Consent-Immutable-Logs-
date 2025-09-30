#!/usr/bin/env python3
"""
NAS Configuration for BHIV Knowledge Base
Configure your company's NAS server settings here
"""

import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional

class NASConfig:
    """Configuration for company NAS server integration."""
    
    def __init__(self):
        self.system = platform.system()
        self.current_config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load NAS configuration based on operating system."""
        
        # Company NAS configuration - Guruukul_DB share
        base_config = {
            "nas_name": "192.168.0.94",
            "share_name": "Guruukul_DB",
            "username": os.getenv("NAS_USERNAME", ""),
            "password": os.getenv("NAS_PASSWORD", ""),
            "domain": os.getenv("NAS_DOMAIN", "WORKGROUP"),
            "timeout": 30,
            "retry_attempts": 3,
            "port": 445,
            "protocol_version": "SMB3"
        }
        
        if self.system == "Windows":
            return {
                **base_config,
                "unc_path": f"\\\\{base_config['nas_name']}\\{base_config['share_name']}",
                "mapped_drive": "G:",  # Changed to G: to avoid conflicts
                "mount_command": f"net use G: \\\\{base_config['nas_name']}\\{base_config['share_name']} /persistent:yes",
                "embeddings_path": "G:\\qdrant_embeddings",
                "documents_path": "G:\\source_documents",
                "metadata_path": "G:\\metadata",
                "qdrant_data_path": "G:\\qdrant_data"
            }
        
        elif self.system == "Linux":
            return {
                **base_config,
                "mount_point": f"/mnt/company-nas/{base_config['share_name']}",
                "mount_command": f"sudo mount -t cifs //{base_config['nas_name']}/{base_config['share_name']} /mnt/company-nas/{base_config['share_name']}",
                "embeddings_path": f"/mnt/company-nas/{base_config['share_name']}/embeddings",
                "documents_path": f"/mnt/company-nas/{base_config['share_name']}/documents",
                "metadata_path": f"/mnt/company-nas/{base_config['share_name']}/metadata"
            }
        
        else:
            raise OSError(f"Unsupported operating system: {self.system}")
    
    def get_embeddings_path(self, domain: str = "vedas") -> str:
        """Get path to embeddings for specific domain."""
        base_path = self.current_config["embeddings_path"]
        return os.path.join(base_path, f"{domain}_embeddings.faiss")
    
    def get_documents_path(self, domain: str = "vedas") -> str:
        """Get path to documents for specific domain."""
        base_path = self.current_config["documents_path"]
        return os.path.join(base_path, f"{domain}_texts")
    
    def get_metadata_path(self, domain: str = "vedas") -> str:
        """Get path to metadata for specific domain."""
        base_path = self.current_config["metadata_path"]
        return os.path.join(base_path, f"{domain}_metadata.json")
    
    def is_nas_accessible(self) -> bool:
        """Check if NAS is accessible."""
        try:
            if self.system == "Windows":
                test_path = self.current_config["unc_path"]
            else:
                test_path = self.current_config["mount_point"]
            
            return os.path.exists(test_path)
        except Exception:
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.current_config.copy()

# Example usage and configuration
if __name__ == "__main__":
    config = NASConfig()
    print("🔧 NAS Configuration:")
    print(f"  System: {config.system}")
    print(f"  NAS accessible: {config.is_nas_accessible()}")
    print(f"  Embeddings path: {config.get_embeddings_path('vedas')}")
    print(f"  Documents path: {config.get_documents_path('vedas')}")
    print(f"  Metadata path: {config.get_metadata_path('vedas')}")
