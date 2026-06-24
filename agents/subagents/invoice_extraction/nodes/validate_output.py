"""
Node 4 — validate_output

Responsibility:
  - Validate parsed_json against the Pydantic InvoiceData schema
  - Collect any missing/invalid fields as warnings (not errors)
  - Enrich the output with extraction metadata
  - Decide: retry parse (if critical fields missing) or accept as-is

Pipeline: load_document → ocr_extract → parse_invoice → [validate_output]
"""

from subagents.invoice_extraction.state import InvoiceExtractionState
from subagents.invoice_extraction.models.invoice_schema import InvoiceData
from pydantic import ValidationError

# Critical fields that MUST be present to accept the result
CRITICAL_FIELDS = ["invoice_number", "total_amount", "vendor"]
MAX_PARSE_ATTEMPTS = 2


async def validate_output_node(state: InvoiceExtractionState) -> dict:
    """
    Validates the parsed JSON against InvoiceData schema.

    Reads:  parsed_json, ocr_method, ocr_confidence, raw_text, parse_attempts
    Writes: validated_invoice, validation_errors, is_valid
    """
    parsed     = state.get("parsed_json", {})
    attempts   = state.get("parse_attempts", 0)
    raw_text   = state.get("raw_text", "")

    print(f"\n✔️  [validate_output] Validating parsed invoice...")

    # ── Enrich with extraction metadata ──────────────────────────────────
    parsed["ocr_method"]             = state.get("ocr_method", "unknown")
    parsed["extraction_confidence"]  = state.get("ocr_confidence", 0.0)
    parsed["raw_text_preview"]       = raw_text[:200] if raw_text else ""

    # ── Pydantic validation ───────────────────────────────────────────────
    errors = []
    try:
        invoice = InvoiceData(**parsed)
        validated_dict = invoice.model_dump()
        print(f"✅ [validate_output] Valid — "
              f"Invoice #{validated_dict.get('invoice_number')} | "
              f"Total: {validated_dict.get('currency', '')} {validated_dict.get('total_amount', 0)}")
        return {
            "validated_invoice": validated_dict,
            "validation_errors": [],
            "is_valid":          True,
        }

    except ValidationError as e:
        for err in e.errors():
            field = " → ".join(str(loc) for loc in err["loc"])
            errors.append(f"{field}: {err['msg']}")
        print(f"⚠️  [validate_output] {len(errors)} validation error(s): {errors[:3]}")

    # ── Check if critical fields are missing ──────────────────────────────
    missing_critical = [
        f for f in CRITICAL_FIELDS
        if not parsed.get(f) or (isinstance(parsed.get(f), dict) and not parsed.get(f, {}).get("name"))
    ]

    if missing_critical and attempts < MAX_PARSE_ATTEMPTS:
        print(f"🔄 [validate_output] Missing critical fields {missing_critical} — will retry parse")
        return {
            "validated_invoice": None,
            "validation_errors": errors + [f"Missing: {', '.join(missing_critical)}"],
            "is_valid":          False,
        }

    # ── Accept with warnings if non-critical issues only ─────────────────
    print(f"⚠️  [validate_output] Accepting with {len(errors)} warning(s)")
    return {
        "validated_invoice": parsed,     # Use raw parsed dict as fallback
        "validation_errors": errors,
        "is_valid":          True,        # Mark valid to stop the loop
    }


def should_retry_or_end(state: InvoiceExtractionState) -> str:
    """
    Conditional edge: retry parse_invoice OR accept result and END.
    """
    if not state.get("is_valid", False) and state.get("parse_attempts", 0) < MAX_PARSE_ATTEMPTS:
        print("🔄 [router] Retrying parse_invoice...")
        return "parse_invoice"
    print("🏁 [router] Validation done → END")
    return "end"
