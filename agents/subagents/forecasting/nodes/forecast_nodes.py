"""
Forecasting Nodes — Pure Python linear regression + seasonality + Gemini insights
Pipeline: load_historical → compute_forecast → detect_seasonality → generate_insights
"""
import json
import math
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
from config.gemini import llm_think
from subagents.forecasting.state import ForecastingState


async def load_historical_node(state: ForecastingState) -> dict:
    """
    Loads historical revenue or cash-flow data for the forecasting node.
    Currently uses stub data if database records are insufficient.
    """
    metric = state.get("metric","revenue")
    print(f"\n[load_historical] Loading historical {metric} data for tenant={state['tenant_id']}...")

    from config.database import get_db
    db = await get_db()

    data = []
    if db is not None:
        try:
            # Group invoices by month and sum the amounts
            pipeline = [
                {"$match": {"tenant_id": state["tenant_id"]}},
                {"$group": {
                    "_id": {"$substr": ["$invoice_date", 0, 7]},  # "YYYY-MM"
                    "value": {"$sum": "$amount"}
                }},
                {"$sort": {"_id": 1}},
                {"$project": {"date": "$_id", "value": 1, "_id": 0}}
            ]
            
            db_results = await db.invoices.aggregate(pipeline).to_list(length=100)
            
            if db_results and len(db_results) >= 3:
                # Need at least 3 points for meaningful forecasting
                if metric == "cash_flow":
                    # Simple heuristic: cash flow is typically collected invoices, let's say 72%
                    data = [{"date": d["date"], "value": int(d["value"] * 0.72)} for d in db_results]
                else:
                    data = db_results
        except Exception as e:
            print(f"  Error: DB Query failed for forecasting: {e}")

    if not data:
        print("  Info: Using stub data for forecasting")
        # Stub: 12 months of realistic revenue data
        STUB_REVENUE = [
            {"date":"2023-07","value":38000},{"date":"2023-08","value":41000},
            {"date":"2023-09","value":44500},{"date":"2023-10","value":47000},
            {"date":"2023-11","value":43000},{"date":"2023-12","value":39000},
            {"date":"2024-01","value":42000},{"date":"2024-02","value":51000},
            {"date":"2024-03","value":48500},{"date":"2024-04","value":63000},
            {"date":"2024-05","value":57000},{"date":"2024-06","value":71000},
        ]
        STUB_CASH_FLOW = [{"date":d["date"],"value":int(d["value"]*0.72)} for d in STUB_REVENUE]
        data = STUB_CASH_FLOW if metric == "cash_flow" else STUB_REVENUE

    print(f"  Loaded {len(data)} data points spanning {len(data)} months")
    return {"historical_data": data, "data_points": len(data), "coverage_months": len(data)}


async def compute_forecast_node(state: ForecastingState) -> dict:
    """
    Computes forecasting projections using pure Python linear regression.
    """
    data         = state.get("historical_data", [])
    forecast_days = state.get("forecast_days", 30)
    print(f"\n[compute_forecast] Running linear regression over {len(data)} points, forecasting {forecast_days} days...")

    if len(data) < 3:
        return {"forecast_values":[],"model_stats":{},"trend_direction":"stable","growth_rate":0.0}

    n      = len(data)
    x_vals = list(range(n))
    y_vals = [d["value"] for d in data]

    x_mean = sum(x_vals) / n
    y_mean = sum(y_vals) / n

    numerator   = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
    denominator = sum((x - x_mean) ** 2 for x in x_vals)
    slope       = numerator / denominator if denominator != 0 else 0
    intercept   = y_mean - slope * x_mean

    # R² score
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_vals, y_vals))
    ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    # RMSE
    rmse = math.sqrt(ss_res / n)

    # Monthly growth rate
    if y_vals[0] > 0:
        growth_rate = ((y_vals[-1] - y_vals[0]) / y_vals[0]) / (n - 1) * 100
    else:
        growth_rate = 0.0

    forecast_months = max(1, forecast_days // 30)
    forecast_values = []
    last_date_str   = data[-1]["date"]

    # Parse last date and generate future months
    try:
        last_dt = datetime.strptime(last_date_str, "%Y-%m")
    except Exception:
        last_dt = datetime.now(timezone.utc)

    std_error = rmse * 1.96  # 95% confidence interval
    for i in range(1, forecast_months + 1):
        x_new       = n - 1 + i
        predicted   = slope * x_new + intercept
        predicted   = max(0, predicted)  # Revenue can't be negative
        future_date = (last_dt.replace(day=1) + timedelta(days=32 * i)).strftime("%Y-%m")
        forecast_values.append({
            "date":        future_date,
            "predicted":   round(predicted, 2),
            "lower_bound": round(max(0, predicted - std_error), 2),
            "upper_bound": round(predicted + std_error, 2),
        })

    trend_direction = "upward" if slope > 500 else ("downward" if slope < -500 else "stable")
    model_stats = {"r_squared": round(r_squared, 4), "slope": round(slope, 2),
                   "intercept": round(intercept, 2), "rmse": round(rmse, 2)}

    print(f"  R²={r_squared:.3f} | slope={slope:.0f}/month | trend={trend_direction} | "
          f"growth={growth_rate:+.1f}%/month")
    for fv in forecast_values:
        print(f"  {fv['date']}: ${fv['predicted']:,.0f} [{fv['lower_bound']:,.0f}–{fv['upper_bound']:,.0f}]")

    return {
        "forecast_values": forecast_values,
        "model_stats":     model_stats,
        "trend_direction": trend_direction,
        "growth_rate":     round(growth_rate, 2),
    }


MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

async def detect_seasonality_node(state: ForecastingState) -> dict:
    """
    Analyzes historical data to identify monthly seasonal patterns,
    including the best and worst performing months.
    """
    data = state.get("historical_data", [])
    print(f"\n[detect_seasonality] Analyzing seasonal patterns...")

    if len(data) < 6:
        return {"seasonality_found":False,"seasonal_patterns":[],"best_month":"N/A","worst_month":"N/A"}

    # Group by month number and compute average
    month_totals: Dict[int, List[float]] = {}
    for d in data:
        try:
            month_num = int(d["date"].split("-")[1])
            month_totals.setdefault(month_num, []).append(d["value"])
        except Exception:
            continue

    overall_mean = sum(d["value"] for d in data) / len(data)
    patterns = []
    for month_num, values in month_totals.items():
        avg = sum(values) / len(values)
        factor = avg / overall_mean if overall_mean > 0 else 1.0
        patterns.append({
            "month":  MONTH_NAMES[month_num - 1],
            "factor": round(factor, 3),
            "label":  "above average" if factor > 1.05 else ("below average" if factor < 0.95 else "average"),
            "avg_value": round(avg, 2),
        })

    patterns.sort(key=lambda x: x["factor"])
    worst = patterns[0]["month"] if patterns else "N/A"
    best  = patterns[-1]["month"] if patterns else "N/A"
    found = any(p["factor"] > 1.15 or p["factor"] < 0.85 for p in patterns)

    print(f"  Seasonality detected: {found} | Best: {best} | Worst: {worst}")
    return {"seasonality_found":found,"seasonal_patterns":patterns,"best_month":best,"worst_month":worst}


INSIGHTS_PROMPT = """You are a financial forecasting analyst.
Based on the revenue forecast data and seasonality patterns, provide:
1. A 3-sentence narrative explaining the forecast in plain English for a business owner
2. 3 specific risk factors that could cause the forecast to be wrong
3. 3 specific opportunities to accelerate the growth trend

Be concrete — reference actual numbers, percentages, and months.

Output ONLY valid JSON:
{
  "narrative": "...",
  "risk_factors": ["risk 1", "risk 2", "risk 3"],
  "opportunities": ["opp 1", "opp 2", "opp 3"]
}
"""

async def generate_insights_node(state: ForecastingState) -> dict:
    """
    Uses the LLM to generate a plain-English narrative, risk factors, 
    and opportunities based on the computed forecast and seasonality.
    """
    print(f"\n[generate_insights] Generating AI insights...")

    context = {
        "metric":         state.get("metric"),
        "forecast_days":  state.get("forecast_days"),
        "trend":          state.get("trend_direction"),
        "growth_rate":    f"{state.get('growth_rate',0):+.1f}%/month",
        "r_squared":      state.get("model_stats",{}).get("r_squared"),
        "forecast":       state.get("forecast_values",[]),
        "best_month":     state.get("best_month"),
        "worst_month":    state.get("worst_month"),
        "seasonality":    state.get("seasonality_found"),
    }

    try:
        response = await llm_think.ainvoke([
            SystemMessage(content=INSIGHTS_PROMPT),
            HumanMessage(content=json.dumps(context, default=str)),
        ])
        raw = response.content if isinstance(response.content, str) else "{}"
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        narrative    = parsed.get("narrative","Forecast generated successfully.")
        risks        = parsed.get("risk_factors",["Market conditions may change."])
        opportunities= parsed.get("opportunities",["Focus on top clients."])
    except Exception as e:
        print(f"  Warning: Insight generation error: {e}")
        narrative    = f"Revenue shows a {state.get('trend_direction','stable')} trend with {state.get('growth_rate',0):+.1f}%/month growth."
        risks        = ["Market uncertainty","Client churn","Seasonal slowdown"]
        opportunities= ["Upsell top clients","Accelerate collections","Enter new market"]

    final_forecast = {
        "metric":           state.get("metric"),
        "forecast_days":    state.get("forecast_days"),
        "trend_direction":  state.get("trend_direction"),
        "growth_rate":      state.get("growth_rate"),
        "model_accuracy":   f"{state.get('model_stats',{}).get('r_squared',0)*100:.1f}%",
        "historical_data":  state.get("historical_data",[]),
        "forecast_values":  state.get("forecast_values",[]),
        "seasonal_patterns":state.get("seasonal_patterns",[]),
        "best_month":       state.get("best_month"),
        "worst_month":      state.get("worst_month"),
        "narrative":        narrative,
        "risk_factors":     risks,
        "opportunities":    opportunities,
    }

    print(f"  Insights complete | Trend: {state.get('trend_direction')} | Growth: {state.get('growth_rate'):+.1f}%/month")
    return {"forecast_narrative":narrative,"risk_factors":risks,"opportunities":opportunities,"final_forecast":final_forecast}
