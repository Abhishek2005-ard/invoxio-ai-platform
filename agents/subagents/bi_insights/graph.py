"""BI Insights Sub-Agent — LangGraph Pipeline
START → parse_question → build_query → execute_query → generate_chart_data → compose_response → END
"""
from langgraph.graph import StateGraph, START, END
from subagents.bi_insights.state import BIInsightsState
from subagents.bi_insights.nodes.parse_question import parse_question_node
from subagents.bi_insights.nodes.build_query import build_query_node
from subagents.bi_insights.nodes.execute_and_format import (
    execute_query_node, generate_chart_data_node, compose_response_node
)

def build_bi_graph():
    g = StateGraph(BIInsightsState)
    g.add_node("parse_question",     parse_question_node)
    g.add_node("build_query",        build_query_node)
    g.add_node("execute_query",      execute_query_node)
    g.add_node("generate_chart_data",generate_chart_data_node)
    g.add_node("compose_response",   compose_response_node)
    g.add_edge(START,                "parse_question")
    g.add_edge("parse_question",     "build_query")
    g.add_edge("build_query",        "execute_query")
    g.add_edge("execute_query",      "generate_chart_data")
    g.add_edge("generate_chart_data","compose_response")
    g.add_edge("compose_response",    END)
    compiled = g.compile()
    print("BI Insights graph compiled")
    return compiled

bi_graph = build_bi_graph()
