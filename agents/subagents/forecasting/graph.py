"""Forecasting LangGraph — load_historical → compute_forecast → detect_seasonality → generate_insights → END"""
from langgraph.graph import StateGraph, START, END
from subagents.forecasting.state import ForecastingState
from subagents.forecasting.nodes.forecast_nodes import (
    load_historical_node, compute_forecast_node,
    detect_seasonality_node, generate_insights_node
)

def build_forecast_graph():
    g = StateGraph(ForecastingState)
    g.add_node("load_historical",    load_historical_node)
    g.add_node("compute_forecast",   compute_forecast_node)
    g.add_node("detect_seasonality", detect_seasonality_node)
    g.add_node("generate_insights",  generate_insights_node)
    g.add_edge(START,                "load_historical")
    g.add_edge("load_historical",    "compute_forecast")
    g.add_edge("compute_forecast",   "detect_seasonality")
    g.add_edge("detect_seasonality", "generate_insights")
    g.add_edge("generate_insights",   END)
    c = g.compile()
    print("Forecasting graph compiled")
    return c

forecast_graph = build_forecast_graph()
