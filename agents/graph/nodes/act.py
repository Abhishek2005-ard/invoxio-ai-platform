"""
ACT Node — Step 2 of the ReAct Loop

Responsibility:
  - Read tool_name and tool_input from the THINK node
  - Route to the correct sub-agent / tool (including the new LangChain StructuredTools)
  - Execute the tool call and return the raw result

ReAct Loop:  THINK → [ACT] → OBSERVE → REFLECT
"""

from graph.state import OrchestratorState

# ── Old Stub Tools ────────────────────────────────────────────────────────────
from tools.invoice_tools import query_invoices, get_invoice_detail
from tools.analytics_tools import get_revenue_trends, get_cash_flow, get_top_clients, forecast_revenue, get_overdue_report
from tools.action_tools import send_payment_reminder, generate_pdf_report

# ── New Production Structured Tools ───────────────────────────────────────────
from tools.db_query_tool import db_query_tool
from tools.ocr_tool import ocr_tool
from tools.vector_search_tool import vector_search_tool
from tools.notify_tool import notify_tool
from tools.payment_tool import payment_tool
from tools.code_run_tool import code_run_tool

# ── Sub-Agents ────────────────────────────────────────────────────────────────
from subagents.bi_insights.graph import bi_graph
from subagents.anomaly_detection.graph import anomaly_graph
from subagents.forecasting.graph import forecast_graph
from subagents.report_generation.graph import report_graph

# ── Tool Registry ─────────────────────────────────────────────────────────────
TOOL_REGISTRY = {
    # Sub-Agents orchestrated as tools
    "bi_insights":       bi_graph.ainvoke,
    "anomaly_detection": anomaly_graph.ainvoke,
    "forecasting":       forecast_graph.ainvoke,
    "report_generation": report_graph.ainvoke,

    # Production Structured Tools
    "db_query":          db_query_tool.ainvoke,
    "ocr":               ocr_tool.ainvoke,
    "vector_search":     vector_search_tool.ainvoke,
    "notify":            notify_tool.ainvoke,
    "payment":           payment_tool.ainvoke,
    "code_run":          code_run_tool.ainvoke,

    "general_response":  None,
}


async def act_node(state: OrchestratorState) -> dict:
    """
    ACT Node — Executes the tool decided by the THINK node.

    Reads:  tool_name, tool_input, tenant_id
    Writes: observations (appends one new observation)
    """
    tool_name = state.get("tool_name", "general_response")
    tool_input = state.get("tool_input", {})
    tenant_id = state["tenant_id"]

    print(f"\n⚡ [ACT] Executing tool: '{tool_name}' with input: {tool_input}")

    if tool_name == "general_response" or tool_name not in TOOL_REGISTRY:
        result = {
            "status": "general",
            "message": "No external tool needed — will answer from context.",
        }
        print(f"ℹ️  [ACT] General response — skipping tool call")
    else:
        tool_fn = TOOL_REGISTRY[tool_name]
        try:
            # Inject tenant_id dynamically into tool input
            tool_input["tenant_id"] = tenant_id

            # Call the tool (handles both async defs and LangChain StructuredTools)
            result = await tool_fn(tool_input)
            print(f"✅ [ACT] Tool '{tool_name}' returned result")
        except Exception as e:
            result = {"status": "error", "error": str(e)}
            print(f"❌ [ACT] Tool '{tool_name}' failed: {e}")

    # Append observation
    existing_observations = state.get("observations", [])
    new_observation = {
        "step": state.get("current_step_index", 0),
        "tool": tool_name,
        "input": tool_input,
        "result": result,
    }

    return {
        "observations": existing_observations + [new_observation],
        "current_step_index": state.get("current_step_index", 0) + 1,
    }
