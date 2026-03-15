"""
Loader Module.

This package contains document loader components:
- Base loader class
- PDF loader
- DOCX loader
- Loader factory
- File integrity checker
"""

from src.libs.loader.base_loader import BaseLoader
from src.libs.loader.docx_loader import DocxLoader
from src.libs.loader.file_integrity import FileIntegrityChecker, SQLiteIntegrityChecker
from src.libs.loader.loader_factory import LOADER_MAP, get_loader
from src.libs.loader.pdf_loader import PdfLoader

__all__ = [
    "BaseLoader",
    "DocxLoader",
    "FileIntegrityChecker",
    "LOADER_MAP",
    "get_loader",
    "PdfLoader",
    "SQLiteIntegrityChecker",
]
