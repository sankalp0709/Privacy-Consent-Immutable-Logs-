import os
import pdfplumber
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class SecureFileAccess:
    """Secure file access utility with permission guardrails."""
    
    def __init__(self, allowed_paths: List[str] = None, read_only: bool = True):
        """
        Initialize secure file access.
        
        Args:
            allowed_paths: List of allowed base paths for file access
            read_only: If True, only allow read operations
        """
        self.read_only = read_only
        self.allowed_paths = allowed_paths or [
            os.getcwd(),  # Current working directory
            "/mnt/vedabase",  # NAS mount point (Linux)
            "//nas/vedabase",  # NAS mount point (Windows)
            "Z:/vedabase",  # Mapped drive (Windows)
            "//your-company-nas/vedabase",  # Your company NAS
            "//your-company-nas/shared/vedabase",  # Alternative company path
            "Y:/vedabase"  # Alternative mapped drive
        ]
        
        # Normalize paths
        self.allowed_paths = [os.path.abspath(path) for path in self.allowed_paths]
        logger.info(f"SecureFileAccess initialized with paths: {self.allowed_paths}, read_only: {read_only}")

    def _is_path_allowed(self, file_path: str) -> bool:
        """Check if the file path is within allowed directories."""
        try:
            abs_path = os.path.abspath(file_path)
            return any(abs_path.startswith(allowed) for allowed in self.allowed_paths)
        except Exception as e:
            logger.error(f"Path validation failed for {file_path}: {str(e)}")
            return False

    def _validate_file_type(self, file_path: str, allowed_types: List[str] = None) -> bool:
        """Validate file type based on extension and MIME type."""
        if allowed_types is None:
            allowed_types = ['.pdf', '.txt', '.md', '.json']
        
        # Check extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in allowed_types:
            return False
        
        # Check MIME type for additional security
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            safe_mime_types = [
                'application/pdf',
                'text/plain',
                'text/markdown',
                'application/json'
            ]
            return mime_type in safe_mime_types or mime_type is None
        except Exception:
            return True  # Allow if MIME detection fails

    def read_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Safely read and extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            # Security checks
            if not self._is_path_allowed(pdf_path):
                raise PermissionError(f"Access denied: {pdf_path} is not in allowed paths")
            
            if not self._validate_file_type(pdf_path, ['.pdf']):
                raise ValueError(f"Invalid file type: {pdf_path}")
            
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"File not found: {pdf_path}")
            
            # Extract text using pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text_content = []
                metadata = {
                    "total_pages": len(pdf.pages),
                    "file_path": pdf_path,
                    "file_size": os.path.getsize(pdf_path)
                }
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append({
                            "page": page_num,
                            "text": page_text.strip()
                        })
                
                # Combine all text
                full_text = "\n\n".join([page["text"] for page in text_content])
                
                result = {
                    "text": full_text,
                    "pages": text_content,
                    "metadata": metadata,
                    "status": "success"
                }
                
                logger.info(f"Successfully extracted text from {pdf_path}: {len(full_text)} characters")
                return result
                
        except Exception as e:
            logger.error(f"Failed to read PDF {pdf_path}: {str(e)}")
            return {
                "text": "",
                "pages": [],
                "metadata": {},
                "status": "error",
                "error": str(e)
            }

    def read_text_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Safely read a text file.
        
        Args:
            file_path: Path to the text file
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dict containing file content and metadata
        """
        try:
            # Security checks
            if not self._is_path_allowed(file_path):
                raise PermissionError(f"Access denied: {file_path} is not in allowed paths")
            
            if not self._validate_file_type(file_path, ['.txt', '.md', '.json']):
                raise ValueError(f"Invalid file type: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            metadata = {
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "encoding": encoding,
                "line_count": content.count('\n') + 1
            }
            
            result = {
                "text": content,
                "metadata": metadata,
                "status": "success"
            }
            
            logger.info(f"Successfully read text file {file_path}: {len(content)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Failed to read text file {file_path}: {str(e)}")
            return {
                "text": "",
                "metadata": {},
                "status": "error",
                "error": str(e)
            }

    def list_files(self, directory: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Safely list files in a directory.
        
        Args:
            directory: Directory path to list
            file_types: List of allowed file extensions
            
        Returns:
            List of file information dictionaries
        """
        if file_types is None:
            file_types = ['.pdf', '.txt', '.md', '.json']
        
        try:
            # Security checks
            if not self._is_path_allowed(directory):
                raise PermissionError(f"Access denied: {directory} is not in allowed paths")
            
            if not os.path.exists(directory):
                raise FileNotFoundError(f"Directory not found: {directory}")
            
            files = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                if os.path.isfile(item_path):
                    file_ext = Path(item).suffix.lower()
                    if file_ext in file_types:
                        files.append({
                            "name": item,
                            "path": item_path,
                            "size": os.path.getsize(item_path),
                            "extension": file_ext,
                            "modified": os.path.getmtime(item_path)
                        })
            
            logger.info(f"Listed {len(files)} files in {directory}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {str(e)}")
            return []

    def check_nas_mount(self) -> Dict[str, Any]:
        """Check if NAS is properly mounted and accessible."""
        nas_paths = [
            "/mnt/vedabase",
            "//nas/vedabase", 
            "Z:/vedabase"
        ]
        
        status = {
            "mounted": False,
            "accessible_paths": [],
            "errors": []
        }
        
        for path in nas_paths:
            try:
                if os.path.exists(path) and os.path.isdir(path):
                    # Try to list directory to verify access
                    os.listdir(path)
                    status["accessible_paths"].append(path)
                    status["mounted"] = True
                    logger.info(f"NAS accessible at: {path}")
            except Exception as e:
                status["errors"].append(f"{path}: {str(e)}")
                logger.warning(f"NAS not accessible at {path}: {str(e)}")
        
        return status


# Global instance for easy access
secure_file_access = SecureFileAccess()
