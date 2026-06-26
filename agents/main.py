"""
Invoxio — AI Agent Entry Point
FastAPI server that exposes the Master Orchestrator (ReAct loop) via REST + SSE
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load .env before importing anything else
load_dotenv()

from config.settings import settings
from routes.agent_routes import router as agent_router
from subagents.invoice_extraction.routes import router as invoice_router
from subagents.anomaly_detection.routes import router as anomaly_router
from subagents.bi_insights.routes import router as bi_router
from subagents.report_generation.routes import router as report_router
from subagents.forecasting.routes import router as forecast_router

# FastAPI App
app = FastAPI(
    title="Invoxio AI Agent",
    description=(
        "Master Orchestrator Agent powered by LangChain + LangGraph + Google Gemini.\n\n"
        "ReAct Loop: **THINK → ACT → OBSERVE → REFLECT**\n\n"
        "Plans tasks · routes to sub-agents · merges results · reflects"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (allow React frontend at localhost:5173 or :3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(agent_router,   prefix="/api/agent",    tags=["Master Orchestrator"])
app.include_router(invoice_router, prefix="/api/invoice",  tags=["Invoice Extraction"])
app.include_router(anomaly_router, prefix="/api/anomaly",  tags=["Anomaly Detection"])
app.include_router(bi_router,      prefix="/api/bi",       tags=["BI Insights"])
app.include_router(report_router,  prefix="/api/report",   tags=["Report Generation"])
app.include_router(forecast_router,prefix="/api/forecast", tags=["Forecasting"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "service":        "Invoxio AI Agent",
        "status":         "running",
        "model":          settings.gemini_model,
        "version":        "1.0.0",
        "react_loop":     "THINK → ACT → OBSERVE → REFLECT",
        "docs":           "/docs",
        "chat_endpoint":  "/api/agent/chat",
        "stream_endpoint":"/api/agent/chat/stream",
    }


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "healthy"}


# Startup Event
@app.on_event("startup")
async def on_startup():
    print("\n" + "="*55)
    print("  Invoxio AI Agent")
    print(f"  Model:      {settings.gemini_model}")
    print(f"  Max iters:  {settings.agent_max_iterations}")
    print(f"  Env:        {settings.app_env}")
    print(f"  Docs:       http://localhost:{settings.app_port}/docs")
    print("="*55 + "\n")


# Entry Point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=True,
        reload_dirs=["./"],
    )
