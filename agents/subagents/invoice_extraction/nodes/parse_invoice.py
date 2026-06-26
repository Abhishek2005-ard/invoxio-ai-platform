"""
Node 3 — parse_invoice

Responsibility:
  - Takes raw OCR text from ocr_extract
  - Sends it to Gemini with a structured extraction prompt
  - Gemini returns a clean JSON matching the InvoiceData schema
  - Supports retry on parse failure (max 2 attempts)

Pipeline: load_document → ocr_extract → [parse_invoice] → validate_output
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.gemini import llm_think
from subagents.invoice_extraction.state import InvoiceExtractionState

#  The most important prompt in the pipeline.
#  Instructs Gemini to extract every invoice field into a precise JSON schema.
PARSE_SYSTEM_PROMPT = """You are an expert invoice data extraction AI.

Extract ALL information from the provided invoice text and return it as a single, valid JSON object.

REQUIRED JSON Schema:
{
  "invoice_number":   "string — invoice/bill number (e.g. 'INV-2024-001')",
  "purchase_order":   "string or null",
  "vendor": {
    "name":    "string — company issuing the invoice",
    "address": "string or null",
    "email":   "string or null",
    "phone":   "string or null",
    "tax_id":  "string — GST/VAT/EIN number or null"
  },
  "client": {
    "name":    "string — company being billed",
    "address": "string or null",
    "email":   "string or null"
  },
  "invoice_date":    "ISO date string YYYY-MM-DD or null",
  "due_date":        "ISO date string YYYY-MM-DD or null",
  "payment_terms":   "string e.g. 'Net 30' or null",
  "line_items": [
    {
      "description": "string",
      "quantity":    number or null,
      "unit_price":  number or null,
      "total":       number or null
    }
  ],
  "subtotal":        number (without tax),
  "tax_rate":        number (percentage, e.g. 18 for 18% GST),
  "tax_amount":      number,
  "discount":        number or 0,
  "total_amount":    number (final amount due),
  "currency":        "3-letter code: USD, INR, EUR, GBP, etc.",
  "payment_method":  "string or null",
  "bank_account":    "string or null",
  "bank_ifsc":       "string or null",
  "notes":           "string or null",
  "status":          "unpaid"
}

RULES:
- Output ONLY the JSON object — no markdown, no explanation, no code blocks
- All monetary values must be numbers (not strings)
- Dates must be in YYYY-MM-DD format
- If a field is not present in the invoice, use null (not empty string)
- For line_items, include EVERY line on the invoice
- For currency, infer from context (₹ = INR, $ = USD, € = EUR)
- Never hallucinate data — only extract what is explicitly visible
"""


async def parse_invoice_node(state: InvoiceExtractionState) -> dict:
    """
    Sends raw OCR text to Gemini and extracts structured invoice JSON.

    Reads:  raw_text, ocr_method, parse_attempts
    Writes: parsed_json, parse_attempts
    """
    raw_text       = state.get("raw_text", "")
    parse_attempts = state.get("parse_attempts", 0)
    ocr_method     = state.get("ocr_method", "unknown")

    print(f"\n[parse_invoice] Attempt {parse_attempts + 1} — Parsing {len(raw_text)} chars of OCR text...")

    if not raw_text.strip():
        return {
            "parsed_json":    {},
            "parse_attempts": parse_attempts + 1,
            "error":          "No text to parse — OCR returned empty content",
        }

    # Build the prompt
    # On retry, add extra guidance to fix the previous failure
    retry_note = ""
    if parse_attempts > 0:
        retry_note = (
            "\n\nNOTE: Previous attempt failed JSON parsing. "
            "Ensure your output is pure JSON with no extra text."
        )

    response = await llm_think.ainvoke([
        SystemMessage(content=PARSE_SYSTEM_PROMPT + retry_note),
        HumanMessage(content=(
            f"OCR Method Used: {ocr_method}\n\n"
            f"=== INVOICE RAW TEXT ===\n{raw_text[:8000]}\n=== END ==="
        )),
    ])

    raw_output = response.content if isinstance(response.content, str) else str(response.content)

    # Parse the JSON
    try:
        # Strip any accidental markdown code fences
        cleaned = (
            raw_output.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        parsed = json.loads(cleaned)
        print(f"[parse_invoice] Successfully parsed JSON — "
              f"vendor: {parsed.get('vendor', {}).get('name', '?')}, "
              f"total: {parsed.get('total_amount', '?')}")
        return {
            "parsed_json":    parsed,
            "parse_attempts": parse_attempts + 1,
        }

    except json.JSONDecodeError as e:
        print(f"Error: [parse_invoice] JSON parse error: {e}")
        return {
            "parsed_json":    {"_raw_output": raw_output},
            "parse_attempts": parse_attempts + 1,
            "error":          f"JSON parse failed: {e}",
        }
