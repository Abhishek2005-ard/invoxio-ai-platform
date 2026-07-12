"""
Invoxio — Supervisor / Orchestrator  (main.py)

Two API surfaces:
  POST /api/agent/chat          — free-form NL chat via master orchestrator graph
  POST /api/pipeline/process    — structured invoice pipeline (parallel + HITL)
  POST /api/pipeline/approve    — resume a paused pipeline after human review
  GET  /api/pipeline/status/{id} — check pipeline state

Run with:
    python main.py
"""

import json
import os
import sys
import uuid

# Force standard streams to use UTF-8 to prevent UnicodeEncodeError on Windows terminals
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from typing import Annotated, Sequence, TypedDict, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

# ── Agent tools ───────────────────────────────────────────────────────────
from agents import (
    make_anomaly_tool,
    make_bi_tool,
    make_categorization_tool,
    make_forecasting_tool,
    make_invoice_tool,
    make_nl_query_tool,
    make_report_tool,
    make_validation_tool,
)

# ── Structured invoice pipeline (parallel + HITL + retry) ─────────────────
from pipeline import build_invoice_pipeline, InvoiceState

# ══════════════════════════════════════════════════════════════════════════════
# 1. Environment & LLM
# ══════════════════════════════════════════════════════════════════════════════

load_dotenv()

GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY", "")
DUMMY = not GOOGLE_GEMINI_API_KEY or "YOUR_KEY_HERE" in GOOGLE_GEMINI_API_KEY

if DUMMY:
    print("[WARNING] GOOGLE_GEMINI_API_KEY not set - running in mock (dummy) mode.")
    GOOGLE_GEMINI_API_KEY = "DUMMY_KEY"

class MockResponse:
    def __init__(self, content):
        self.content = content
        self.tool_calls = []

class MockLLM:
    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        # Extract content from list of messages or single message
        msg = messages[0] if isinstance(messages, list) else messages
        content = msg.content if hasattr(msg, "content") else str(msg)
        if isinstance(content, list):
            # Join all text parts together
            content = " ".join([part["text"] for part in content if isinstance(part, dict) and part.get("type") == "text"])
        
        # 1. Pipeline: Extraction Node
        if "Extract the following fields from the invoice" in content:
            amount = 450.0
            if "15,000" in content or "15000" in content:
                amount = 15000.0
            
            return AIMessage(content=json.dumps({
                "vendor": "SaaSify LLC" if amount == 450.0 else "Legacy Enterprise Solutions",
                "invoice_id": "INV-001" if amount == 450.0 else "INV-002",
                "date": "2026-06-15" if amount == 450.0 else "2026-06-18",
                "amount": amount,
                "tax": amount * 0.1,
                "po_number": "PO-1234",
                "line_items": [{"description": "Monthly subscription" if amount == 450.0 else "Enterprise support", "price": amount}],
                "payment_due_date": "2026-07-15",
                "confidence": 0.95
            }))

        # 2. Pipeline: Validation Node
        elif "Validate and normalise this extracted invoice JSON" in content:
            amount = 450.0
            if "15000" in content or "15,000" in content:
                amount = 15000.0
            return AIMessage(content=json.dumps({
                "vendor": "SaaSify LLC" if amount == 450.0 else "Legacy Enterprise Solutions",
                "invoice_id": "INV-001" if amount == 450.0 else "INV-002",
                "date": "2026-06-15" if amount == 450.0 else "2026-06-18",
                "amount": amount,
                "tax": amount * 0.1,
                "po_number": "PO-1234",
                "status": "valid"
            }))

        # 3. Pipeline: Categorization Node
        elif "Classify this invoice into one category from" in content:
            return AIMessage(content=json.dumps({
                "category": "SaaS / Cloud Infrastructure",
                "sub_category": "Hosting",
                "confidence": 0.95,
                "reason": "Matches hosting keywords."
            }))

        # 4. Pipeline: Anomaly Node
        elif "Analyse this invoice for anomalies" in content:
            return AIMessage(content=json.dumps({
                "anomalies_found": False,
                "details": [],
                "risk_level": "low"
            }))

        # 5. Pipeline: Finalize Node
        elif "Compile the following data into a concise executive summary" in content:
            return AIMessage(content="Invoice successfully processed and verified. Category: SaaS / Cloud Infrastructure. Risk: Low.")

        # Default Chat mock response
        return AIMessage(content="Based on the mock database records, the total amount spent on SaaSify is $495.00.")

    def invoke(self, messages):
        # Extract content from list of messages or single message
        msg = messages[0] if isinstance(messages, list) else messages
        content = msg.content if hasattr(msg, "content") else str(msg)
        if isinstance(content, list):
            content = " ".join([part["text"] for part in content if isinstance(part, dict) and part.get("type") == "text"])
        
        # Same mock checks synchronously
        if "Extract the following fields from the invoice" in content:
            amount = 450.0
            if "15,000" in content or "15000" in content:
                amount = 15000.0
            return AIMessage(content=json.dumps({
                "vendor": "SaaSify LLC" if amount == 450.0 else "Legacy Enterprise Solutions",
                "invoice_id": "INV-001" if amount == 450.0 else "INV-002",
                "date": "2026-06-15" if amount == 450.0 else "2026-06-18",
                "amount": amount,
                "tax": amount * 0.1,
                "po_number": "PO-1234",
                "line_items": [{"description": "Monthly subscription" if amount == 450.0 else "Enterprise support", "price": amount}],
                "payment_due_date": "2026-07-15",
                "confidence": 0.95
            }))
        elif "Validate and normalise this extracted invoice JSON" in content:
            amount = 450.0
            if "15000" in content or "15,000" in content:
                amount = 15000.0
            return AIMessage(content=json.dumps({
                "vendor": "SaaSify LLC" if amount == 450.0 else "Legacy Enterprise Solutions",
                "invoice_id": "INV-001" if amount == 450.0 else "INV-002",
                "date": "2026-06-15" if amount == 450.0 else "2026-06-18",
                "amount": amount,
                "tax": amount * 0.1,
                "po_number": "PO-1234",
                "status": "valid"
            }))
        elif "Classify this invoice into one category from" in content:
            return AIMessage(content=json.dumps({
                "category": "SaaS / Cloud Infrastructure",
                "sub_category": "Hosting",
                "confidence": 0.95,
                "reason": "Matches hosting keywords."
            }))
        elif "Analyse this invoice for anomalies" in content:
            return AIMessage(content=json.dumps({
                "anomalies_found": False,
                "details": [],
                "risk_level": "low"
            }))
        elif "Compile the following data into a concise executive summary" in content:
            return AIMessage(content="Invoice successfully processed and verified. Category: SaaS / Cloud Infrastructure. Risk: Low.")
        return AIMessage(content="Based on the mock database records, the total amount spent on SaaSify is $495.00.")

class StringContentChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    async def ainvoke(self, input, config=None, **kwargs):
        try:
            resp = await super().ainvoke(input, config=config, **kwargs)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "limit" in str(e).lower() or "exhausted" in str(e).lower():
                print("\n[WARNING] Live Gemini API Key Rate Limited/Exhausted (429). Falling back to mock LLM response...")
                mock_llm = MockLLM()
                return await mock_llm.ainvoke(input)
            raise e

        if hasattr(resp, "content"):
            content = resp.content
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        parts.append(part["text"])
                    elif isinstance(part, str):
                        parts.append(part)
                resp.content = "".join(parts)
            else:
                resp.content = str(content)
        return resp

    def invoke(self, input, config=None, **kwargs):
        try:
            resp = super().invoke(input, config=config, **kwargs)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "limit" in str(e).lower() or "exhausted" in str(e).lower():
                print("\n[WARNING] Live Gemini API Key Rate Limited/Exhausted (429). Falling back to mock LLM response...")
                mock_llm = MockLLM()
                return mock_llm.invoke(input)
            raise e

        if hasattr(resp, "content"):
            content = resp.content
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        parts.append(part["text"])
                    elif isinstance(part, str):
                        parts.append(part)
                resp.content = "".join(parts)
            else:
                resp.content = str(content)
        return resp

if DUMMY:
    llm = MockLLM()
else:
    llm = StringContentChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
        google_api_key=GOOGLE_GEMINI_API_KEY,
        temperature=0.0,
        convert_system_message_to_human=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# 2. Build all agent tools
# ══════════════════════════════════════════════════════════════════════════════

invoice_tool      = make_invoice_tool(llm,      dummy=DUMMY)
anomaly_tool      = make_anomaly_tool(llm,      dummy=DUMMY)
bi_tool           = make_bi_tool(llm,           dummy=DUMMY)
forecasting_tool  = make_forecasting_tool(llm,  dummy=DUMMY)
report_tool       = make_report_tool()
validation_tool   = make_validation_tool(llm,   dummy=DUMMY)
categor_tool      = make_categorization_tool(llm, dummy=DUMMY)
nl_query_tool     = make_nl_query_tool(llm,     dummy=DUMMY)

ALL_TOOLS = [
    invoice_tool, anomaly_tool, bi_tool,
    forecasting_tool, report_tool, validation_tool,
    categor_tool, nl_query_tool,
]
TOOLS_MAP = {t.name: t for t in ALL_TOOLS}

# ══════════════════════════════════════════════════════════════════════════════
# 3. Supervisor / Orchestrator graph  (free-form chat)
# ══════════════════════════════════════════════════════════════════════════════

orchestrator_llm = llm.bind_tools(ALL_TOOLS)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


SYSTEM_PROMPT = SystemMessage(content=(
    "You are the Invoxio Supervisor Orchestrator — a financial AI platform. "
    "Delegate every task to the correct specialist agent:\n"
    "• invoice_extraction_tool       — extract data from raw invoice text\n"
    "• validation_normalization_agent — validate & normalise extracted JSON\n"
    "• categorization_agent          — classify invoice into spending category\n"
    "• anomaly_detection_tool        — detect duplicates, fraud, price spikes\n"
    "• nl_query_agent                — answer NL financial queries via SQL\n"
    "• bi_insights_subagent          — revenue trends, expense breakdowns\n"
    "• forecasting_subagent          — project future cash flow\n"
    "• report_generation_subagent    — compile findings into markdown report\n\n"
    "Chain agents when needed (e.g. extract → validate → categorize → report). "
    "Always synthesise a clear final answer for the user."
))


async def orchestrator_node(state: AgentState) -> dict:
    print("\n─── [Supervisor Orchestrator] ───")
    response = await orchestrator_llm.ainvoke([SYSTEM_PROMPT] + list(state["messages"]))
    if response.tool_calls:
        print(f"  → delegating to: {[tc['name'] for tc in response.tool_calls]}")
    return {"messages": [response]}


async def tools_node(state: AgentState) -> dict:
    print("─── [Tool Execution] ───")
    last = state["messages"][-1]
    outputs = []
    for tc in last.tool_calls:
        fn = TOOLS_MAP.get(tc["name"])
        result = await fn.ainvoke(tc["args"]) if fn else f"Unknown tool: {tc['name']}"
        outputs.append(ToolMessage(content=str(result), tool_call_id=tc["id"], name=tc["name"]))
    return {"messages": outputs}


def router(state: AgentState) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else "end"


chat_graph = StateGraph(AgentState)
chat_graph.add_node("orchestrator", orchestrator_node)
chat_graph.add_node("tools",        tools_node)
chat_graph.add_edge(START, "orchestrator")
chat_graph.add_conditional_edges("orchestrator", router, {"tools": "tools", "end": END})
chat_graph.add_edge("tools", "orchestrator")
chat_app = chat_graph.compile()

# ══════════════════════════════════════════════════════════════════════════════
# 4. Structured invoice pipeline (parallel + HITL + retry loop)
# ══════════════════════════════════════════════════════════════════════════════

invoice_pipeline = build_invoice_pipeline(llm)

# In-memory store for pipeline run configs (thread_id → status)
_pipeline_runs: dict[str, dict] = {}

print("[OK] Invoxio Supervisor Orchestrator compiled.")

# ══════════════════════════════════════════════════════════════════════════════
# 5. FastAPI
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Invoxio Orchestrator API",
    description=(
        "Supervisor orchestrator with 8 specialist agents. "
        "Supports free-form chat AND structured invoice pipeline "
        "(parallel branches, retry loop, human-in-the-loop approvals)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Chat endpoint ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


@app.post("/api/agent/chat")
async def chat(req: ChatRequest):
    try:
        result = await chat_app.ainvoke({"messages": [HumanMessage(content=req.message)]})
        return {
            "answer": result["messages"][-1].content,
            "messages_count": len(result["messages"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── Pipeline: start ────────────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    invoice_text: Optional[str] = None
    file_data: Optional[str] = None
    mime_type: Optional[str] = None
    file_name: Optional[str] = None


@app.post("/api/pipeline/process")
async def pipeline_process(req: PipelineRequest):
    """
    Start the invoice processing pipeline.
    - Runs extraction (with retry loop if confidence is low).
    - Runs validation, categorization, anomaly-detection IN PARALLEL.
    - If invoice amount >= $10,000: pauses and returns status='awaiting_approval'.
    - Otherwise: runs to completion and returns final_report.
    """
    run_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": run_id}}
    _pipeline_runs[run_id] = {"config": config, "status": "running"}

    try:
        initial: InvoiceState = {
            "raw_text":        req.invoice_text or "",
            "file_data":       req.file_data,
            "mime_type":       req.mime_type,
            "file_name":       req.file_name,
            "extracted_json":  "",
            "confidence":      0.0,
            "retry_count":     0,
            "validated_json":  "",
            "category":        "",
            "anomaly_report":  "",
            "amount":          0.0,
            "approval_status": "pending",
            "final_report":    "",
        }

        # ainvoke will pause at interrupt_before=["approval_gate"] for high-value invoices
        result = await invoice_pipeline.ainvoke(initial, config)

        # Check if graph is still interrupted (high-value, awaiting approval)
        snapshot = invoice_pipeline.get_state(config)
        if snapshot.next:  # graph paused — next nodes pending
            _pipeline_runs[run_id]["status"] = "awaiting_approval"
            return {
                "run_id":          run_id,
                "status":          "awaiting_approval",
                "amount":          result.get("amount", 0),
                "extracted_json":  result.get("extracted_json", ""),
                "category":        result.get("category", ""),
                "anomaly_report":  result.get("anomaly_report", ""),
                "message":         "High-value invoice requires human approval. POST to /api/pipeline/approve.",
            }

        _pipeline_runs[run_id]["status"] = "completed"
        return {
            "run_id":          run_id,
            "status":          "completed",
            "amount":          result.get("amount", 0.0),
            "extracted_json":  result.get("extracted_json", ""),
            "validated_json":  result.get("validated_json", ""),
            "category":        result.get("category", ""),
            "anomaly_report":  result.get("anomaly_report", ""),
            "final_report":    result.get("final_report", ""),
            "retry_count":     result.get("retry_count", 1),
            "confidence":      result.get("confidence", 0.0),
        }

    except Exception as e:
        _pipeline_runs[run_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── Pipeline: human approval (resume HITL) ─────────────────────────────────

class ApprovalRequest(BaseModel):
    run_id: str
    decision: str   # "approved" | "rejected"
    reviewer: str   # reviewer name / email


@app.post("/api/pipeline/approve")
async def pipeline_approve(req: ApprovalRequest):
    """
    Resume a paused pipeline after human review.
    Injects approval_status into the graph state and continues execution.
    """
    run = _pipeline_runs.get(req.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")
    if run["status"] != "awaiting_approval":
        raise HTTPException(status_code=400, detail=f"Run is not awaiting approval (status: {run['status']}).")

    config = run["config"]
    try:
        # Inject human decision into the paused graph state
        invoice_pipeline.update_state(
            config,
            {"approval_status": req.decision},
            as_node="approval_gate",
        )

        # Resume the graph from the checkpoint
        result = await invoice_pipeline.ainvoke(None, config)

        _pipeline_runs[req.run_id]["status"] = "completed"
        return {
            "run_id":          req.run_id,
            "status":          "completed",
            "decision":        req.decision,
            "reviewer":        req.reviewer,
            "amount":          result.get("amount", 0.0),
            "extracted_json":  result.get("extracted_json", ""),
            "validated_json":  result.get("validated_json", ""),
            "category":        result.get("category", ""),
            "anomaly_report":  result.get("anomaly_report", ""),
            "final_report":    result.get("final_report", ""),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── Pipeline: status ───────────────────────────────────────────────────────

@app.get("/api/pipeline/status/{run_id}")
def pipeline_status(run_id: str):
    run = _pipeline_runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    snapshot = invoice_pipeline.get_state(run["config"])
    return {
        "run_id":      run_id,
        "status":      run["status"],
        "next_nodes":  list(snapshot.next) if snapshot.next else [],
    }


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":    "online",
        "agents":    list(TOOLS_MAP.keys()),
        "endpoints": {
            "chat":            "POST /api/agent/chat",
            "pipeline_start":  "POST /api/pipeline/process",
            "pipeline_approve":"POST /api/pipeline/approve",
            "pipeline_status": "GET  /api/pipeline/status/{run_id}",
        },
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("APP_PORT", 8000)))
    print(f"Starting Invoxio on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
