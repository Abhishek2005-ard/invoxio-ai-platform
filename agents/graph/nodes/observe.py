"""
OBSERVE Node — Step 3 of the ReAct Loop

Responsibility:
  - Examine the latest tool result from the ACT node
  - Summarize what was found (not the final answer — just what the tool returned)
  - Identify if the result is sufficient or if more steps are needed
  - Prepare a concise observation summary for the REFLECT node

ReAct Loop:  THINK → ACT → [OBSERVE] → REFLECT
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.gemini import llm_think
from graph.state import OrchestratorState

OBSERVE_SYSTEM_PROMPT = """You are analyzing a tool result from an AI business intelligence system.

Your job in this OBSERVE step:
1. Summarize what the tool actually returned (facts only — no conclusions yet)
2. Identify any gaps, errors, or missing data
3. State clearly whether the result answers the user's request

Output a brief, factual observation in 2-4 sentences.
Do NOT make final recommendations yet — just describe what was observed.
"""


async def observe_node(state: OrchestratorState) -> dict:
    """
    OBSERVE Node — Summarizes the latest tool result.

    Reads:  observations (last entry), messages (user request)
    Writes: observation summary appended to the last observation entry
    """
    observations = state.get("observations", [])
    if not observations:
        print("⚠️  [OBSERVE] No observations to process")
        return {}

    latest = observations[-1]
    tool_name = latest.get("tool", "unknown")
    result = latest.get("result", {})

    print(f"\n👁️  [OBSERVE] Analyzing result from: '{tool_name}'")

    # ── Get original user question ────────────────────────────────────────
    user_question = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            user_question = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    # ── Ask Gemini to summarize the tool result ───────────────────────────
    result_str = json.dumps(result, indent=2, default=str)[:2000]  # cap at 2k chars

    response = await llm_think.ainvoke([
        SystemMessage(content=OBSERVE_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"User's question: {user_question}\n\n"
            f"Tool used: {tool_name}\n\n"
            f"Tool result:\n{result_str}"
        )),
    ])

    summary = response.content if isinstance(response.content, str) else str(response.content)
    print(f"📝 [OBSERVE] Summary: {summary[:200]}...")

    # ── Attach summary to the latest observation ──────────────────────────
    updated_observations = observations[:-1] + [{
        **latest,
        "summary": summary,
    }]

    return {
        "observations": updated_observations,
    }
