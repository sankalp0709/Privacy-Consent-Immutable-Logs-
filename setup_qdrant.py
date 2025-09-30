#!/usr/bin/env python3
"""
Qdrant Setup and Management Script
Handles Qdrant installation, startup, and basic configuration for the BHIV knowledge system.
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

class QdrantManager:
    """Manage Qdrant vector database setup and operations."""
    
    def __init__(self, qdrant_url="http://localhost:6333"):
        self.qdrant_url = qdrant_url
        self.docker_image = "qdrant/qdrant:latest"
        self.container_name = "bhiv-qdrant"
        
    def check_qdrant_running(self) -> bool:
        """Check if Qdrant is running and accessible."""
        try:
            response = requests.get(f"{self.qdrant_url}/collections", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Qdrant not accessible: {str(e)}")
            return False
    
    def check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Docker not available: {str(e)}")
            return False
    
    def start_qdrant_docker(self, data_path: str = None) -> bool:
        """Start Qdrant using Docker."""
        try:
            # Stop existing container if running
            self.stop_qdrant_docker()
            
            # Prepare data directory
            if data_path is None:
                data_path = os.path.join(os.getcwd(), "qdrant_data")
            
            os.makedirs(data_path, exist_ok=True)
            logger.info(f"Using Qdrant data directory: {data_path}")
            
            # Docker run command
            cmd = [
                "docker", "run", "-d",
                "--name", self.container_name,
                "-p", "6333:6333",
                "-p", "6334:6334",
                "-v", f"{data_path}:/qdrant/storage",
                self.docker_image
            ]
            
            logger.info("Starting Qdrant with Docker...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("Qdrant container started successfully")
                
                # Wait for Qdrant to be ready
                for i in range(30):  # Wait up to 30 seconds
                    if self.check_qdrant_running():
                        logger.info("Qdrant is ready and accessible")
                        return True
                    time.sleep(1)
                
                logger.warning("Qdrant started but not accessible within timeout")
                return False
            else:
                logger.error(f"Failed to start Qdrant: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Qdrant: {str(e)}")
            return False
    
    def stop_qdrant_docker(self) -> bool:
        """Stop Qdrant Docker container."""
        try:
            # Check if container exists
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if self.container_name in result.stdout:
                logger.info("Stopping existing Qdrant container...")
                subprocess.run(["docker", "stop", self.container_name], timeout=30)
                subprocess.run(["docker", "rm", self.container_name], timeout=30)
                logger.info("Qdrant container stopped and removed")
            
            return True
            
        except Exception as e:
            logger.warning(f"Error stopping Qdrant container: {str(e)}")
            return False
    
    def install_qdrant_binary(self) -> bool:
        """Install Qdrant binary (alternative to Docker)."""
        try:
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                logger.info("For Windows, please use Docker or download Qdrant binary manually from:")
                logger.info("https://github.com/qdrant/qdrant/releases")
                return False
            
            elif system in ["linux", "darwin"]:  # Linux or macOS
                logger.info("Installing Qdrant binary...")
                
                # Download and install script would go here
                # For now, recommend Docker or manual installation
                logger.info("Please install Qdrant using Docker or download from:")
                logger.info("https://github.com/qdrant/qdrant/releases")
                return False
            
            else:
                logger.error(f"Unsupported system: {system}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing Qdrant: {str(e)}")
            return False
    
    def get_qdrant_status(self) -> dict:
        """Get detailed Qdrant status information."""
        status = {
            "running": False,
            "accessible": False,
            "version": None,
            "collections": [],
            "docker_available": self.check_docker_available(),
            "container_running": False
        }
        
        try:
            # Check if accessible
            if self.check_qdrant_running():
                status["running"] = True
                status["accessible"] = True
                
                # Get version
                try:
                    response = requests.get(f"{self.qdrant_url}/", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        status["version"] = data.get("version", "unknown")
                except Exception:
                    pass
                
                # Get collections
                try:
                    response = requests.get(f"{self.qdrant_url}/collections", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        status["collections"] = [col["name"] for col in data.get("result", {}).get("collections", [])]
                except Exception:
                    pass
            
            # Check Docker container status
            if status["docker_available"]:
                try:
                    result = subprocess.run(
                        ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    status["container_running"] = self.container_name in result.stdout
                except Exception:
                    pass
        
        except Exception as e:
            logger.error(f"Error getting Qdrant status: {str(e)}")
        
        return status
    
    def setup_qdrant(self, data_path: str = None) -> bool:
        """Complete Qdrant setup process."""
        logger.info("Starting Qdrant setup...")
        
        # Check if already running
        if self.check_qdrant_running():
            logger.info("✅ Qdrant is already running and accessible")
            return True
        
        # Try Docker setup
        if self.check_docker_available():
            logger.info("Docker is available, using Docker setup...")
            if self.start_qdrant_docker(data_path):
                logger.info("✅ Qdrant setup complete using Docker")
                return True
            else:
                logger.error("❌ Failed to start Qdrant with Docker")
        else:
            logger.warning("Docker not available")
        
        # Fallback instructions
        logger.info("Manual setup required:")
        logger.info("1. Install Docker and run: docker run -p 6333:6333 qdrant/qdrant")
        logger.info("2. Or download Qdrant binary from: https://github.com/qdrant/qdrant/releases")
        logger.info("3. Or use cloud Qdrant service")
        
        return False


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Qdrant setup and management")
    parser.add_argument("--start", action="store_true", help="Start Qdrant using Docker")
    parser.add_argument("--stop", action="store_true", help="Stop Qdrant Docker container")
    parser.add_argument("--status", action="store_true", help="Check Qdrant status")
    parser.add_argument("--setup", action="store_true", help="Complete Qdrant setup")
    parser.add_argument("--data-path", help="Custom data directory for Qdrant")
    
    args = parser.parse_args()
    
    manager = QdrantManager()
    
    if args.status:
        status = manager.get_qdrant_status()
        print("🔍 Qdrant Status:")
        print(f"  Running: {'✅' if status['running'] else '❌'}")
        print(f"  Accessible: {'✅' if status['accessible'] else '❌'}")
        print(f"  Version: {status['version'] or 'Unknown'}")
        print(f"  Collections: {', '.join(status['collections']) or 'None'}")
        print(f"  Docker Available: {'✅' if status['docker_available'] else '❌'}")
        print(f"  Container Running: {'✅' if status['container_running'] else '❌'}")
        return
    
    if args.stop:
        if manager.stop_qdrant_docker():
            print("✅ Qdrant stopped successfully")
        else:
            print("❌ Failed to stop Qdrant")
        return
    
    if args.start:
        if manager.start_qdrant_docker(args.data_path):
            print("✅ Qdrant started successfully")
        else:
            print("❌ Failed to start Qdrant")
        return
    
    if args.setup:
        if manager.setup_qdrant(args.data_path):
            print("✅ Qdrant setup completed successfully")
        else:
            print("❌ Qdrant setup failed")
        return
    
    if not any([args.start, args.stop, args.status, args.setup]):
        print("No action specified. Use --help for options.")


if __name__ == "__main__":
    main()
