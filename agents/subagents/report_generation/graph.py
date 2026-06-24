"""Report Generation LangGraph — gather_data → generate_content → render_pdf → distribute → END"""
from langgraph.graph import StateGraph, START, END
from subagents.report_generation.state import ReportGenerationState
from subagents.report_generation.nodes.report_nodes import (
    gather_data_node, generate_content_node, render_pdf_node, distribute_node
)

def build_report_graph():
    g = StateGraph(ReportGenerationState)
    g.add_node("gather_data",       gather_data_node)
    g.add_node("generate_content",  generate_content_node)
    g.add_node("render_pdf",        render_pdf_node)
    g.add_node("distribute",        distribute_node)
    g.add_edge(START,               "gather_data")
    g.add_edge("gather_data",       "generate_content")
    g.add_edge("generate_content",  "render_pdf")
    g.add_edge("render_pdf",        "distribute")
    g.add_edge("distribute",        END)
    c = g.compile()
    print("✅ Report Generation graph compiled")
    return c

report_graph = build_report_graph()
