"""
Categorization Agent
Classifies each invoice into a spending category
(e.g. Marketing, SaaS/Cloud, Payroll, Legal, Office Supplies, Travel)
and enriches it with a confidence score and sub-category.
"""

from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END

CATEGORIES = [
    "Marketing & Advertising",
    "SaaS / Cloud Infrastructure",
    "Payroll & Contractor Fees",
    "Legal & Compliance",
    "Office Supplies & Equipment",
    "Travel & Entertainment",
    "Professional Services",
    "Utilities",
    "Other / Uncategorized",
]


class CategorizationState(TypedDict):
    invoice_json: str
    category: str


async def classify_invoice(state: CategorizationState, llm) -> dict:
    """Use the LLM to assign the most appropriate spending category."""
    print("[Categorization Agent] classify_invoice")
    prompt = (
        "You are a financial categorization engine. "
        "Given the invoice JSON below, assign the single most appropriate category "
        f"from this list:\n{chr(10).join(f'- {c}' for c in CATEGORIES)}\n\n"
        "Also provide:\n"
        "- sub_category: a short 2-4 word description\n"
        "- confidence: a float 0.0-1.0\n"
        "- reason: one sentence\n\n"
        "Return ONLY a JSON object with keys: category, sub_category, confidence, reason.\n\n"
        f"Invoice:\n{state['invoice_json']}"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"category": response.content}


def build_categorization_graph(llm):
    async def _classify(state):
        return await classify_invoice(state, llm)

    g = StateGraph(CategorizationState)
    g.add_node("classify", _classify)
    g.add_edge(START, "classify")
    g.add_edge("classify", END)
    return g.compile()


def make_categorization_tool(llm, dummy: bool = False):
    graph = build_categorization_graph(llm)

    @tool
    async def categorization_agent(invoice_json: str) -> str:
        """
        Classify an invoice into a spending category.
        Returns category, sub-category, confidence score, and reasoning.
        Useful for expense tracking and budget allocation analysis.
        """
        print("\n--- [Categorization Agent triggered] ---")
        if dummy:
            return '{"category":"SaaS / Cloud Infrastructure","sub_category":"Cloud Hosting","confidence":0.95,"reason":"Vendor name and line items indicate cloud server costs."}'
        result = await graph.ainvoke({"invoice_json": invoice_json, "category": ""})
        return result["category"]

    return categorization_agent
