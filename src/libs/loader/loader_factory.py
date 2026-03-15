"""Loader factory for selecting document loaders by file extension.

This module provides a factory that returns the appropriate loader
based on file suffix, enabling multi-format ingestion (PDF, DOCX, etc.).
"""

from __future__ import annotations

from pathlib import Path

from src.core.settings import resolve_path
from src.libs.loader.base_loader import BaseLoader
from src.libs.loader.docx_loader import DocxLoader
from src.libs.loader.pdf_loader import PdfLoader

LOADER_MAP: dict[str, type[BaseLoader]] = {
    ".pdf": PdfLoader,
    ".docx": DocxLoader,
}


def get_loader(
    file_path: str | Path,
    collection: str = "default",
    extract_images: bool = True,
) -> BaseLoader:
    """Return the appropriate loader for the given file.

    Args:
        file_path: Path to the document file.
        collection: Collection name (used for image_storage_dir by PDF/DOCX loaders).
        extract_images: Whether to extract images (PDF and DOCX loaders).

    Returns:
        Loader instance for the given file type.

    Raises:
        ValueError: If file suffix is not supported.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix not in LOADER_MAP:
        raise ValueError(
            f"Unsupported file type: {suffix}. Supported: {list(LOADER_MAP.keys())}"
        )

    loader_cls = LOADER_MAP[suffix]

    if loader_cls is PdfLoader:
        image_storage_dir = str(resolve_path(f"data/images/{collection}"))
        return PdfLoader(
            extract_images=extract_images,
            image_storage_dir=image_storage_dir,
        )

    if loader_cls is DocxLoader:
        image_storage_dir = str(resolve_path(f"data/images/{collection}"))
        return DocxLoader(
            extract_images=extract_images,
            image_storage_dir=image_storage_dir,
        )

    return loader_cls()
