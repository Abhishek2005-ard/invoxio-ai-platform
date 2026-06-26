"""
THINK Node — Step 1 of the ReAct Loop

Responsibility:
  - Read the user's request + previous observations
  - Produce a structured plan (list of steps)
  - Decide which tool/sub-agent to call next

This is the BRAIN of the orchestrator. It reasons about WHAT to do
before anything is actually executed.

ReAct Loop:  [THINK] → ACT → OBSERVE → REFLECT
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.gemini import llm_think
from graph.state import OrchestratorState

#  System prompt for the THINK node.
#  Instructs Gemini to reason step-by-step and output structured JSON.
THINK_SYSTEM_PROMPT = """You are the Master Orchestrator for Invoxio, an AI-powered business intelligence platform.

Your job in this THINK step is to:
1. Understand the user's request completely
2. Review any previous observations from prior steps
3. Create a clear, step-by-step plan
4. Decide the NEXT immediate action to take

Available Sub-Agents / Tools:
- "bi_insights"      → General query tool for revenue trends, cash flow, or invoice details (calls bi_graph)
- "anomaly_detection"→ Scan tenant invoices for duplicates or fraud (calls anomaly_graph)
- "forecasting"      → Predict future revenue or cash flow (calls forecast_graph)
- "report_generation"→ Compile and distribute a PDF summary (calls report_graph)
- "general_response" → Answer from context, no database needed

Output ONLY valid JSON in this exact format:
{
  "plan": "Brief description of the overall plan",
  "steps": ["step 1", "step 2", "step 3"],
  "next_tool": "tool_name_from_list_above",
  "next_tool_input": {
    "query": "natural language query for the tool",
    "filters": {}
  },
  "reasoning": "Why you chose this tool and these inputs"
}

Rules:
- Always use a tool from the allowed list
- Be specific in tool inputs — include date ranges, client names, amounts if mentioned
- If previous observations have partial results, plan the next step to fill gaps
- If the task needs multiple steps, plan them ALL upfront in "steps"
"""


async def think_node(state: OrchestratorState) -> dict:
    """
    THINK Node — Plans the next action based on user request and observations.

    Reads:  messages, observations, iteration
    Writes: plan, steps, current_step_index, tool_name, tool_input
    """
    print(f"\n[THINK] Iteration {state['iteration'] + 1} — Planning next action...")

    # Build context from previous observations
    observation_context = ""
    if state.get("observations"):
        obs_list = "\n".join(
            f"  Step {i+1} ({o['tool']}): {json.dumps(o['result'])[:500]}"
            for i, o in enumerate(state["observations"])
        )
        observation_context = f"\n\nPrevious Observations:\n{obs_list}"

    # Get user's original request
    user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    # Invoke Gemini to produce a plan
    prompt_content = f"User Request: {user_message}{observation_context}"

    response = await llm_think.ainvoke([
        SystemMessage(content=THINK_SYSTEM_PROMPT),
        HumanMessage(content=prompt_content),
    ])

    raw = response.content if isinstance(response.content, str) else str(response.content)

    # Parse the JSON plan
    try:
        # Strip markdown code fences if Gemini wraps the JSON
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        plan_data = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"Warning: [THINK] JSON parse failed — using fallback plan")
        plan_data = {
            "plan": "Answer the user's question directly",
            "steps": ["Provide a general response"],
            "next_tool": "general_response",
            "next_tool_input": {"query": user_message},
            "reasoning": "Fallback due to parse error",
        }

    print(f"[THINK] Plan: {plan_data.get('plan', '')}")
    print(f"[THINK] Next tool: {plan_data.get('next_tool', '')} — Input: {plan_data.get('next_tool_input', {})}")

    return {
        "plan": plan_data.get("plan", ""),
        "steps": plan_data.get("steps", []),
        "current_step_index": state.get("current_step_index", 0),
        "tool_name": plan_data.get("next_tool", "general_response"),
        "tool_input": plan_data.get("next_tool_input", {}),
    }
