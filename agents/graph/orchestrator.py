"""
Invoxio — Master Orchestrator Graph (LangGraph StateGraph)

Wires all 4 ReAct nodes into a directed graph:

    START
      │
      ▼
  ┌──────┐
  │ THINK│  ← Plans next action, selects tool
  └──┬───┘
     │
     ▼
  ┌──────┐
  │  ACT │  ← Executes tool, calls sub-agents
  └──┬───┘
     │
     ▼
  ┌─────────┐
  │ OBSERVE │  ← Summarizes what the tool returned
  └────┬────┘
       │
       ▼
  ┌─────────┐
  │ REFLECT │  ← Decides: done? or loop back to THINK?
  └────┬────┘
       │
    ┌──┴──┐
    │     │
    ▼     ▼
  THINK   END

Usage:
    from graph.orchestrator import build_graph

    graph = build_graph()
    result = await graph.ainvoke(initial_state)
"""

from langgraph.graph import StateGraph, START, END
from graph.state import OrchestratorState
from graph.nodes.think import think_node
from graph.nodes.act import act_node
from graph.nodes.observe import observe_node
from graph.nodes.reflect import reflect_node, should_continue


def build_graph() -> StateGraph:
    """
    Constructs and compiles the Master Orchestrator LangGraph.

    Returns:
        A compiled LangGraph ready for .ainvoke() or .astream()
    """

    # 1. Create the StateGraph with OrchestratorState
    graph = StateGraph(OrchestratorState)

    # 2. Register all nodes
    graph.add_node("think",   think_node)
    graph.add_node("act",     act_node)
    graph.add_node("observe", observe_node)
    graph.add_node("reflect", reflect_node)

    # 3. Define edges (the flow between nodes)

    # START → THINK (always begin with planning)
    graph.add_edge(START, "think")

    # THINK → ACT (after planning, execute)
    graph.add_edge("think", "act")

    # ACT → OBSERVE (after executing, analyze results)
    graph.add_edge("act", "observe")

    # OBSERVE → REFLECT (after observing, decide next step)
    graph.add_edge("observe", "reflect")

    # REFLECT → THINK or END (conditional — the ReAct loop decision)
    graph.add_conditional_edges(
        "reflect",          # From this node
        should_continue,    # Call this function to decide
        {
            "think": "think",   # "think" → loop back
            "end":   END,       # "end"   → terminate
        },
    )

    # 4. Compile and return
    compiled = graph.compile()
    print("Master Orchestrator Graph compiled successfully")
    return compiled


# Convenience: pre-built graph singleton
orchestrator = build_graph()
