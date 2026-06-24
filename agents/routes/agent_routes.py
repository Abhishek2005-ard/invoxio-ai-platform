"""
Agent Routes — FastAPI endpoints for the Master Orchestrator Agent

Endpoints:
  POST /api/agent/chat          → Standard JSON response
  POST /api/agent/chat/stream   → SSE streaming response (token-by-token)
  GET  /api/agent/health        → Health check
"""

import uuid
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
from langchain_core.messages import HumanMessage

from graph.orchestrator import orchestrator
from config.settings import settings

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    tenant_id: str = "demo-tenant"
    user_id: str = "demo-user"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    plan: str
    iterations: int
    observations_count: int


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Run the Master Orchestrator (full ReAct loop) and return the final answer.
    Blocks until the agent completes all iterations.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Build the initial state
    initial_state = {
        "messages":           [HumanMessage(content=request.message)],
        "tenant_id":          request.tenant_id,
        "user_id":            request.user_id,
        "session_id":         session_id,
        "plan":               "",
        "steps":              [],
        "current_step_index": 0,
        "tool_name":          "",
        "tool_input":         {},
        "observations":       [],
        "reflection":         "",
        "is_complete":        False,
        "final_answer":       "",
        "iteration":          0,
        "max_iterations":     settings.agent_max_iterations,
        "error":              None,
    }

    try:
        result = await orchestrator.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return ChatResponse(
        session_id=session_id,
        answer=result.get("final_answer", "I could not complete the task."),
        plan=result.get("plan", ""),
        iterations=result.get("iteration", 0),
        observations_count=len(result.get("observations", [])),
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Run the Master Orchestrator and stream node-level updates via SSE.

    SSE event format:
      event: node_update   → when a node starts/completes
      event: token         → final answer tokens (streaming)
      event: done          → final event with session_id
    """
    session_id = request.session_id or str(uuid.uuid4())

    initial_state = {
        "messages":           [HumanMessage(content=request.message)],
        "tenant_id":          request.tenant_id,
        "user_id":            request.user_id,
        "session_id":         session_id,
        "plan":               "",
        "steps":              [],
        "current_step_index": 0,
        "tool_name":          "",
        "tool_input":         {},
        "observations":       [],
        "reflection":         "",
        "is_complete":        False,
        "final_answer":       "",
        "iteration":          0,
        "max_iterations":     settings.agent_max_iterations,
        "error":              None,
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        """Yields SSE-formatted strings for each graph node update."""
        try:
            # Stream each node update as it completes
            async for event in orchestrator.astream(initial_state, stream_mode="updates"):
                for node_name, node_output in event.items():
                    payload = {
                        "node": node_name,
                        "iteration": node_output.get("iteration", 0),
                        "plan": node_output.get("plan", ""),
                        "tool": node_output.get("tool_name", ""),
                        "is_complete": node_output.get("is_complete", False),
                    }
                    yield f"event: node_update\ndata: {json.dumps(payload)}\n\n"

                    # Stream the final answer when reflect is done
                    if node_name == "reflect" and node_output.get("is_complete"):
                        answer = node_output.get("final_answer", "")
                        # Simulate token streaming on the final answer
                        words = answer.split(" ")
                        for word in words:
                            yield f"event: token\ndata: {json.dumps({'text': word + ' '})}\n\n"

            yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def agent_health():
    return {
        "status": "healthy",
        "model": settings.gemini_model,
        "max_iterations": settings.agent_max_iterations,
    }
