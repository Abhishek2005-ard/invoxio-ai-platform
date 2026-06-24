"""
Invoice Extraction Sub-Agent — LangGraph Pipeline

Flow:
    START
      │
      ▼
  ┌──────────────┐
  │ load_document│  Detect type, extract text/images
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  ocr_extract │  PyMuPDF text OR Gemini Vision
  └──────┬───────┘
         │
         ▼
  ┌───────────────┐
  │ parse_invoice │  Gemini: raw text → structured JSON  ◄──┐
  └──────┬────────┘                                         │ (retry)
         │                                                   │
         ▼                                                   │
  ┌─────────────────┐                                        │
  │ validate_output │  Pydantic check ── if invalid & retry ─┘
  └──────┬──────────┘
         │ if valid (or max retries)
         ▼
        END
"""

from langgraph.graph import StateGraph, START, END
from subagents.invoice_extraction.state import InvoiceExtractionState
from subagents.invoice_extraction.nodes.load_document  import load_document_node
from subagents.invoice_extraction.nodes.ocr_extract    import ocr_extract_node
from subagents.invoice_extraction.nodes.parse_invoice  import parse_invoice_node
from subagents.invoice_extraction.nodes.validate_output import validate_output_node, should_retry_or_end


def build_extraction_graph():
    """
    Builds and compiles the Invoice Extraction sub-agent graph.

    Returns:
        Compiled LangGraph ready for .ainvoke()
    """
    graph = StateGraph(InvoiceExtractionState)

    # ── Register nodes ────────────────────────────────────────────────────
    graph.add_node("load_document",   load_document_node)
    graph.add_node("ocr_extract",     ocr_extract_node)
    graph.add_node("parse_invoice",   parse_invoice_node)
    graph.add_node("validate_output", validate_output_node)

    # ── Linear edges ──────────────────────────────────────────────────────
    graph.add_edge(START,          "load_document")
    graph.add_edge("load_document", "ocr_extract")
    graph.add_edge("ocr_extract",   "parse_invoice")
    graph.add_edge("parse_invoice", "validate_output")

    # ── Conditional: retry or end ─────────────────────────────────────────
    graph.add_conditional_edges(
        "validate_output",
        should_retry_or_end,
        {
            "parse_invoice": "parse_invoice",   # Retry parse with guidance
            "end":           END,               # Accept result
        },
    )

    compiled = graph.compile()
    print("✅ Invoice Extraction Sub-Agent graph compiled")
    return compiled


# ── Singleton ─────────────────────────────────────────────────────────────────
extraction_graph = build_extraction_graph()
