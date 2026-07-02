"""
BI Insights Agent
Responsible for: answering business intelligence queries against
the financial database context (revenue, expenses, top clients).
"""

import json
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

# Simulated DB context — replace with real DB calls as needed
_DB_CONTEXT = {
    "Q1_revenue": "$350,000",
    "Q2_revenue": "$420,000",
    "monthly_expenses": {
        "marketing": "$12,000/mo",
        "salaries": "$85,000/mo",
        "cloud_servers": "$4,500/mo"
    },
    "top_paying_clients": [
        "Globex Corp ($120k)",
        "Initech ($85k)",
        "ACME Corp ($60k)"
    ]
}


def make_bi_tool(llm, dummy: bool = False):
    """Return a @tool-decorated function for BI insights."""

    @tool
    async def bi_insights_subagent(query: str) -> str:
        """Answer revenue trends, expense breakdowns, or client statistics from the database."""
        print("\n--- [BI Insights Agent triggered] ---")
        if dummy:
            return f"[Mock] BI Insight for: '{query}'"

        prompt = (
            "You are a financial analyst. "
            "Answer the user's query using ONLY the database context below.\n\n"
            f"Database Context:\n{json.dumps(_DB_CONTEXT, indent=2)}\n\n"
            f"User Query: {query}"
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    return bi_insights_subagent
