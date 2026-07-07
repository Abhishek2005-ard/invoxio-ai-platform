"""
Invoxio — Invoice Processing Pipeline  (pipeline.py)

Demonstrates the three core LangGraph advantages:

  1. PARALLEL BRANCHES — after extraction, validation + categorization +
     anomaly-detection run concurrently, then merge.

  2. CYCLIC RETRY LOOP — if extraction confidence is low, the graph loops
     back to the extraction node (up to MAX_RETRIES).

  3. HUMAN-IN-THE-LOOP — invoices above HIGH_VALUE_THRESHOLD are
     interrupted and wait for an external human-approval signal before
     the pipeline finalises.

Public surface:
  build_invoice_pipeline(llm) -> CompiledGraph
  InvoiceState                -> TypedDict used as graph state

Run the pipeline:
  result = await pipeline.ainvoke({"raw_text": "<invoice text>", ...})
"""

import asyncio
import json
from typing import Annotated, TypedDict, Optional

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver   # enables HITL interrupts

HIGH_VALUE_THRESHOLD = 10_000   # USD — invoices above this need approval
MAX_RETRIES          = 3        # max extraction retry cycles


# ══════════════════════════════════════════════════════════════════════════════
# State
# ══════════════════════════════════════════════════════════════════════════════

class InvoiceState(TypedDict):
    # Input
    raw_text:          str
    file_data:         Optional[str]
    mime_type:         Optional[str]
    file_name:         Optional[str]

    # Extraction (node 1)
    extracted_json:    str
    confidence:        float          # 0.0 – 1.0, set by extraction node
    retry_count:       int

    # Parallel branch outputs
    validated_json:    str
    category:          str
    anomaly_report:    str

    # Approval
    amount:            float
    approval_status:   str            # "pending" | "approved" | "rejected"

    # Final
    final_report:      str


# ══════════════════════════════════════════════════════════════════════════════
# Node helpers
# ══════════════════════════════════════════════════════════════════════════════

def _get_text_content(content) -> str:
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    return str(content)


async def _llm_call(llm, prompt: str) -> str:
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return _get_text_content(resp.content)


# ── Node 1: Extraction (loops back if confidence is low) ──────────────────

async def extraction_node(state: InvoiceState, llm) -> dict:
    attempt = state.get("retry_count", 0) + 1
    print(f"[Pipeline] extraction_node  attempt={attempt}")

    prompt = (
        "Extract the following fields from the invoice document and return a JSON object:\n"
        "vendor, invoice_id, date (ISO 8601), amount (float), tax (float), "
        "po_number, line_items (list), payment_due_date, confidence (float 0-1 "
        "reflecting how complete and unambiguous the extraction was).\n\n"
    )

    file_data = state.get("file_data")
    mime_type = state.get("mime_type")

    if file_data and mime_type:
        print(f"[Pipeline] Using multimodal extraction for file: {state.get('file_name', 'document')}")
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{file_data}"}
            }
        ]
        resp = await llm.ainvoke([HumanMessage(content=content)])
        raw = _get_text_content(resp.content)
    else:
        print("[Pipeline] Using text-based extraction")
        full_prompt = prompt + f"Invoice text (attempt {attempt}):\n{state['raw_text']}"
        resp = await llm.ainvoke([HumanMessage(content=full_prompt)])
        raw = _get_text_content(resp.content)

    # Parse confidence from response
    try:
        # Strip code blocks or "json" header if present
        clean_raw = raw.strip("` \n")
        if clean_raw.lower().startswith("json"):
            clean_raw = clean_raw[4:].strip()
        
        data = json.loads(clean_raw)
        confidence = float(data.get("confidence", 0.5))
        amount     = float(str(data.get("amount", 0)).replace(",", "").replace("$", "") or 0)
    except Exception:
        confidence = 0.3
        amount     = 0.0

    return {
        "extracted_json": raw,
        "confidence":     confidence,
        "amount":         amount,
        "retry_count":    attempt,
    }


# ── Node 2a: Validation  ──────────────────────────────────────────────────

async def validation_node(state: InvoiceState, llm) -> dict:
    print("[Pipeline] validation_node  (parallel branch)")
    prompt = (
        "Validate and normalise this extracted invoice JSON.\n"
        "- Dates → ISO 8601  |  amounts → float  |  missing fields → null\n"
        "Return ONLY the corrected JSON.\n\n"
        f"{state['extracted_json']}"
    )
    return {"validated_json": await _llm_call(llm, prompt)}


# ── Node 2b: Categorization  ──────────────────────────────────────────────

async def categorization_node(state: InvoiceState, llm) -> dict:
    print("[Pipeline] categorization_node  (parallel branch)")
    categories = [
        "Marketing & Advertising", "SaaS / Cloud Infrastructure",
        "Payroll & Contractor Fees", "Legal & Compliance",
        "Office Supplies & Equipment", "Travel & Entertainment",
        "Professional Services", "Utilities", "Other",
    ]
    prompt = (
        f"Classify this invoice into one category from: {categories}.\n"
        "Return JSON: {category, sub_category, confidence, reason}.\n\n"
        f"{state['extracted_json']}"
    )
    return {"category": await _llm_call(llm, prompt)}


# ── Node 2c: Anomaly Detection  ───────────────────────────────────────────

async def anomaly_node(state: InvoiceState, llm) -> dict:
    print("[Pipeline] anomaly_node  (parallel branch)")
    prompt = (
        "Analyse this invoice for anomalies: duplicate risk, unusual amounts, "
        "missing PO number, suspicious vendor patterns.\n"
        "Return JSON: {anomalies_found (bool), details (list), risk_level}.\n\n"
        f"{state['extracted_json']}"
    )
    return {"anomaly_report": await _llm_call(llm, prompt)}


# ── Node 3: Merge — run 2a/2b/2c in true parallel ─────────────────────────

async def parallel_analysis(state: InvoiceState, llm) -> dict:
    """Fan-out: run validation, categorization, and anomaly detection concurrently."""
    print("[Pipeline] parallel_analysis  (fan-out → merge)")
    v, c, a = await asyncio.gather(
        validation_node(state, llm),
        categorization_node(state, llm),
        anomaly_node(state, llm),
    )
    return {**v, **c, **a}


# ── Node 4: Approval Gate (HITL interrupt happens BEFORE this node) ────────

async def approval_gate(state: InvoiceState) -> dict:
    """
    This node only runs after a human has resumed the graph.
    By the time it executes, approval_status has been set externally.
    """
    print(f"[Pipeline] approval_gate  status={state.get('approval_status','pending')}")
    return {}   # state already updated by human resume call


# ── Node 5: Finalise ──────────────────────────────────────────────────────

async def finalize_node(state: InvoiceState, llm) -> dict:
    print("[Pipeline] finalize_node")
    if state.get("approval_status") == "rejected":
        return {"final_report": "Invoice REJECTED by approver. No further processing."}

    prompt = (
        "Compile the following data into a concise executive summary:\n\n"
        f"Validated Invoice: {state.get('validated_json','')}\n"
        f"Category: {state.get('category','')}\n"
        f"Anomaly Report: {state.get('anomaly_report','')}\n"
        f"Approval Status: {state.get('approval_status','auto-approved')}\n\n"
        "Keep the summary under 150 words."
    )
    return {"final_report": await _llm_call(llm, prompt)}


# ══════════════════════════════════════════════════════════════════════════════
# Router edges
# ══════════════════════════════════════════════════════════════════════════════

def route_after_extraction(state: InvoiceState) -> str:
    """
    CYCLIC LOOP: if confidence < 0.7 and retries remain, loop back.
    Otherwise proceed to parallel analysis.
    """
    if state["confidence"] < 0.7 and state.get("retry_count", 0) < MAX_RETRIES:
        print(f"  → low confidence ({state['confidence']:.2f}), retrying extraction…")
        return "retry"
    print(f"  → confidence OK ({state['confidence']:.2f}), proceeding")
    return "ok"


def route_after_analysis(state: InvoiceState) -> str:
    """
    HUMAN-IN-THE-LOOP: high-value invoices pause here.
    Low-value invoices go straight to finalise.
    """
    if state.get("amount", 0) >= HIGH_VALUE_THRESHOLD:
        print(f"  → high-value invoice (${state['amount']:,.0f}), requesting approval…")
        return "needs_approval"
    return "auto_approve"


# ══════════════════════════════════════════════════════════════════════════════
# Graph builder
# ══════════════════════════════════════════════════════════════════════════════

def build_invoice_pipeline(llm):
    """
    Build and compile the full invoice processing LangGraph.

    Features:
      - MemorySaver checkpointer enables human-in-the-loop interrupts.
      - interrupt_before=["approval_gate"] pauses the graph for high-value
        invoices; resume by calling  graph.update_state(config, {"approval_status": "approved"})
        then  graph.invoke(None, config).
    """

    # Bind LLM to nodes
    async def _extract(state):  return await extraction_node(state, llm)
    async def _parallel(state): return await parallel_analysis(state, llm)
    async def _finalize(state): return await finalize_node(state, llm)

    g = StateGraph(InvoiceState)

    g.add_node("extraction",     _extract)
    g.add_node("parallel",       _parallel)
    g.add_node("approval_gate",  approval_gate)
    g.add_node("finalize",       _finalize)

    # ── Edges ──────────────────────────────────────────────────────────────
    g.add_edge(START, "extraction")

    # Cyclic retry loop
    g.add_conditional_edges(
        "extraction",
        route_after_extraction,
        {
            "retry": "extraction",   # ← cycles back
            "ok":    "parallel",
        }
    )

    # After parallel analysis: HITL branch or auto-approve
    g.add_conditional_edges(
        "parallel",
        route_after_analysis,
        {
            "needs_approval": "approval_gate",  # graph pauses here (interrupt_before)
            "auto_approve":   "finalize",
        }
    )

    g.add_edge("approval_gate", "finalize")
    g.add_edge("finalize", END)

    # MemorySaver lets the graph persist state across the interrupt/resume cycle
    memory = MemorySaver()

    return g.compile(
        checkpointer=memory,
        interrupt_before=["approval_gate"],  # HITL: graph suspends before this node
    )
