"""
Validation & Normalization Agent
Validates extracted invoice fields for completeness and consistency,
then normalises formats (dates → ISO 8601, amounts → float, etc.).
"""

import re
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END


class ValidationState(TypedDict):
    raw_data: str       # JSON string of extracted invoice fields
    validated_data: str # normalised + validated JSON string
    errors: str         # validation errors found


def rule_based_validation(state: ValidationState) -> dict:
    """Quick rule-based checks before calling the LLM."""
    print("[Validation Agent] rule_based_validation")
    errors = []
    raw = state["raw_data"]

    # Check mandatory keywords
    for field in ["vendor", "date", "amount"]:
        if field.lower() not in raw.lower():
            errors.append(f"Missing required field: {field}")

    # Detect obviously malformed amounts (letters where digits expected)
    if re.search(r'"\s*amount\s*"\s*:\s*"[^0-9$€£\-\.,"]+', raw, re.IGNORECASE):
        errors.append("Amount field contains non-numeric characters.")

    return {"errors": "; ".join(errors) if errors else "none"}


async def llm_normalize(state: ValidationState, llm) -> dict:
    """Ask the LLM to normalise and fill gaps in the extracted data."""
    print("[Validation Agent] llm_normalize")
    prompt = (
        "You are a financial data validator. Given the raw extracted invoice JSON below, do the following:\n"
        "1. Normalise all dates to ISO 8601 (YYYY-MM-DD).\n"
        "2. Normalise all monetary amounts to a float (e.g. '$1,250.00' → 1250.00).\n"
        "3. Fill any obviously missing fields with null.\n"
        "4. Flag validation errors found (if any): " + state["errors"] + "\n\n"
        "Return ONLY the corrected JSON object.\n\n"
        f"Raw Data:\n{state['raw_data']}"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"validated_data": response.content}


def build_validation_graph(llm):
    async def _normalize(state):
        return await llm_normalize(state, llm)

    g = StateGraph(ValidationState)
    g.add_node("validate", rule_based_validation)
    g.add_node("normalize", _normalize)
    g.add_edge(START, "validate")
    g.add_edge("validate", "normalize")
    g.add_edge("normalize", END)
    return g.compile()


def make_validation_tool(llm, dummy: bool = False):
    graph = build_validation_graph(llm)

    @tool
    async def validation_normalization_agent(raw_invoice_json: str) -> str:
        """
        Validate and normalise raw extracted invoice JSON.
        Checks for missing fields, normalises dates to ISO 8601,
        and converts amounts to floats. Returns clean validated JSON.
        """
        print("\n--- [Validation & Normalization Agent triggered] ---")
        if dummy:
            return '{"vendor":"ACME Corp","date":"2026-06-01","amount":1250.00,"tax":112.50,"po_number":"PO-8821","status":"valid"}'
        result = await graph.ainvoke({
            "raw_data": raw_invoice_json,
            "validated_data": "",
            "errors": ""
        })
        return result["validated_data"]

    return validation_normalization_agent
