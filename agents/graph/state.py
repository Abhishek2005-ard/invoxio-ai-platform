"""
Invoxio — Orchestrator Agent State

This is the SHARED MEMORY that flows through every node in the LangGraph.
Every node reads from this state and returns a partial update.
LangGraph automatically merges updates between nodes.

ReAct Loop Fields:
  THINK  → populates: plan, steps, current_action
  ACT    → populates: tool_name, tool_input
  OBSERVE→ populates: observations (appends results)
  REFLECT→ populates: is_complete, final_answer, or loops back to THINK
"""

from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class OrchestratorState(TypedDict):
    """
    The single shared state object for the Master Orchestrator Agent.
    Flows through every node in the LangGraph StateGraph.
    """

    # Conversation
    # add_messages is a LangGraph reducer: APPENDS new messages instead of overwriting
    messages: Annotated[List[BaseMessage], add_messages]

    # Identity & Tenancy
    tenant_id: str          # Scopes every DB call — prevents cross-tenant data leaks
    user_id: str            # Who is chatting
    session_id: str         # Unique chat session identifier

    # THINK node outputs
    plan: str               # High-level plan produced by the THINK node
    steps: List[str]        # Ordered list of steps to execute
    current_step_index: int # Which step we're currently executing

    # ACT node outputs
    tool_name: str              # Name of the tool/sub-agent to call
    tool_input: Dict[str, Any]  # Arguments passed to the tool

    # OBSERVE node outputs
    # List of (step, result) tuples — one per ACT→OBSERVE cycle
    observations: List[Dict[str, Any]]

    # REFLECT node outputs
    reflection: str         # Reasoning about whether the task is done
    is_complete: bool       # If True → END the loop, if False → loop back to THINK
    final_answer: str       # The synthesized response sent back to the user

    # Loop Control
    iteration: int          # Current ReAct loop iteration count
    max_iterations: int     # Hard ceiling to prevent infinite loops

    # Error Handling
    error: Optional[str]    # Populated if any node fails
