"""Forecasting Sub-Agent — State"""
from typing import TypedDict, List, Dict, Any, Optional

class ForecastingState(TypedDict):
    # Input
    tenant_id:         str
    forecast_days:     int          # 30 | 60 | 90
    metric:            str          # "revenue" | "cash_flow" | "invoice_volume"

    # load_historical node
    historical_data:   List[Dict[str, Any]]  # [{date, value}] sorted ascending
    data_points:       int
    coverage_months:   int

    # compute_forecast node
    forecast_values:   List[Dict[str, Any]]  # [{date, predicted, lower_bound, upper_bound}]
    model_stats:       Dict[str, float]      # {r_squared, slope, intercept, rmse}
    trend_direction:   str                   # "upward" | "downward" | "stable"
    growth_rate:       float                 # Monthly % growth rate

    # detect_seasonality node
    seasonality_found: bool
    seasonal_patterns: List[Dict[str, Any]]  # [{month, factor, label}]
    best_month:        str
    worst_month:       str

    # generate_insights node
    forecast_narrative: str
    risk_factors:       List[str]
    opportunities:      List[str]
    final_forecast:     Dict[str, Any]

    error: Optional[str]
