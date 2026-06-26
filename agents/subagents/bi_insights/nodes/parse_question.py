"""
Node 1/5 — parse_question
NL question → structured intent + time period + dimensions
Pipeline: [parse_question] → build_query → execute_query → generate_chart_data → compose_response
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.gemini import llm_think
from subagents.bi_insights.state import BIInsightsState
from datetime import datetime, timezone

PARSE_PROMPT = """You are a BI query intent classifier for an invoice management system.

Analyze the user's question and extract:
1. query_intent: one of ["revenue_trend","cash_flow","top_clients","top_vendors","expense_breakdown","invoice_status","custom"]
2. time_period: {"from":"YYYY-MM-DD","to":"YYYY-MM-DD","label":"Human label"}
   - If no date mentioned, default to current month
3. dimensions: list of grouping fields from ["client","vendor","category","month","quarter","status"]
4. metrics: list from ["total_amount","count","avg_amount","paid_amount","unpaid_amount"]
5. chart_type: best visualization ["bar","line","pie","area","table"]

Today is: {today}

Output ONLY valid JSON:
{{"query_intent":"...","time_period":{{...}},"dimensions":[...],"metrics":[...],"chart_type":"..."}}
"""

async def parse_question_node(state: BIInsightsState) -> dict:
    print(f"\n[parse_question] Parsing: '{state['question']}'")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    response = await llm_think.ainvoke([
        SystemMessage(content=PARSE_PROMPT.format(today=today)),
        HumanMessage(content=state["question"]),
    ])
    raw = response.content if isinstance(response.content, str) else "{}"
    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
    except Exception:
        data = {"query_intent":"revenue_trend","time_period":{"from":"2024-01-01","to":"2024-12-31","label":"2024"},"dimensions":["month"],"metrics":["total_amount"],"chart_type":"line"}
    print(f"  Intent: {data.get('query_intent')} | Period: {data.get('time_period',{}).get('label')} | Chart: {data.get('chart_type')}")
    return {
        "query_intent":  data.get("query_intent","revenue_trend"),
        "time_period":   data.get("time_period",{}),
        "dimensions":    data.get("dimensions",[]),
        "metrics":       data.get("metrics",["total_amount"]),
        "chart_type":    data.get("chart_type","bar"),
    }
