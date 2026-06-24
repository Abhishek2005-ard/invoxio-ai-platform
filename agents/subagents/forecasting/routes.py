"""Forecasting Routes — POST /api/forecast/run"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from subagents.forecasting.graph import forecast_graph

router = APIRouter()

class ForecastRequest(BaseModel):
    tenant_id:     str = "demo-tenant"
    forecast_days: int = Field(default=30, description="30, 60, or 90 days")
    metric:        Literal["revenue","cash_flow","invoice_volume"] = "revenue"

@router.post("/run")
async def run_forecast(req: ForecastRequest):
    """
    Run AI revenue/cash flow forecasting.
    Uses linear regression on historical data + seasonality analysis + Gemini insights.

    Returns:
      - forecast_values: predicted amounts per month with confidence intervals
      - trend_direction: upward | downward | stable
      - growth_rate: monthly % growth
      - seasonal_patterns: best/worst months
      - narrative + risk_factors + opportunities
    """
    print(f"\n🔮 [POST /forecast/run] metric={req.metric} | days={req.forecast_days}")
    initial = {
        "tenant_id":req.tenant_id,"forecast_days":req.forecast_days,"metric":req.metric,
        "historical_data":[],"data_points":0,"coverage_months":0,
        "forecast_values":[],"model_stats":{},"trend_direction":"stable","growth_rate":0.0,
        "seasonality_found":False,"seasonal_patterns":[],"best_month":"","worst_month":"",
        "forecast_narrative":"","risk_factors":[],"opportunities":[],"final_forecast":{},"error":None,
    }
    try:
        result = await forecast_graph.ainvoke(initial)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, **result.get("final_forecast", {})}

@router.get("/health")
async def forecast_health():
    return {"status":"healthy","pipeline":["load_historical","compute_forecast","detect_seasonality","generate_insights"]}
