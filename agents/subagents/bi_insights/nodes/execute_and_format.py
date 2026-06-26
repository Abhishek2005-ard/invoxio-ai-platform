"""
Node 3/5 — execute_query  |  Node 4/5 — generate_chart_data  |  Node 5/5 — compose_response
Pipeline: parse_question → build_query → [execute_query → generate_chart_data → compose_response]
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.gemini import llm_think
from subagents.bi_insights.state import BIInsightsState

# Node 3: execute_query
async def execute_query_node(state: BIInsightsState) -> dict:
    """Runs the MongoDB aggregation pipeline. Returns stub data until DB is connected."""
    print(f"\n[execute_query] Running {len(state.get('mongo_pipeline',[]))} pipeline stages...")
    from config.database import get_db
    db = await get_db()
    
    if db is not None and "mongo_pipeline" in state and state["mongo_pipeline"]:
        try:
            results = await db.invoices.aggregate(state["mongo_pipeline"]).to_list(length=100)
            print(f"  DB Query returned {len(results)} records")
            return {"raw_results": results, "result_count": len(results)}
        except Exception as e:
            print(f"  Error: DB Query failed: {e}")
            # Fall back to stub below
            pass

    # Stub data mapped by intent
    STUB = {
        "revenue_trend": [
            {"month":"2024-01","total_revenue":42000,"count":8},{"month":"2024-02","total_revenue":51000,"count":10},
            {"month":"2024-03","total_revenue":48500,"count":9},{"month":"2024-04","total_revenue":63000,"count":12},
            {"month":"2024-05","total_revenue":57000,"count":11},{"month":"2024-06","total_revenue":71000,"count":14},
        ],
        "top_clients": [
            {"client":"Acme Corp","total_revenue":85000,"invoice_count":14},
            {"client":"Beta Ltd","total_revenue":62000,"invoice_count":10},
            {"client":"Gamma Inc","total_revenue":41000,"invoice_count":7},
            {"client":"Delta Co","total_revenue":28000,"invoice_count":5},
            {"client":"Epsilon LLC","total_revenue":19000,"invoice_count":3},
        ],
        "invoice_status": [
            {"status":"paid","count":48,"total_amount":245000},
            {"status":"unpaid","count":12,"total_amount":58000},
            {"status":"overdue","count":5,"total_amount":31000},
            {"status":"draft","count":3,"total_amount":14000},
        ],
        "cash_flow": [
            {"month":"2024-01","paid":35000,"unpaid":7000},{"month":"2024-02","paid":44000,"unpaid":7000},
            {"month":"2024-03","paid":41000,"unpaid":7500},{"month":"2024-04","paid":55000,"unpaid":8000},
        ],
    }
    intent  = state.get("query_intent","revenue_trend")
    results = STUB.get(intent, STUB["revenue_trend"])
    print(f"  Stub Query returned {len(results)} records")
    return {"raw_results": results, "result_count": len(results)}


# Node 4: generate_chart_data
async def generate_chart_data_node(state: BIInsightsState) -> dict:
    """Transforms raw query results into Recharts-compatible chart data + KPI cards."""
    print(f"\n[generate_chart_data] Formatting {state.get('result_count',0)} records as {state.get('chart_type','bar')} chart...")
    results    = state.get("raw_results", [])
    intent     = state.get("query_intent", "revenue_trend")
    chart_type = state.get("chart_type", "bar")

    # Recharts data array — each item is one data point
    chart_data = {"type": chart_type, "data": results, "intent": intent}

    # KPI cards for the dashboard header
    kpi_cards = []
    if intent == "revenue_trend":
        total = sum(r.get("total_revenue", 0) for r in results)
        kpi_cards = [
            {"label":"Total Revenue","value":f"${total:,.0f}","trend":"up"},
            {"label":"Avg Monthly","value":f"${total/max(len(results),1):,.0f}","trend":"neutral"},
            {"label":"Invoice Count","value":str(sum(r.get("count",0) for r in results)),"trend":"up"},
        ]
    elif intent == "top_clients":
        kpi_cards = [{"label":r["client"],"value":f"${r['total_revenue']:,.0f}","trend":"neutral"} for r in results[:3]]
    elif intent == "invoice_status":
        paid = next((r for r in results if r["status"]=="paid"), {})
        overdue = next((r for r in results if r["status"]=="overdue"), {})
        kpi_cards = [
            {"label":"Paid","value":f"${paid.get('total_amount',0):,.0f}","trend":"up"},
            {"label":"Overdue","value":f"${overdue.get('total_amount',0):,.0f}","trend":"down"},
        ]
    elif intent == "cash_flow":
        total_paid   = sum(r.get("paid", 0) for r in results)
        total_unpaid = sum(r.get("unpaid", 0) for r in results)
        kpi_cards = [
            {"label":"Net Cash Flow","value":f"${total_paid - total_unpaid:,.0f}","trend":"up"},
            {"label":"Collected","value":f"${total_paid:,.0f}","trend":"up"},
            {"label":"Outstanding","value":f"${total_unpaid:,.0f}","trend":"down"},
        ]

    print(f"  Chart data ready | {len(kpi_cards)} KPI cards")
    return {"chart_data": chart_data, "kpi_cards": kpi_cards}


# Node 5: compose_response
NARRATE_PROMPT = """You are a business analyst providing insights from financial data.

Write a concise 2-3 sentence plain-English answer to the user's question based on the data.
Highlight the most important number, trend, or insight. Be specific — include actual values.
"""

async def compose_response_node(state: BIInsightsState) -> dict:
    """Gemini writes a plain-English narrative + assembles the final response."""
    print(f"\n[compose_response] Writing narrative...")
    question   = state.get("question","")
    results    = state.get("raw_results",[])
    period     = state.get("time_period",{})

    try:
        response = await llm_think.ainvoke([
            SystemMessage(content=NARRATE_PROMPT),
            HumanMessage(content=f"Question: {question}\nPeriod: {period.get('label','')}\nData: {json.dumps(results[:10], default=str)}"),
        ])
        narrative = response.content if isinstance(response.content, str) else "Data retrieved successfully."
    except Exception as e:
        narrative = f"Query executed successfully. {len(results)} records found."

    final_response = {
        "question":      question,
        "narrative":     narrative,
        "chart":         state.get("chart_data", {}),
        "kpi_cards":     state.get("kpi_cards", []),
        "query_intent":  state.get("query_intent",""),
        "time_period":   period,
        "record_count":  state.get("result_count", 0),
    }
    print(f"  Response ready")
    return {"narrative": narrative, "final_response": final_response}
