"""
Invoice Extraction Agent
Responsible for: parsing raw invoice text and returning structured JSON data.
"""

import json
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END


# ── State ──────────────────────────────────────────────────────────────────

class InvoiceState(TypedDict):
    invoice_text: str
    structured_data: str


# ── Nodes ──────────────────────────────────────────────────────────────────

def clean_text(state: InvoiceState) -> dict:
    """Normalise whitespace before passing to the LLM."""
    print("  └─ [Invoice Agent] clean_text")
    cleaned = " ".join(state["invoice_text"].split())
    return {"invoice_text": cleaned}


async def extract_with_llm(state: InvoiceState, llm) -> dict:
    """Ask the LLM to return a JSON object with invoice fields."""
    print("  └─ [Invoice Agent] extract_with_llm")
    prompt = (
        "Extract these fields from the invoice text: "
        "Vendor Name, Invoice Date, Total Amount, Line Items.\n"
        "Return ONLY a clean JSON object.\n\n"
        f"Invoice Text:\n{state['invoice_text']}"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"structured_data": response.content}


# ── Graph factory ──────────────────────────────────────────────────────────

def build_invoice_graph(llm):
    """Build and compile the invoice extraction sub-graph."""

    async def _extract(state):
        return await extract_with_llm(state, llm)

    g = StateGraph(InvoiceState)
    g.add_node("clean", clean_text)
    g.add_node("extract", _extract)
    g.add_edge(START, "clean")
    g.add_edge("clean", "extract")
    g.add_edge("extract", END)
    return g.compile()


# ── Tool wrapper (for the orchestrator to call) ────────────────────────────

def make_invoice_tool(llm, dummy: bool = False):
    """Return a @tool-decorated function bound to the provided LLM."""
    graph = build_invoice_graph(llm)

    @tool
    async def invoice_extraction_tool(invoice_text: str) -> str:
        """Parse raw invoice text and return structured JSON (vendor, date, amount, items)."""
        print("\n--- [Invoice Agent triggered] ---")
        if dummy:
            return json.dumps({
                "vendor": "ACME Corp",
                "date": "2026-06-01",
                "total": "$1,250",
                "items": ["Consulting services"]
            })
        result = await graph.ainvoke({"invoice_text": invoice_text, "structured_data": ""})
        return result["structured_data"]

    return invoice_extraction_tool
