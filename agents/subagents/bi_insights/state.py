"""BI Insights Sub-Agent — State"""
from typing import TypedDict, List, Dict, Any, Optional

class BIInsightsState(TypedDict):
    # Input
    tenant_id:     str
    question:      str          # NL question: "What's my revenue this quarter?"

    # parse_question node
    query_intent:  str          # "revenue_trend" | "cash_flow" | "top_clients" | "expense_breakdown" | "custom"
    time_period:   Dict[str, str]  # {"from": "2024-01-01", "to": "2024-03-31", "label": "Q1 2024"}
    dimensions:    List[str]    # ["vendor", "client", "category"]
    metrics:       List[str]    # ["total_amount", "count", "avg_amount"]

    # build_query node
    mongo_pipeline: List[Dict[str, Any]]   # MongoDB aggregation pipeline stages
    query_description: str                 # Human-readable description of query

    # execute_query node
    raw_results:   List[Dict[str, Any]]    # Raw MongoDB results
    result_count:  int

    # generate_chart_data node
    chart_type:    str          # "bar" | "line" | "pie" | "area" | "table"
    chart_data:    Dict[str, Any]  # Recharts-compatible data structure
    kpi_cards:     List[Dict[str, Any]]  # Summary KPI values

    # compose_response node
    narrative:     str          # AI-written plain English answer
    final_response: Dict[str, Any]  # Full response with chart + narrative

    error:         Optional[str]
