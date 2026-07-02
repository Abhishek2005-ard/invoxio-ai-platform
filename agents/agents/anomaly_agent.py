"""
Anomaly Detection Agent
Responsible for: scanning transaction lists and flagging duplicates,
price spikes, missing PO numbers, or other billing anomalies.
"""

import json
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END


# ── State ──────────────────────────────────────────────────────────────────

class AnomalyState(TypedDict):
    transactions_json: str
    anomalies: str


# ── Nodes ──────────────────────────────────────────────────────────────────

def validate_transactions(state: AnomalyState) -> dict:
    """Ensure the input is valid JSON before sending to the LLM."""
    print("[Anomaly Agent] validate_transactions")
    try:
        json.loads(state["transactions_json"])
    except json.JSONDecodeError:
        print("Warning: input is not valid JSON — passing as-is.")
    return {"transactions_json": state["transactions_json"]}


async def detect_with_llm(state: AnomalyState, llm) -> dict:
    """Ask the LLM to identify anomalies and return a JSON summary."""
    print("[Anomaly Agent] detect_with_llm")
    prompt = (
        "Analyze these transactions for anomalies such as: "
        "duplicate invoices (same vendor + same amount), "
        "sudden price spikes, or missing PO numbers.\n"
        "Return ONLY a clean JSON summary of findings.\n\n"
        f"Transactions:\n{state['transactions_json']}"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"anomalies": response.content}


# ── Graph factory ──────────────────────────────────────────────────────────

def build_anomaly_graph(llm):
    """Build and compile the anomaly detection sub-graph."""

    async def _detect(state):
        return await detect_with_llm(state, llm)

    g = StateGraph(AnomalyState)
    g.add_node("validate", validate_transactions)
    g.add_node("detect", _detect)
    g.add_edge(START, "validate")
    g.add_edge("validate", "detect")
    g.add_edge("detect", END)
    return g.compile()


# ── Tool wrapper ───────────────────────────────────────────────────────────

def make_anomaly_tool(llm, dummy: bool = False):
    """Return a @tool-decorated function bound to the provided LLM."""
    graph = build_anomaly_graph(llm)

    @tool
    async def anomaly_detection_tool(transactions_json: str) -> str:
        """Scan billing logs or transactions for duplicate invoices, price spikes, or fraud."""
        print("\n--- [Anomaly Agent triggered] ---")
        if dummy:
            return json.dumps({
                "anomalies_found": 1,
                "details": [{"type": "Duplicate Invoice", "amount": "$450"}]
            })
        result = await graph.ainvoke({
            "transactions_json": transactions_json,
            "anomalies": ""
        })
        return result["anomalies"]

    return anomaly_detection_tool
