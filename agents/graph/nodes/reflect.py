"""
REFLECT Node — Step 4 of the ReAct Loop

Responsibility:
  - Review ALL observations collected so far
  - Decide: Is the task complete? Or do we need another THINK→ACT→OBSERVE cycle?
  - If COMPLETE  → synthesize a final, human-friendly answer
  - If INCOMPLETE → signal the graph to loop back to THINK

This is the QUALITY GATE of the agent.

ReAct Loop:  THINK → ACT → OBSERVE → [REFLECT] → (END or loop back to THINK)
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.gemini import llm
from graph.state import OrchestratorState
from config.settings import settings

REFLECT_SYSTEM_PROMPT = """You are the reflection engine for Invoxio, an AI business intelligence platform.

Review all observations collected and decide:

A) If the task is COMPLETE:
   - All necessary data has been gathered
   - You can write a complete, accurate, helpful answer
   - Set is_complete = true and write the final_answer

B) If the task is INCOMPLETE:
   - Key data is missing
   - A tool returned an error and retry would help
   - Additional steps are needed
   - Set is_complete = false and describe what is still needed in reflection

Output ONLY valid JSON:
{
  "is_complete": true or false,
  "reflection": "Your reasoning about why the task is or isn't done",
  "final_answer": "Complete, well-formatted answer (only if is_complete=true, else empty string)"
}

Rules for final_answer:
- Use markdown formatting (bold, bullet points, tables where helpful)
- Include actual numbers and data from observations
- Be concise but complete
- Always acknowledge what you found and what action was taken
"""


async def reflect_node(state: OrchestratorState) -> dict:
    """
    REFLECT Node — Evaluates if the task is done and synthesizes the final answer.

    Reads:  messages, plan, steps, observations, iteration, max_iterations
    Writes: reflection, is_complete, final_answer, iteration
    """
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", settings.agent_max_iterations)

    print(f"\n🪞 [REFLECT] Iteration {iteration + 1}/{max_iter} — Evaluating task completion...")

    # ── Hard stop: max iterations reached ────────────────────────────────
    if iteration >= max_iter - 1:
        print(f"⛔ [REFLECT] Max iterations ({max_iter}) reached — forcing completion")
        observations_text = _format_observations(state.get("observations", []))
        return {
            "is_complete": True,
            "reflection": f"Stopped after {max_iter} iterations.",
            "final_answer": (
                f"I've gathered the following information after {max_iter} steps:\n\n"
                f"{observations_text}\n\n"
                "_Note: Reached maximum reasoning steps. Results may be partial._"
            ),
            "iteration": iteration + 1,
        }

    # ── Get user's original question ──────────────────────────────────────
    user_question = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            user_question = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    # ── Format all observations for context ───────────────────────────────
    observations_text = _format_observations(state.get("observations", []))

    # ── Ask Gemini to reflect ─────────────────────────────────────────────
    response = await llm.ainvoke([
        SystemMessage(content=REFLECT_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"User's original request: {user_question}\n\n"
            f"My plan: {state.get('plan', '')}\n\n"
            f"All steps planned: {state.get('steps', [])}\n\n"
            f"Observations collected:\n{observations_text}"
        )),
    ])

    raw = response.content if isinstance(response.content, str) else str(response.content)

    # ── Parse reflection JSON ─────────────────────────────────────────────
    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        print("⚠️  [REFLECT] JSON parse failed — defaulting to complete")
        result = {
            "is_complete": True,
            "reflection": "Could not parse structured reflection.",
            "final_answer": raw,
        }

    is_complete = result.get("is_complete", True)
    print(f"{'✅' if is_complete else '🔄'} [REFLECT] Complete: {is_complete} — {result.get('reflection', '')[:100]}")

    # ── If complete, add the final answer to message history ──────────────
    new_messages = []
    if is_complete and result.get("final_answer"):
        new_messages = [AIMessage(content=result["final_answer"])]

    return {
        "reflection": result.get("reflection", ""),
        "is_complete": is_complete,
        "final_answer": result.get("final_answer", ""),
        "iteration": iteration + 1,
        "messages": new_messages,   # Appended via add_messages reducer
    }


def _format_observations(observations: list) -> str:
    """Formats the observations list into a readable string for the LLM."""
    if not observations:
        return "No observations yet."
    lines = []
    for i, obs in enumerate(observations):
        summary = obs.get("summary", json.dumps(obs.get("result", {}), default=str)[:300])
        lines.append(f"Step {i+1} [{obs.get('tool', '?')}]: {summary}")
    return "\n".join(lines)


# ── Conditional Edge Function ─────────────────────────────────────────────────
def should_continue(state: OrchestratorState) -> str:
    """
    Conditional edge for LangGraph.
    Called after REFLECT to decide the next node.

    Returns:
        "think"  → loop back to THINK for another ReAct cycle
        "end"    → task is complete, terminate the graph
    """
    if state.get("is_complete", False):
        print("🏁 [ROUTER] Task complete → END")
        return "end"
    else:
        print("🔄 [ROUTER] Task incomplete → loop back to THINK")
        return "think"
