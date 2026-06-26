"""
Node 2 — ocr_extract

Responsibility:
  - Choose the best OCR strategy based on the document:
      Strategy A (PDF with text layer) → use PyMuPDF text directly
      Strategy B (PDF image-only / scanned) → Gemini Vision on each page image
      Strategy C (Image file) → Gemini Vision directly on the image
  - Concatenate all page text into raw_text
  - Set ocr_method and ocr_confidence

Pipeline: load_document → [ocr_extract] → parse_invoice → validate_output
"""

import base64
from subagents.invoice_extraction.state import InvoiceExtractionState
from config.settings import settings

# OCR quality threshold:
# If PyMuPDF extracts fewer than this many chars per page, use Gemini Vision
MIN_TEXT_CHARS_PER_PAGE = 100


async def ocr_extract_node(state: InvoiceExtractionState) -> dict:
    """
    Extracts raw text from the document using the best available strategy.

    Reads:  file_type, pages, page_images, doc_meta
    Writes: raw_text, ocr_method, ocr_confidence
    """
    file_type = state.get("file_type", "pdf")
    pages     = state.get("pages", [])
    doc_meta  = state.get("doc_meta", {})

    print(f"\n[ocr_extract] Selecting OCR strategy...")

    # Strategy A: PDF with a good text layer
    if file_type == "pdf" and doc_meta.get("has_text_layer", False):
        avg_chars = doc_meta.get("total_text_chars", 0) / max(len(pages), 1)
        if avg_chars >= MIN_TEXT_CHARS_PER_PAGE:
            raw_text = "\n\n--- PAGE BREAK ---\n\n".join(pages).strip()
            print(f"[ocr_extract] Strategy A: PyMuPDF text ({len(raw_text)} chars)")
            return {
                "raw_text":         raw_text,
                "ocr_method":       "pymupdf",
                "ocr_confidence":   0.90,
            }

    # Strategy B/C: Gemini Vision
    print(f"[ocr_extract] Strategy B/C: Gemini Vision OCR")
    raw_text, confidence = await _gemini_vision_ocr(
        page_images=state.get("page_images", []),
        file_type=file_type,
    )

    method = "gemini_vision" if file_type == "image" else "gemini_vision_pdf"
    print(f"[ocr_extract] Gemini Vision extracted {len(raw_text)} chars")

    return {
        "raw_text":       raw_text,
        "ocr_method":     method,
        "ocr_confidence": confidence,
    }


async def _gemini_vision_ocr(page_images: list, file_type: str) -> tuple[str, float]:
    """
    Uses Google Gemini Vision to extract text from page images.

    Sends each page image with a prompt asking Gemini to read the invoice text.
    Returns concatenated text + estimated confidence.
    """
    import google.generativeai as genai
    genai.configure(api_key=settings.google_gemini_api_key)

    model = genai.GenerativeModel(settings.gemini_model)

    OCR_PROMPT = (
        "You are an OCR engine. Read ALL text visible in this invoice image exactly as it appears. "
        "Preserve the layout: include all numbers, dates, addresses, line items, totals, and labels. "
        "Output only the raw text — no commentary, no markdown, no JSON yet. "
        "If text is unclear, make your best guess and mark it with [?]."
    )

    all_pages_text = []

    for i, img_bytes in enumerate(page_images):
        if not img_bytes:
            continue

        # Convert to base64 for Gemini
        b64_image = base64.b64encode(img_bytes).decode("utf-8")

        # Detect MIME type from bytes header
        mime_type = _detect_mime(img_bytes)

        try:
            response = model.generate_content([
                {"mime_type": mime_type, "data": b64_image},
                OCR_PROMPT,
            ])
            page_text = response.text.strip() if response.text else ""
            all_pages_text.append(f"--- PAGE {i+1} ---\n{page_text}")
            print(f"  Page {i+1}: {len(page_text)} chars extracted")
        except Exception as e:
            print(f"  Warning: Page {i+1} OCR failed: {e}")
            all_pages_text.append(f"--- PAGE {i+1} ---\n[OCR FAILED: {e}]")

    raw_text    = "\n\n".join(all_pages_text)
    confidence  = 0.85 if all_pages_text else 0.0

    return raw_text, confidence


def _detect_mime(img_bytes: bytes) -> str:
    """Detect image MIME type from magic bytes."""
    if img_bytes[:4] == b"\x89PNG":
        return "image/png"
    if img_bytes[:2] in (b"\xff\xd8", b"\xff\xe0", b"\xff\xe1"):
        return "image/jpeg"
    if img_bytes[:4] == b"RIFF" and img_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"  # Default fallback
