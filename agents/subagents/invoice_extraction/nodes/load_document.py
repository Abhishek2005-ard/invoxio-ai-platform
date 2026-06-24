"""
Node 1 — load_document

Responsibility:
  - Detect file type (PDF or image)
  - For PDFs  → extract text per page using PyMuPDF (fitz)
               → also render each page as an image (for Gemini Vision fallback)
  - For images → load raw bytes directly for Gemini Vision
  - Populate: pages, page_images, doc_meta

Pipeline: [load_document] → ocr_extract → parse_invoice → validate_output
"""

import io
import base64
from typing import List, Dict, Any

from subagents.invoice_extraction.state import InvoiceExtractionState


async def load_document_node(state: InvoiceExtractionState) -> dict:
    """
    Loads and pre-processes the uploaded file.

    - PDF  → PyMuPDF text + page images
    - Image→ raw bytes ready for Gemini Vision
    """
    file_bytes = state["file_bytes"]
    file_name  = state["file_name"].lower()

    print(f"\n📂 [load_document] Processing: {state['file_name']} ({len(file_bytes):,} bytes)")

    # ── Detect file type ──────────────────────────────────────────────────
    if file_name.endswith(".pdf"):
        file_type = "pdf"
        pages, page_images, meta = await _load_pdf(file_bytes)
    elif file_name.endswith((".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp")):
        file_type = "image"
        pages, page_images, meta = await _load_image(file_bytes)
    else:
        return {
            "error": f"Unsupported file type: {file_name}. Supported: PDF, JPG, PNG, WEBP.",
            "is_valid": False,
        }

    print(f"✅ [load_document] Type: {file_type} | Pages: {meta['page_count']} | "
          f"Text chars: {meta['total_text_chars']}")

    return {
        "file_type":   file_type,
        "pages":       pages,
        "page_images": page_images,
        "doc_meta":    meta,
    }


async def _load_pdf(file_bytes: bytes):
    """Extracts text and page images from a PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError("PyMuPDF not installed. Run: pip install PyMuPDF")

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages: List[str] = []
    page_images: List[bytes] = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Extract text
        text = page.get_text("text")
        pages.append(text)

        # Render page as PNG image (for Gemini Vision fallback)
        mat = fitz.Matrix(2.0, 2.0)   # 2x zoom = better OCR quality
        clip = page.get_pixmap(matrix=mat)
        page_images.append(clip.tobytes("png"))

    doc.close()

    meta: Dict[str, Any] = {
        "page_count":        len(pages),
        "total_text_chars":  sum(len(p) for p in pages),
        "has_text_layer":    any(len(p.strip()) > 50 for p in pages),
    }
    return pages, page_images, meta


async def _load_image(file_bytes: bytes):
    """Loads an image invoice directly (no text extraction at this stage)."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow not installed. Run: pip install Pillow")

    img = Image.open(io.BytesIO(file_bytes))
    width, height = img.size

    meta: Dict[str, Any] = {
        "page_count":        1,
        "total_text_chars":  0,        # No text extracted yet
        "has_text_layer":    False,
        "image_size":        f"{width}x{height}",
    }

    # Return image bytes as a single "page"
    return [""], [file_bytes], meta
