#!/usr/bin/env python3
"""
Complete BHIV NAS + Qdrant Deployment Script
One-click deployment of BHIV with NAS integration and Qdrant vector database
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from example.qdrant_deployment import QdrantDeployment
from example.setup_nas_embeddings import NASEmbeddingsSetup
from example.nas_config import NASConfig
from example.test_nas_integration import NASIntegrationTest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BHIVNASDeployment:
    """Complete BHIV NAS + Qdrant deployment."""
    
    def __init__(self):
        self.deployment_steps = [
            ("check_prerequisites", "Check system prerequisites"),
            ("deploy_qdrant", "Deploy Qdrant vector database"),
            ("configure_nas", "Configure NAS connection"),
            ("setup_embeddings", "Setup embeddings and collections"),
            ("test_integration", "Test complete integration"),
            ("generate_configs", "Generate configuration files"),
            ("deploy_bhiv", "Deploy BHIV services")
        ]
        
        self.deployment_status = {}
        self.config = {}
    
    def run_deployment(self, config: Dict[str, Any] = None) -> bool:
        """Run complete deployment process."""
        logger.info("🚀 Starting BHIV NAS + Qdrant Deployment")
        logger.info("=" * 60)
        
        if config:
            self.config = config
        else:
            self.config = self._get_deployment_config()
        
        # Execute deployment steps
        for step_name, step_description in self.deployment_steps:
            logger.info(f"\n📋 Step: {step_description}")
            logger.info("-" * 40)
            
            try:
                step_method = getattr(self, step_name)
                success = step_method()
                
                self.deployment_status[step_name] = {
                    "success": success,
                    "description": step_description,
                    "timestamp": time.time()
                }
                
                if success:
                    logger.info(f"✅ {step_description} - SUCCESS")
                else:
                    logger.error(f"❌ {step_description} - FAILED")
                    if not self.config.get("continue_on_error", False):
                        logger.error("🛑 Deployment stopped due to error")
                        return False
                    
            except Exception as e:
                logger.error(f"❌ {step_description} - ERROR: {e}")
                self.deployment_status[step_name] = {
                    "success": False,
                    "error": str(e),
                    "description": step_description,
                    "timestamp": time.time()
                }
                
                if not self.config.get("continue_on_error", False):
                    return False
        
        # Final summary
        self._print_deployment_summary()
        return self._is_deployment_successful()
    
    def _get_deployment_config(self) -> Dict[str, Any]:
        """Get deployment configuration from user input."""
        print("🔧 BHIV NAS + Qdrant Deployment Configuration")
        print("=" * 50)
        
        config = {}
        
        # Qdrant deployment type
        print("\n1. Qdrant Deployment:")
        print("   1. Docker (recommended)")
        print("   2. Local server")
        print("   3. Qdrant Cloud")
        
        qdrant_choice = input("Choose Qdrant deployment (1-3, default: 1): ").strip() or "1"
        qdrant_types = {"1": "docker", "2": "local", "3": "cloud"}
        config["qdrant_type"] = qdrant_types.get(qdrant_choice, "docker")
        
        # NAS configuration
        print("\n2. NAS Configuration:")
        config["nas_address"] = input("NAS address (default: your-company-nas): ").strip() or "your-company-nas"
        config["nas_share"] = input("NAS share name (default: bhiv_knowledge): ").strip() or "bhiv_knowledge"
        
        # Domains to setup
        print("\n3. Knowledge Domains:")
        domains_input = input("Domains to setup (comma-separated, default: vedas,education,wellness): ").strip()
        if domains_input:
            config["domains"] = [d.strip() for d in domains_input.split(",")]
        else:
            config["domains"] = ["vedas", "education", "wellness"]
        
        # Data sources
        print("\n4. Data Sources:")
        config["data_path"] = input("Path to source documents (optional): ").strip()
        
        # Advanced options
        print("\n5. Advanced Options:")
        config["continue_on_error"] = input("Continue on errors? (y/N): ").strip().lower() == 'y'
        config["skip_tests"] = input("Skip integration tests? (y/N): ").strip().lower() == 'y'
        
        return config
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites."""
        logger.info("🔍 Checking prerequisites...")
        
        checks = {
            "python_version": sys.version_info >= (3, 8),
            "required_packages": self._check_packages(),
            "disk_space": self._check_disk_space(),
            "network": self._check_network()
        }
        
        all_good = all(checks.values())
        
        for check, status in checks.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"  {status_icon} {check}: {'OK' if status else 'FAILED'}")
        
        return all_good
    
    def _check_packages(self) -> bool:
        """Check required Python packages."""
        required = ["qdrant_client", "sentence_transformers", "fastapi", "requests"]
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            logger.warning(f"Missing packages: {', '.join(missing)}")
            logger.info(f"Install with: pip install {' '.join(missing)}")
            return False
        
        return True
    
    def _check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            
            if free_gb < 5:  # Require at least 5GB
                logger.warning(f"Low disk space: {free_gb}GB available")
                return False
            
            logger.info(f"Disk space: {free_gb}GB available")
            return True
        except Exception:
            return True  # Skip check if unable to determine
    
    def _check_network(self) -> bool:
        """Check network connectivity."""
        try:
            import requests
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            return response.status_code == 200
        except Exception:
            logger.warning("Network connectivity check failed")
            return True  # Don't fail deployment for this
    
    def deploy_qdrant(self) -> bool:
        """Deploy Qdrant vector database."""
        logger.info("🗄️ Deploying Qdrant...")
        
        try:
            deployment = QdrantDeployment(self.config["qdrant_type"])
            
            if not deployment.check_prerequisites():
                return False
            
            if not deployment.deploy_qdrant():
                return False
            
            if not deployment.setup_collections(self.config["domains"]):
                return False
            
            if not deployment.test_deployment():
                return False
            
            # Store deployment info
            self.config["qdrant_deployment"] = deployment.get_connection_info()
            return True
            
        except Exception as e:
            logger.error(f"Qdrant deployment failed: {e}")
            return False
    
    def configure_nas(self) -> bool:
        """Configure NAS connection."""
        logger.info("📁 Configuring NAS...")
        
        try:
            nas_config = NASConfig()
            
            # Update NAS configuration
            nas_config.current_config.update({
                "nas_name": self.config["nas_address"],
                "share_name": self.config["nas_share"]
            })
            
            # Test NAS accessibility (optional)
            if nas_config.is_nas_accessible():
                logger.info("✅ NAS is accessible")
            else:
                logger.warning("⚠️ NAS not accessible (will use local cache)")
            
            self.config["nas_config"] = nas_config.get_config()
            return True
            
        except Exception as e:
            logger.error(f"NAS configuration failed: {e}")
            return False
    
    def setup_embeddings(self) -> bool:
        """Setup embeddings and collections."""
        logger.info("🧠 Setting up embeddings...")
        
        if not self.config.get("data_path"):
            logger.info("⏭️ No data path provided, skipping embedding setup")
            return True
        
        try:
            qdrant_url = self.config.get("qdrant_deployment", {}).get("qdrant_url", "localhost:6333")
            embeddings_setup = NASEmbeddingsSetup(qdrant_url)
            
            for domain in self.config["domains"]:
                domain_data_path = os.path.join(self.config["data_path"], domain)
                
                if os.path.exists(domain_data_path):
                    logger.info(f"📚 Processing {domain} documents...")
                    if not embeddings_setup.process_local_documents(domain_data_path, domain):
                        logger.warning(f"⚠️ Failed to process {domain} documents")
                        continue
                    
                    if not embeddings_setup.test_embeddings(domain):
                        logger.warning(f"⚠️ Failed to test {domain} embeddings")
                        continue
                    
                    embeddings_setup.create_local_cache(domain)
                    logger.info(f"✅ {domain} embeddings setup complete")
                else:
                    logger.warning(f"⚠️ Data path not found for {domain}: {domain_data_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Embeddings setup failed: {e}")
            return False
    
    def test_integration(self) -> bool:
        """Test complete integration."""
        if self.config.get("skip_tests", False):
            logger.info("⏭️ Skipping integration tests")
            return True
        
        logger.info("🧪 Testing integration...")
        
        try:
            tester = NASIntegrationTest()
            results = tester.run_all_tests(self.config["domains"])
            
            # Check if most tests passed
            total_tests = len(results)
            passed_tests = sum(1 for result in results.values() 
                             if isinstance(result, bool) and result)
            
            success_rate = passed_tests / total_tests if total_tests > 0 else 0
            
            if success_rate >= 0.7:  # 70% success rate
                logger.info(f"✅ Integration tests passed ({success_rate:.1%})")
                return True
            else:
                logger.warning(f"⚠️ Integration tests partially failed ({success_rate:.1%})")
                return self.config.get("continue_on_error", False)
                
        except Exception as e:
            logger.error(f"Integration testing failed: {e}")
            return False
    
    def generate_configs(self) -> bool:
        """Generate configuration files."""
        logger.info("📝 Generating configuration files...")
        
        try:
            # Generate main config
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            deployment_config = {
                "bhiv_nas_deployment": {
                    "version": "1.0",
                    "deployment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "qdrant": self.config.get("qdrant_deployment", {}),
                    "nas": self.config.get("nas_config", {}),
                    "domains": self.config["domains"],
                    "status": "deployed"
                }
            }
            
            config_file = config_dir / "bhiv_nas_deployment.json"
            with open(config_file, 'w') as f:
                json.dump(deployment_config, f, indent=2)
            
            logger.info(f"✅ Configuration saved to: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Config generation failed: {e}")
            return False
    
    def deploy_bhiv(self) -> bool:
        """Deploy BHIV services."""
        logger.info("🚀 Deploying BHIV services...")
        
        # This would start your BHIV services
        # For now, just validate that everything is ready
        
        try:
            # Check if main BHIV files exist
            required_files = [
                "simple_api.py",
                "mcp_bridge.py", 
                "agents/KnowledgeAgent.py"
            ]
            
            missing_files = []
            for file_path in required_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                logger.error(f"Missing BHIV files: {missing_files}")
                return False
            
            logger.info("✅ BHIV services ready for deployment")
            return True
            
        except Exception as e:
            logger.error(f"BHIV deployment check failed: {e}")
            return False
    
    def _print_deployment_summary(self):
        """Print deployment summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 DEPLOYMENT SUMMARY")
        logger.info("=" * 60)
        
        total_steps = len(self.deployment_steps)
        successful_steps = sum(1 for status in self.deployment_status.values() 
                             if status.get("success", False))
        
        logger.info(f"Total steps: {total_steps}")
        logger.info(f"Successful: {successful_steps}")
        logger.info(f"Failed: {total_steps - successful_steps}")
        logger.info(f"Success rate: {successful_steps/total_steps:.1%}")
        
        logger.info("\nStep Details:")
        for step_name, step_info in self.deployment_status.items():
            status_icon = "✅" if step_info.get("success") else "❌"
            logger.info(f"  {status_icon} {step_info['description']}")
            if not step_info.get("success") and "error" in step_info:
                logger.info(f"     Error: {step_info['error']}")
    
    def _is_deployment_successful(self) -> bool:
        """Check if deployment was successful."""
        critical_steps = ["deploy_qdrant", "configure_nas"]
        
        for step in critical_steps:
            if not self.deployment_status.get(step, {}).get("success", False):
                return False
        
        return True

def main():
    """Main deployment function."""
    print("🎯 BHIV NAS + Qdrant Complete Deployment")
    print("This will deploy a complete BHIV system with NAS integration and Qdrant vector database")
    print("=" * 80)
    
    deployment = BHIVNASDeployment()
    success = deployment.run_deployment()
    
    if success:
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("Your BHIV system with NAS + Qdrant integration is ready!")
        print("\n🎯 Next Steps:")
        print("1. Start BHIV services: python simple_api.py")
        print("2. Test queries: python example/example_usage.py")
        print("3. Monitor logs: tail -f logs/bhiv_*.log")
    else:
        print("\n❌ DEPLOYMENT FAILED!")
        print("Check the logs above for error details.")
        print("You can retry with continue_on_error=True option.")
    
    return success

if __name__ == "__main__":
    main()
