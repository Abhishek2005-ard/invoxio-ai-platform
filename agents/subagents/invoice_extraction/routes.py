"""
Invoice Extraction Routes — FastAPI endpoints

POST /api/invoice/extract    → Upload PDF/image → returns structured JSON
GET  /api/invoice/schema     → Returns the expected InvoiceData JSON schema
"""

import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from subagents.invoice_extraction.graph import extraction_graph
from subagents.invoice_extraction.models.invoice_schema import InvoiceData

router = APIRouter()

# Max upload size: 20 MB
MAX_FILE_SIZE = 20 * 1024 * 1024

SUPPORTED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg":      ".jpg",
    "image/png":       ".png",
    "image/webp":      ".webp",
    "image/tiff":      ".tiff",
}


@router.post("/extract")
async def extract_invoice(
    file:      UploadFile = File(..., description="Invoice PDF or image file"),
    tenant_id: str        = Form(default="demo-tenant"),
):
    """
    Upload an invoice PDF or image.
    Returns the fully extracted, structured invoice data as JSON.

    Pipeline: PDF/Image → load_document → ocr_extract → parse_invoice → validate_output → JSON
    """
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_TYPES and not file.filename.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {content_type}. Supported: PDF, JPG, PNG, WEBP",
        )

    # Read file bytes
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(file_bytes):,} bytes). Max: {MAX_FILE_SIZE:,} bytes",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    print(f"\n[/extract] Received: {file.filename} ({len(file_bytes):,} bytes) for tenant: {tenant_id}")

    # Build initial state
    initial_state = {
        "file_bytes":         file_bytes,
        "file_name":          file.filename or "invoice.pdf",
        "file_type":          "",           # Detected in load_document
        "tenant_id":          tenant_id,
        "pages":              [],
        "page_images":        [],
        "doc_meta":           {},
        "raw_text":           "",
        "ocr_method":         "",
        "ocr_confidence":     0.0,
        "parsed_json":        {},
        "parse_attempts":     0,
        "validated_invoice":  None,
        "validation_errors":  [],
        "is_valid":           False,
        "error":              None,
    }

    # Run the extraction pipeline
    try:
        result = await extraction_graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    # Handle errors
    if result.get("error") and not result.get("validated_invoice"):
        raise HTTPException(status_code=422, detail=result["error"])

    invoice_data = result.get("validated_invoice") or result.get("parsed_json", {})

    return JSONResponse(content={
        "success":           True,
        "file_name":         file.filename,
        "ocr_method":        result.get("ocr_method", "unknown"),
        "ocr_confidence":    result.get("ocr_confidence", 0.0),
        "is_valid":          result.get("is_valid", False),
        "validation_errors": result.get("validation_errors", []),
        "invoice":           invoice_data,
    })


@router.get("/schema")
async def get_invoice_schema():
    """Returns the JSON Schema that the extraction pipeline produces."""
    return InvoiceData.model_json_schema()
