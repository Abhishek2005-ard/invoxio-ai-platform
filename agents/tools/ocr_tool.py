"""
OCR Tool — Tesseract + AWS Textract + Gemini Vision

LangChain StructuredTool that accepts a file path or base64-encoded image
and extracts structured text using the best available OCR strategy:
  Strategy 1: PyMuPDF       — fast, for PDFs with text layer
  Strategy 2: Tesseract     — open-source OCR, good for clean images
  Strategy 3: AWS Textract  — cloud OCR, best for complex invoices
  Strategy 4: Gemini Vision — fallback AI-powered OCR
"""
import base64
import os
from typing import Any, Dict, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class OCRInput(BaseModel):
    file_path:   Optional[str] = Field(default=None, description="Absolute path to PDF or image file")
    base64_data: Optional[str] = Field(default=None, description="Base64-encoded file content")
    file_type:   str           = Field(default="pdf", description="'pdf' or 'image'")
    engine:      str           = Field(default="auto", description="'auto'|'tesseract'|'textract'|'gemini_vision'|'pymupdf'")
    tenant_id:   str           = Field(default="", description="Tenant scope")


@tool(args_schema=OCRInput)
async def ocr_tool(
    file_path: Optional[str],
    base64_data: Optional[str],
    file_type: str,
    engine: str,
    tenant_id: str,
) -> Dict[str, Any]:
    """
    Extract text from a PDF or image using the best available OCR engine.
    Supports Tesseract (local), AWS Textract (cloud), Gemini Vision (AI), and PyMuPDF.
    """
    print(f"  📸 [ocr_tool] engine={engine} | type={file_type} | tenant={tenant_id}")

    # ── Load file bytes ───────────────────────────────────────────────────
    file_bytes = None
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    elif base64_data:
        file_bytes = base64.b64decode(base64_data)

    if not file_bytes:
        return {"status": "error", "error": "No file provided — supply file_path or base64_data"}

    # ── Auto-select best engine ───────────────────────────────────────────
    if engine == "auto":
        engine = _select_engine(file_type, len(file_bytes))

    print(f"  🔧 [ocr_tool] Selected engine: {engine}")

    # ── Execute OCR ───────────────────────────────────────────────────────
    if engine == "pymupdf":
        return await _pymupdf_ocr(file_bytes)
    elif engine == "tesseract":
        return await _tesseract_ocr(file_bytes)
    elif engine == "textract":
        return await _textract_ocr(file_bytes)
    else:  # gemini_vision
        return await _gemini_vision_ocr(file_bytes, file_type)


def _select_engine(file_type: str, file_size: int) -> str:
    """Auto-selects the best OCR engine based on file type and size."""
    if file_type == "pdf":
        return "pymupdf"      # Try text layer first — fastest
    if file_size > 5 * 1024 * 1024:
        return "textract"     # Large image → AWS Textract (handles complex layouts)
    return "tesseract"        # Default for normal images


async def _pymupdf_ocr(file_bytes: bytes) -> Dict[str, Any]:
    """Extract text from PDF using PyMuPDF (fitz)."""
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = [page.get_text("text") for page in doc]
        doc.close()
        full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages_text).strip()
        char_count = len(full_text)
        # If text layer is sparse, signal caller to try vision OCR
        confidence = 0.90 if char_count > 200 else 0.30
        return {"status":"success","engine":"pymupdf","text":full_text,
                "char_count":char_count,"confidence":confidence,"pages":len(pages_text)}
    except Exception as e:
        return {"status":"error","engine":"pymupdf","error":str(e)}


async def _tesseract_ocr(file_bytes: bytes) -> Dict[str, Any]:
    """Extract text from image using Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(file_bytes))
        # Run Tesseract with invoice-optimized config
        config = "--oem 3 --psm 6"   # LSTM engine + uniform block of text
        text = pytesseract.image_to_string(img, config=config)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=config)
        confidences = [int(c) for c in data["conf"] if str(c).isdigit() and int(c) >= 0]
        avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.5
        return {"status":"success","engine":"tesseract","text":text.strip(),
                "char_count":len(text),"confidence":round(avg_confidence, 3)}
    except Exception as e:
        return {"status":"error","engine":"tesseract","error":str(e)}


async def _textract_ocr(file_bytes: bytes) -> Dict[str, Any]:
    """Extract text using AWS Textract (best for structured invoices)."""
    try:
        import boto3
        client = boto3.client("textract", region_name=os.getenv("AWS_REGION","us-east-1"))
        response = client.detect_document_text(Document={"Bytes": file_bytes})
        blocks   = response.get("Blocks", [])
        lines    = [b["Text"] for b in blocks if b["BlockType"] == "LINE"]
        text     = "\n".join(lines)
        # Textract confidence scores
        confidences = [b.get("Confidence",0)/100 for b in blocks if b["BlockType"] == "LINE"]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.85
        return {"status":"success","engine":"textract","text":text,
                "char_count":len(text),"confidence":round(avg_conf,3),"line_count":len(lines)}
    except Exception as e:
        return {"status":"error","engine":"textract","error":str(e),
                "fallback_note":"AWS credentials may not be configured — use gemini_vision instead"}


async def _gemini_vision_ocr(file_bytes: bytes, file_type: str) -> Dict[str, Any]:
    """AI-powered OCR using Google Gemini Vision."""
    try:
        import google.generativeai as genai
        from config.settings import settings
        genai.configure(api_key=settings.google_gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        b64   = base64.b64encode(file_bytes).decode()
        mime  = "application/pdf" if file_type == "pdf" else "image/png"
        resp  = model.generate_content([
            {"mime_type": mime, "data": b64},
            "Extract ALL text from this document exactly as it appears. Preserve numbers, dates, and amounts.",
        ])
        text = resp.text.strip() if resp.text else ""
        return {"status":"success","engine":"gemini_vision","text":text,
                "char_count":len(text),"confidence":0.88}
    except Exception as e:
        return {"status":"error","engine":"gemini_vision","error":str(e)}
