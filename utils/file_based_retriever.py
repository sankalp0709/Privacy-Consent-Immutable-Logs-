#!/usr/bin/env python3
"""
File-Based Knowledge Retriever
A simple alternative to Qdrant that works with local files for knowledge retrieval.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from utils.file_utils import secure_file_access
from utils.logger import get_logger

logger = get_logger(__name__)

class FileBasedRetriever:
    """Simple file-based knowledge retriever using semantic similarity."""
    
    def __init__(self, data_directory: str = None, cache_file: str = "knowledge_cache.json"):
        self.data_directory = data_directory or os.getcwd()
        self.cache_file = os.path.join(self.data_directory, cache_file)
        self.model = None
        self.knowledge_chunks = []
        self.chunk_embeddings = None
        
        # Initialize embedding model
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("FileBasedRetriever initialized with SentenceTransformer")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            self.model = None
        
        # Load or build knowledge base
        self._load_or_build_knowledge_base()
    
    def _load_or_build_knowledge_base(self):
        """Load existing knowledge base or build from files."""
        if os.path.exists(self.cache_file):
            try:
                self._load_from_cache()
                logger.info(f"Loaded knowledge base from cache: {len(self.knowledge_chunks)} chunks")
                return
            except Exception as e:
                logger.warning(f"Failed to load cache, rebuilding: {str(e)}")
        
        # Build from files
        self._build_from_files()
    
    def _load_from_cache(self):
        """Load knowledge base from cache file."""
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        self.knowledge_chunks = cache_data.get('chunks', [])
        embeddings_data = cache_data.get('embeddings', [])
        
        if embeddings_data and self.model:
            self.chunk_embeddings = np.array(embeddings_data)
        else:
            # Regenerate embeddings if model is available
            if self.model and self.knowledge_chunks:
                texts = [chunk['text'] for chunk in self.knowledge_chunks]
                self.chunk_embeddings = self.model.encode(texts)
                self._save_to_cache()
    
    def _build_from_files(self):
        """Build knowledge base from files in the directory."""
        logger.info("Building knowledge base from files...")
        
        self.knowledge_chunks = []
        
        # Process PDF files
        pdf_files = secure_file_access.list_files(self.data_directory, ['.pdf'])
        for pdf_file in pdf_files:
            self._process_pdf_file(pdf_file['path'])
        
        # Process text files
        text_files = secure_file_access.list_files(self.data_directory, ['.txt', '.md'])
        for text_file in text_files:
            self._process_text_file(text_file['path'])
        
        # Generate embeddings if model is available
        if self.model and self.knowledge_chunks:
            texts = [chunk['text'] for chunk in self.knowledge_chunks]
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            self.chunk_embeddings = self.model.encode(texts)
            
            # Save to cache
            self._save_to_cache()
        
        logger.info(f"Knowledge base built: {len(self.knowledge_chunks)} chunks")
    
    def _process_pdf_file(self, pdf_path: str):
        """Process a PDF file and extract chunks."""
        try:
            pdf_data = secure_file_access.read_pdf(pdf_path)
            
            if pdf_data['status'] == 'success':
                file_name = Path(pdf_path).stem
                text = pdf_data['text']
                
                # Split into chunks
                chunks = self._split_text(text)
                
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # Skip empty chunks
                        self.knowledge_chunks.append({
                            'text': chunk.strip(),
                            'source': pdf_path,
                            'file_name': file_name,
                            'chunk_id': i,
                            'type': 'pdf',
                            'metadata': {
                                'total_pages': pdf_data['metadata'].get('total_pages', 0),
                                'file_size': pdf_data['metadata'].get('file_size', 0)
                            }
                        })
                
                logger.info(f"Processed PDF {pdf_path}: {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {str(e)}")
    
    def _process_text_file(self, text_path: str):
        """Process a text file and extract chunks."""
        try:
            text_data = secure_file_access.read_text_file(text_path)
            
            if text_data['status'] == 'success':
                file_name = Path(text_path).stem
                text = text_data['text']
                
                # Split into chunks
                chunks = self._split_text(text)
                
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # Skip empty chunks
                        self.knowledge_chunks.append({
                            'text': chunk.strip(),
                            'source': text_path,
                            'file_name': file_name,
                            'chunk_id': i,
                            'type': 'text',
                            'metadata': {
                                'line_count': text_data['metadata'].get('line_count', 0),
                                'file_size': text_data['metadata'].get('file_size', 0)
                            }
                        })
                
                logger.info(f"Processed text file {text_path}: {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to process text file {text_path}: {str(e)}")
    
    def _split_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        # Simple sentence-based splitting
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_words = words[-overlap//10:] if len(words) > overlap//10 else words
                current_chunk = " ".join(overlap_words) + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _save_to_cache(self):
        """Save knowledge base to cache file."""
        try:
            cache_data = {
                'chunks': self.knowledge_chunks,
                'embeddings': self.chunk_embeddings.tolist() if self.chunk_embeddings is not None else []
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Knowledge base cached to {self.cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {str(e)}")
    
    def search(self, query: str, limit: int = 5, min_similarity: float = 0.1) -> List[Dict[str, Any]]:
        """Search for relevant chunks using semantic similarity."""
        if not self.knowledge_chunks:
            logger.warning("No knowledge chunks available")
            return []
        
        if not self.model or self.chunk_embeddings is None:
            logger.warning("No embeddings available, using keyword search")
            return self._keyword_search(query, limit)
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.chunk_embeddings)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:limit]
            
            results = []
            for idx in top_indices:
                similarity = similarities[idx]
                if similarity >= min_similarity:
                    chunk = self.knowledge_chunks[idx].copy()
                    chunk['similarity_score'] = float(similarity)
                    results.append(chunk)
            
            logger.info(f"Semantic search found {len(results)} results for: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            return self._keyword_search(query, limit)
    
    def _keyword_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback keyword-based search."""
        query_words = set(query.lower().split())
        results = []
        
        for chunk in self.knowledge_chunks:
            text_words = set(chunk['text'].lower().split())
            common_words = query_words.intersection(text_words)
            
            if common_words:
                score = len(common_words) / len(query_words)
                chunk_copy = chunk.copy()
                chunk_copy['similarity_score'] = score
                results.append(chunk_copy)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        logger.info(f"Keyword search found {len(results[:limit])} results for: {query}")
        return results[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        if not self.knowledge_chunks:
            return {"total_chunks": 0, "sources": [], "types": []}
        
        sources = list(set(chunk['source'] for chunk in self.knowledge_chunks))
        types = list(set(chunk['type'] for chunk in self.knowledge_chunks))
        
        return {
            "total_chunks": len(self.knowledge_chunks),
            "sources": sources,
            "types": types,
            "has_embeddings": self.chunk_embeddings is not None,
            "embedding_model": "all-MiniLM-L6-v2" if self.model else None
        }
    
    def rebuild_cache(self):
        """Force rebuild of the knowledge base cache."""
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        self._build_from_files()


# Global instance
file_retriever = FileBasedRetriever()
