#!/usr/bin/env python3
"""
Data Loader for Qdrant Knowledge Base
Loads PDF and text files into Qdrant vector database for the BHIV knowledge system.
"""

import os
import sys
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List
from utils.quadrant_loader import QdrantLoader
from utils.file_utils import secure_file_access
from utils.logger import get_logger
from config.settings import QDRANT_CONFIG

logger = get_logger(__name__)

class DataLoader:
    """Production-grade data loader for Qdrant knowledge base."""
    
    def __init__(self):
        self.loader = QdrantLoader()
        self.collection_name = QDRANT_CONFIG.get("collection_name", "vedas_knowledge_base")
        self.data_directory = os.getcwd()  # Current directory
        
    def initialize_qdrant(self):
        """Initialize Qdrant collection."""
        try:
            logger.info("Initializing Qdrant collection...")
            self.loader.initialize_collection()
            logger.info(f"Qdrant collection '{self.collection_name}' initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {str(e)}")
            return False
    
    def load_pdf_files(self, pdf_paths: List[str] = None) -> Dict[str, Any]:
        """Load PDF files into Qdrant."""
        if pdf_paths is None:
            # Auto-discover PDF files in current directory
            pdf_files = secure_file_access.list_files(self.data_directory, ['.pdf'])
            pdf_paths = [file['path'] for file in pdf_files]
        
        results = {
            "loaded": [],
            "failed": [],
            "total_files": len(pdf_paths),
            "total_chunks": 0
        }
        
        for pdf_path in pdf_paths:
            try:
                logger.info(f"Loading PDF: {pdf_path}")
                
                # Extract text using secure file access
                pdf_data = secure_file_access.read_pdf(pdf_path)
                
                if pdf_data["status"] != "success":
                    results["failed"].append({
                        "file": pdf_path,
                        "error": pdf_data.get("error", "Unknown error")
                    })
                    continue
                
                # Prepare metadata
                file_name = Path(pdf_path).stem
                metadata = {
                    "source": pdf_path,
                    "file_name": file_name,
                    "type": "vedic_text",  # Default type
                    "book": self._extract_book_name(file_name),
                    "version": "v1",
                    "total_pages": pdf_data["metadata"].get("total_pages", 0),
                    "file_size": pdf_data["metadata"].get("file_size", 0),
                    "loaded_at": str(uuid.uuid4())
                }
                
                # Load into Qdrant using the text content
                self._load_text_to_qdrant(pdf_data["text"], metadata)
                
                results["loaded"].append({
                    "file": pdf_path,
                    "metadata": metadata
                })
                
                logger.info(f"Successfully loaded {pdf_path}")
                
            except Exception as e:
                logger.error(f"Failed to load {pdf_path}: {str(e)}")
                results["failed"].append({
                    "file": pdf_path,
                    "error": str(e)
                })
        
        logger.info(f"PDF loading complete: {len(results['loaded'])} successful, {len(results['failed'])} failed")
        return results
    
    def load_text_files(self, text_paths: List[str] = None) -> Dict[str, Any]:
        """Load text files into Qdrant."""
        if text_paths is None:
            # Auto-discover text files in current directory
            text_files = secure_file_access.list_files(self.data_directory, ['.txt', '.md'])
            text_paths = [file['path'] for file in text_files]
        
        results = {
            "loaded": [],
            "failed": [],
            "total_files": len(text_paths)
        }
        
        for text_path in text_paths:
            try:
                logger.info(f"Loading text file: {text_path}")
                
                # Extract text using secure file access
                text_data = secure_file_access.read_text_file(text_path)
                
                if text_data["status"] != "success":
                    results["failed"].append({
                        "file": text_path,
                        "error": text_data.get("error", "Unknown error")
                    })
                    continue
                
                # Prepare metadata
                file_name = Path(text_path).stem
                metadata = {
                    "source": text_path,
                    "file_name": file_name,
                    "type": "text_document",
                    "book": file_name,
                    "version": "v1",
                    "file_size": text_data["metadata"].get("file_size", 0),
                    "line_count": text_data["metadata"].get("line_count", 0),
                    "loaded_at": str(uuid.uuid4())
                }
                
                # Load into Qdrant
                self._load_text_to_qdrant(text_data["text"], metadata)
                
                results["loaded"].append({
                    "file": text_path,
                    "metadata": metadata
                })
                
                logger.info(f"Successfully loaded {text_path}")
                
            except Exception as e:
                logger.error(f"Failed to load {text_path}: {str(e)}")
                results["failed"].append({
                    "file": text_path,
                    "error": str(e)
                })
        
        logger.info(f"Text loading complete: {len(results['loaded'])} successful, {len(results['failed'])} failed")
        return results
    
    def _load_text_to_qdrant(self, text: str, metadata: Dict[str, Any]):
        """Load text content to Qdrant with chunking."""
        try:
            # Use the QdrantLoader's chunking and embedding
            chunks = self.loader.splitter.split_text(text)
            embeddings = self.loader.model.encode(chunks)
            
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_metadata = metadata.copy()
                point_metadata.update({
                    "text": chunk,
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                })
                
                points.append({
                    "id": str(uuid.uuid4()),
                    "vector": embedding.tolist(),
                    "payload": point_metadata
                })
            
            # Insert into Qdrant
            from qdrant_client import models
            qdrant_points = [
                models.PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point["payload"]
                )
                for point in points
            ]
            
            self.loader.client.upsert(
                collection_name=self.collection_name,
                points=qdrant_points
            )
            
            logger.info(f"Loaded {len(points)} chunks to Qdrant")
            
        except Exception as e:
            logger.error(f"Failed to load text to Qdrant: {str(e)}")
            raise
    
    def _extract_book_name(self, file_name: str) -> str:
        """Extract book name from file name."""
        # Simple heuristic to extract book names
        file_name_lower = file_name.lower()
        
        vedic_books = {
            "rigveda": "rigveda",
            "samaveda": "samaveda", 
            "yajurveda": "yajurveda",
            "atharvaveda": "atharvaveda",
            "bhagavad": "bhagavad_gita",
            "gita": "bhagavad_gita",
            "upanishad": "upanishads",
            "purana": "puranas",
            "ramayana": "ramayana",
            "mahabharata": "mahabharata"
        }
        
        for key, book in vedic_books.items():
            if key in file_name_lower:
                return book
        
        return file_name  # Default to file name
    
    def check_qdrant_status(self) -> Dict[str, Any]:
        """Check Qdrant connection and collection status."""
        try:
            # Check connection
            collections = self.loader.client.get_collections()
            
            # Check if our collection exists
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            if collection_exists:
                collection_info = self.loader.client.get_collection(self.collection_name)
                return {
                    "status": "connected",
                    "collection_exists": True,
                    "collection_info": {
                        "name": collection_info.config.params.vectors[""].size,
                        "vector_count": collection_info.vectors_count,
                        "points_count": collection_info.points_count
                    }
                }
            else:
                return {
                    "status": "connected",
                    "collection_exists": False,
                    "message": f"Collection '{self.collection_name}' does not exist"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load data into Qdrant knowledge base")
    parser.add_argument("--init", action="store_true", help="Initialize Qdrant collection")
    parser.add_argument("--load-pdfs", action="store_true", help="Load PDF files")
    parser.add_argument("--load-texts", action="store_true", help="Load text files")
    parser.add_argument("--status", action="store_true", help="Check Qdrant status")
    parser.add_argument("--files", nargs="+", help="Specific files to load")
    
    args = parser.parse_args()
    
    loader = DataLoader()
    
    if args.status:
        status = loader.check_qdrant_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.init:
        if loader.initialize_qdrant():
            try:
                print("✅ Qdrant collection initialized successfully")
            except UnicodeEncodeError:
                print("[OK] Qdrant collection initialized successfully")
        else:
            try:
                print("❌ Failed to initialize Qdrant collection")
            except UnicodeEncodeError:
                print("[ERROR] Failed to initialize Qdrant collection")
            sys.exit(1)
    
    if args.load_pdfs:
        results = loader.load_pdf_files(args.files)
        try:
            print(f"📄 PDF Loading Results:")
        except UnicodeEncodeError:
            print("[PDF] Loading Results:")
        try:
            print(f"  ✅ Loaded: {len(results['loaded'])}")
            print(f"  ❌ Failed: {len(results['failed'])}")
        except UnicodeEncodeError:
            print(f"  [OK] Loaded: {len(results['loaded'])}")
            print(f"  [ERROR] Failed: {len(results['failed'])}")
        
        if results['failed']:
            print("Failed files:")
            for failed in results['failed']:
                print(f"  - {failed['file']}: {failed['error']}")
    
    if args.load_texts:
        results = loader.load_text_files(args.files)
        try:
            print(f"📝 Text Loading Results:")
        except UnicodeEncodeError:
            print("[TEXT] Loading Results:")
        try:
            print(f"  ✅ Loaded: {len(results['loaded'])}")
            print(f"  ❌ Failed: {len(results['failed'])}")
        except UnicodeEncodeError:
            print(f"  [OK] Loaded: {len(results['loaded'])}")
            print(f"  [ERROR] Failed: {len(results['failed'])}")
        
        if results['failed']:
            print("Failed files:")
            for failed in results['failed']:
                print(f"  - {failed['file']}: {failed['error']}")
    
    if not any([args.init, args.load_pdfs, args.load_texts, args.status]):
        print("No action specified. Use --help for options.")


if __name__ == "__main__":
    main()
