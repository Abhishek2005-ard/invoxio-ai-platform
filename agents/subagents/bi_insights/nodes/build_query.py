"""
Node 2/5 — build_query
Intent + params → MongoDB aggregation pipeline via Gemini
Pipeline: parse_question → [build_query] → execute_query → generate_chart_data → compose_response
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.gemini import llm_think
from subagents.bi_insights.state import BIInsightsState

BUILD_PROMPT = """You are a MongoDB aggregation pipeline expert.

Build a MongoDB aggregation pipeline for the Invoxio invoices collection.

Collection schema (invoices):
  tenant_id, invoice_number, vendor.name, client.name, total_amount,
  subtotal, tax_amount, status (paid/unpaid/overdue/draft),
  invoice_date (ISO string), due_date, currency, line_items[]

Build the pipeline to answer the query intent, filtered to the given tenant_id and date range.
Always start with: {{"$match": {{"tenant_id": "<TENANT_ID>", "invoice_date": {{"$gte":"FROM","$lte":"TO"}}}}}}

Output ONLY a valid JSON array of MongoDB pipeline stages.
"""

# Pre-built pipelines for common intents (fast, no LLM needed)
PRESET_PIPELINES = {
    "revenue_trend": [
        {"$match": {"tenant_id": "__TENANT__", "invoice_date": {"$gte": "__FROM__", "$lte": "__TO__"}}},
        {"$group": {"_id": {"$substr": ["$invoice_date", 0, 7]}, "total_revenue": {"$sum": "$total_amount"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$project": {"month": "$_id", "total_revenue": 1, "count": 1, "_id": 0}},
    ],
    "top_clients": [
        {"$match": {"tenant_id": "__TENANT__", "status": "paid"}},
        {"$group": {"_id": "$client.name", "total_revenue": {"$sum": "$total_amount"}, "invoice_count": {"$sum": 1}}},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 10},
        {"$project": {"client": "$_id", "total_revenue": 1, "invoice_count": 1, "_id": 0}},
    ],
    "invoice_status": [
        {"$match": {"tenant_id": "__TENANT__"}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}, "total_amount": {"$sum": "$total_amount"}}},
        {"$project": {"status": "$_id", "count": 1, "total_amount": 1, "_id": 0}},
    ],
    "cash_flow": [
        {"$match": {"tenant_id": "__TENANT__", "invoice_date": {"$gte": "__FROM__", "$lte": "__TO__"}}},
        {"$group": {"_id": {"$substr": ["$invoice_date", 0, 7]},
            "paid": {"$sum": {"$cond": [{"$eq": ["$status", "paid"]}, "$total_amount", 0]}},
            "unpaid": {"$sum": {"$cond": [{"$ne": ["$status", "paid"]}, "$total_amount", 0]}}}},
        {"$sort": {"_id": 1}},
        {"$project": {"month": "$_id", "paid": 1, "unpaid": 1, "_id": 0}},
    ],
}

async def build_query_node(state: BIInsightsState) -> dict:
    intent    = state.get("query_intent", "revenue_trend")
    tenant_id = state["tenant_id"]
    period    = state.get("time_period", {})
    date_from = period.get("from", "2024-01-01")
    date_to   = period.get("to", "2024-12-31")

    print(f"\n[build_query] Building query for intent: '{intent}'")

    # Use preset pipeline if available
    if intent in PRESET_PIPELINES:
        pipeline = json.loads(
            json.dumps(PRESET_PIPELINES[intent])
            .replace("__TENANT__", tenant_id)
            .replace("__FROM__", date_from)
            .replace("__TO__", date_to)
        )
        desc = f"Preset pipeline for {intent} from {date_from} to {date_to}"
        print(f"  Using preset pipeline ({len(pipeline)} stages)")
    else:
        # Fallback to Gemini for custom queries
        response = await llm_think.ainvoke([
            SystemMessage(content=BUILD_PROMPT),
            HumanMessage(content=f"tenant_id={tenant_id}\nfrom={date_from}\nto={date_to}\nintent={intent}\ndimensions={state.get('dimensions')}\nmetrics={state.get('metrics')}"),
        ])
        raw = response.content if isinstance(response.content, str) else "[]"
        try:
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            pipeline = json.loads(cleaned)
        except Exception:
            pipeline = PRESET_PIPELINES["revenue_trend"]
        desc = f"Custom pipeline for {intent}"
        print(f"  Gemini generated pipeline ({len(pipeline)} stages)")

    return {"mongo_pipeline": pipeline, "query_description": desc}
