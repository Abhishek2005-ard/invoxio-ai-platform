"""
Invoice Extraction Sub-Agent — State

Shared TypedDict that flows through all 4 nodes:
    load_document → ocr_extract → parse_invoice → validate_output
"""

from typing import TypedDict, Optional, Dict, Any, List


class InvoiceExtractionState(TypedDict):
    """State for the Invoice Extraction pipeline."""

    # Input
    file_bytes: bytes          # Raw bytes of the uploaded PDF or image
    file_name: str             # Original filename (e.g. "invoice_march.pdf")
    file_type: str             # "pdf" | "image"
    tenant_id: str             # Tenant scope for storage

    # load_document node
    pages: List[str]           # Extracted text pages (from PyMuPDF for PDFs)
    page_images: List[bytes]   # Page images as bytes (for Gemini Vision)
    doc_meta: Dict[str, Any]   # File metadata (page count, size, etc.)

    # ocr_extract node
    raw_text: str              # Full concatenated OCR text
    ocr_method: str            # "pymupdf" | "gemini_vision" | "combined"
    ocr_confidence: float      # Estimated confidence 0.0–1.0

    # parse_invoice node
    parsed_json: Dict[str, Any]  # Gemini-structured invoice JSON
    parse_attempts: int          # Retry counter (max 2)

    # validate_output node
    validated_invoice: Optional[Dict[str, Any]]  # Final clean invoice dict
    validation_errors: List[str]                  # Any validation warnings
    is_valid: bool

    # Error Handling
    error: Optional[str]
