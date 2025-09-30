#!/usr/bin/env python3
"""
Complete Knowledge Base Setup Script
Sets up the entire BHIV knowledge base system including Qdrant, data loading, and API integration.
"""

import os
import sys
import time
import json
from pathlib import Path
from setup_qdrant import QdrantManager
from load_data_to_qdrant import DataLoader
from utils.logger import get_logger
from utils.file_utils import secure_file_access

logger = get_logger(__name__)

class KnowledgeBaseSetup:
    """Complete knowledge base setup and management."""
    
    def __init__(self):
        self.qdrant_manager = QdrantManager()
        self.data_loader = DataLoader()
        self.setup_steps = [
            ("check_requirements", "Check system requirements"),
            ("setup_qdrant", "Setup Qdrant vector database"),
            ("initialize_collection", "Initialize Qdrant collection"),
            ("load_data", "Load data files into knowledge base"),
            ("verify_setup", "Verify knowledge base setup"),
            ("test_queries", "Test knowledge base queries")
        ]
    
    def check_requirements(self) -> bool:
        """Check system requirements."""
        logger.info("🔍 Checking system requirements...")
        
        requirements = {
            "python_version": sys.version_info >= (3, 8),
            "data_files": self._check_data_files(),
            "dependencies": self._check_dependencies(),
            "file_access": self._check_file_access()
        }
        
        all_good = all(requirements.values())
        
        for req, status in requirements.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"  {status_icon} {req}: {'OK' if status else 'FAILED'}")
        
        if not all_good:
            logger.error("❌ System requirements not met")
            self._print_requirements_help()
        
        return all_good
    
    def _check_data_files(self) -> bool:
        """Check if data files are available."""
        try:
            pdf_files = secure_file_access.list_files(os.getcwd(), ['.pdf'])
            text_files = secure_file_access.list_files(os.getcwd(), ['.txt', '.md'])
            
            total_files = len(pdf_files) + len(text_files)
            logger.info(f"    Found {len(pdf_files)} PDF files and {len(text_files)} text files")
            
            return total_files > 0
        except Exception as e:
            logger.error(f"    Error checking data files: {str(e)}")
            return False
    
    def _check_dependencies(self) -> bool:
        """Check if required Python packages are installed."""
        required_packages = [
            "qdrant_client",
            "sentence_transformers", 
            "langchain",
            "pdfplumber",
            "fastapi",
            "requests"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            logger.warning(f"    Missing packages: {', '.join(missing)}")
            logger.info(f"    Install with: pip install {' '.join(missing)}")
            return False
        
        return True
    
    def _check_file_access(self) -> bool:
        """Check file access permissions."""
        try:
            # Test file access
            test_files = secure_file_access.list_files(os.getcwd())
            return len(test_files) >= 0  # Should at least return empty list
        except Exception as e:
            logger.error(f"    File access error: {str(e)}")
            return False
    
    def setup_qdrant(self) -> bool:
        """Setup Qdrant vector database."""
        logger.info("🚀 Setting up Qdrant vector database...")
        
        # Check if already running
        if self.qdrant_manager.check_qdrant_running():
            logger.info("  ✅ Qdrant is already running")
            return True
        
        # Setup Qdrant
        if self.qdrant_manager.setup_qdrant():
            logger.info("  ✅ Qdrant setup completed")
            return True
        else:
            logger.error("  ❌ Qdrant setup failed")
            return False
    
    def initialize_collection(self) -> bool:
        """Initialize Qdrant collection."""
        logger.info("📊 Initializing Qdrant collection...")
        
        if self.data_loader.initialize_qdrant():
            logger.info("  ✅ Collection initialized successfully")
            return True
        else:
            logger.error("  ❌ Collection initialization failed")
            return False
    
    def load_data(self) -> bool:
        """Load data files into knowledge base."""
        logger.info("📚 Loading data into knowledge base...")
        
        success = True
        
        # Load PDF files
        pdf_results = self.data_loader.load_pdf_files()
        if pdf_results["total_files"] > 0:
            logger.info(f"  📄 PDF files: {len(pdf_results['loaded'])} loaded, {len(pdf_results['failed'])} failed")
            if pdf_results["failed"]:
                success = False
                for failed in pdf_results["failed"]:
                    logger.error(f"    ❌ {failed['file']}: {failed['error']}")
        
        # Load text files
        text_results = self.data_loader.load_text_files()
        if text_results["total_files"] > 0:
            logger.info(f"  📝 Text files: {len(text_results['loaded'])} loaded, {len(text_results['failed'])} failed")
            if text_results["failed"]:
                success = False
                for failed in text_results["failed"]:
                    logger.error(f"    ❌ {failed['file']}: {failed['error']}")
        
        total_loaded = len(pdf_results["loaded"]) + len(text_results["loaded"])
        if total_loaded == 0:
            logger.warning("  ⚠️ No files were loaded into the knowledge base")
            return False
        
        logger.info(f"  ✅ Total files loaded: {total_loaded}")
        return success
    
    def verify_setup(self) -> bool:
        """Verify knowledge base setup."""
        logger.info("🔍 Verifying knowledge base setup...")
        
        try:
            # Check Qdrant status
            status = self.data_loader.check_qdrant_status()
            
            if status["status"] != "connected":
                logger.error(f"  ❌ Qdrant connection failed: {status.get('error', 'Unknown error')}")
                return False
            
            if not status["collection_exists"]:
                logger.error("  ❌ Collection does not exist")
                return False
            
            collection_info = status.get("collection_info", {})
            points_count = collection_info.get("points_count", 0)
            
            if points_count == 0:
                logger.warning("  ⚠️ No data points found in collection")
                return False
            
            logger.info(f"  ✅ Collection verified: {points_count} data points")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Verification failed: {str(e)}")
            return False
    
    def test_queries(self) -> bool:
        """Test knowledge base queries."""
        logger.info("🧪 Testing knowledge base queries...")
        
        try:
            from agents.KnowledgeAgent import KnowledgeAgent
            
            # Initialize knowledge agent
            agent = KnowledgeAgent()
            
            # Test queries
            test_queries = [
                "What is the meaning of life?",
                "Tell me about dharma",
                "What is meditation?"
            ]
            
            success_count = 0
            for query in test_queries:
                try:
                    result = agent.query(query)
                    if result["status"] == "success" and result["results"]:
                        success_count += 1
                        logger.info(f"  ✅ Query '{query}': {len(result['results'])} results")
                    else:
                        logger.warning(f"  ⚠️ Query '{query}': No results")
                except Exception as e:
                    logger.error(f"  ❌ Query '{query}': {str(e)}")
            
            if success_count > 0:
                logger.info(f"  ✅ {success_count}/{len(test_queries)} test queries successful")
                return True
            else:
                logger.error("  ❌ All test queries failed")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Query testing failed: {str(e)}")
            return False
    
    def run_complete_setup(self) -> bool:
        """Run the complete knowledge base setup process."""
        logger.info("🚀 Starting complete knowledge base setup...")
        logger.info("=" * 60)
        
        overall_success = True
        
        for step_func, step_desc in self.setup_steps:
            logger.info(f"\n📋 Step: {step_desc}")
            logger.info("-" * 40)
            
            try:
                step_method = getattr(self, step_func)
                success = step_method()
                
                if success:
                    logger.info(f"✅ {step_desc} completed successfully")
                else:
                    logger.error(f"❌ {step_desc} failed")
                    overall_success = False
                    
                    # Ask user if they want to continue
                    if not self._ask_continue():
                        logger.info("Setup aborted by user")
                        return False
                        
            except Exception as e:
                logger.error(f"❌ {step_desc} failed with error: {str(e)}")
                overall_success = False
                
                if not self._ask_continue():
                    logger.info("Setup aborted by user")
                    return False
        
        logger.info("\n" + "=" * 60)
        if overall_success:
            logger.info("🎉 Knowledge base setup completed successfully!")
            self._print_next_steps()
        else:
            logger.warning("⚠️ Knowledge base setup completed with some issues")
            self._print_troubleshooting()
        
        return overall_success
    
    def _ask_continue(self) -> bool:
        """Ask user if they want to continue after a failure."""
        try:
            response = input("Continue with next step? (y/n): ").lower().strip()
            return response in ['y', 'yes']
        except KeyboardInterrupt:
            return False
    
    def _print_requirements_help(self):
        """Print help for fixing requirements."""
        logger.info("\n📋 To fix requirements:")
        logger.info("1. Ensure Python 3.8+ is installed")
        logger.info("2. Install dependencies: pip install -r requirements.txt")
        logger.info("3. Add PDF or text files to the current directory")
        logger.info("4. Ensure file access permissions are correct")
    
    def _print_next_steps(self):
        """Print next steps after successful setup."""
        logger.info("\n🎯 Next Steps:")
        logger.info("1. Start the API server: python simple_api.py --port 8001")
        logger.info("2. Start the MCP bridge: python mcp_bridge.py")
        logger.info("3. Test the knowledge base: curl 'http://localhost:8001/query-kb?query=your_question'")
        logger.info("4. Integrate with your applications using the /query-kb endpoint")
    
    def _print_troubleshooting(self):
        """Print troubleshooting information."""
        logger.info("\n🔧 Troubleshooting:")
        logger.info("1. Check Qdrant status: python setup_qdrant.py --status")
        logger.info("2. Restart Qdrant: python setup_qdrant.py --stop && python setup_qdrant.py --start")
        logger.info("3. Reload data: python load_data_to_qdrant.py --init --load-pdfs --load-texts")
        logger.info("4. Check logs for detailed error messages")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete knowledge base setup")
    parser.add_argument("--full-setup", action="store_true", help="Run complete setup process")
    parser.add_argument("--check-only", action="store_true", help="Only check requirements")
    
    args = parser.parse_args()
    
    setup = KnowledgeBaseSetup()
    
    if args.check_only:
        if setup.check_requirements():
            print("✅ All requirements met")
            sys.exit(0)
        else:
            print("❌ Requirements not met")
            sys.exit(1)
    
    if args.full_setup or not any(vars(args).values()):
        success = setup.run_complete_setup()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
