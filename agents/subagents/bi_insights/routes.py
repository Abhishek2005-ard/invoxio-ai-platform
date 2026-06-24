"""BI Insights Routes — POST /api/bi/ask"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from subagents.bi_insights.graph import bi_graph

router = APIRouter()

class BIRequest(BaseModel):
    question:  str
    tenant_id: str = "demo-tenant"

@router.post("/ask")
async def ask_bi(req: BIRequest):
    """
    Ask a natural language business intelligence question.
    Returns chart data + KPI cards + AI narrative.

    Examples:
      - "What is my total revenue this quarter?"
      - "Who are my top 5 clients by revenue?"
      - "Show me cash flow for the last 6 months"
      - "What's my invoice status breakdown?"
    """
    print(f"\n💬 [POST /bi/ask] '{req.question}' for tenant={req.tenant_id}")
    initial = {
        "tenant_id":req.tenant_id,"question":req.question,
        "query_intent":"","time_period":{},"dimensions":[],"metrics":[],
        "mongo_pipeline":[],"query_description":"",
        "raw_results":[],"result_count":0,
        "chart_type":"bar","chart_data":{},"kpi_cards":[],
        "narrative":"","final_response":{},"error":None,
    }
    try:
        result = await bi_graph.ainvoke(initial)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, **result.get("final_response", {})}

@router.get("/health")
async def bi_health():
    return {"status":"healthy","pipeline":["parse_question","build_query","execute_query","generate_chart_data","compose_response"]}
