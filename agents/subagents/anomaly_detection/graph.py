"""
Anomaly Detection Sub-Agent — LangGraph Pipeline

Flow:
    START
      │
      ▼
  ┌──────────────────┐
  │  ingest_invoices │  Normalize invoices + compute stats baseline
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────────┐
  │  detect_duplicates   │  Exact / fuzzy / amount+vendor duplicate pairs
  └────────┬─────────────┘
           │
           ▼
  ┌──────────────┐
  │ detect_fraud │  Rule-based checks + Gemini AI pattern analysis
  └──────┬───────┘
         │
         ▼
  ┌───────────────┐
  │ score_outliers│  Z-score + IQR statistical outlier scoring
  └──────┬────────┘
         │
         ▼
  ┌─────────────────┐
  │ generate_report │  Consolidate + AI narrative + recommendations
  └──────┬──────────┘
         │
         ▼
        END
"""

from langgraph.graph import StateGraph, START, END

from subagents.anomaly_detection.state import AnomalyDetectionState
from subagents.anomaly_detection.nodes.ingest_invoices   import ingest_invoices_node
from subagents.anomaly_detection.nodes.detect_duplicates import detect_duplicates_node
from subagents.anomaly_detection.nodes.detect_fraud      import detect_fraud_node
from subagents.anomaly_detection.nodes.score_outliers    import score_outliers_node
from subagents.anomaly_detection.nodes.generate_report   import generate_report_node


def build_anomaly_graph():
    """
    Builds and compiles the Anomaly Detection sub-agent LangGraph.

    Returns:
        Compiled LangGraph ready for .ainvoke() or .astream()
    """
    graph = StateGraph(AnomalyDetectionState)

    # Register all 5 nodes
    graph.add_node("ingest_invoices",   ingest_invoices_node)
    graph.add_node("detect_duplicates", detect_duplicates_node)
    graph.add_node("detect_fraud",      detect_fraud_node)
    graph.add_node("score_outliers",    score_outliers_node)
    graph.add_node("generate_report",   generate_report_node)

    # Linear pipeline edges
    graph.add_edge(START,                "ingest_invoices")
    graph.add_edge("ingest_invoices",    "detect_duplicates")
    graph.add_edge("detect_duplicates",  "detect_fraud")
    graph.add_edge("detect_fraud",       "score_outliers")
    graph.add_edge("score_outliers",     "generate_report")
    graph.add_edge("generate_report",    END)

    compiled = graph.compile()
    print("Anomaly Detection Sub-Agent graph compiled")
    return compiled


# Singleton
anomaly_graph = build_anomaly_graph()
