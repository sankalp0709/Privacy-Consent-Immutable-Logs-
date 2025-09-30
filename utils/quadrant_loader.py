import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
import os
import uuid
from utils.logger import get_logger

logger = get_logger(__name__)

class QdrantLoader:
    def __init__(self, qdrant_url="localhost:6333", collection_name="vedas_knowledge_base"):
        self.client = QdrantClient(qdrant_url, prefer_grpc=False)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # Matches 384-dim vectors
        self.collection_name = collection_name

    def initialize_collection(self):
        """Create or recreate the Qdrant collection as per meta.json."""
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Initialized Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {str(e)}")

    def load_pdf(self, pdf_path: str, metadata: dict) -> None:
        """Load a PDF into Qdrant with metadata."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "".join(page.extract_text() or "" for page in pdf.pages)
            chunks = self.splitter.split_text(text)
            embeddings = self.model.encode(chunks)
            points = [
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={**metadata, "text": chunk}
                )
                for chunk, embedding in zip(chunks, embeddings)
            ]
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Loaded {len(points)} chunks from {pdf_path} into {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to load PDF {pdf_path}: {str(e)}")