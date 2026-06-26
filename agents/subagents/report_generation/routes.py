"""Report Generation Routes — POST /api/report/generate"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from subagents.report_generation.graph import report_graph

router = APIRouter()

class ReportRequest(BaseModel):
    tenant_id:    str = "demo-tenant"
    report_type:  str = Field(default="monthly_summary", description="monthly_summary|quarterly_bi|overdue_invoices|custom")
    period_label: str = Field(default="June 2024")
    date_from:    str = Field(default="2024-06-01")
    date_to:      str = Field(default="2024-06-30")
    recipients:   List[str] = Field(default=[], description="Email addresses")
    channels:     List[str] = Field(default=["save"], description="email|slack|save")
    custom_prompt: Optional[str] = None

@router.post("/generate")
async def generate_report(req: ReportRequest):
    """Generate a full business report as PDF and distribute via email/Slack."""
    print(f"\n[POST /report/generate] type={req.report_type} | period={req.period_label}")
    initial = {
        "tenant_id":req.tenant_id,"report_type":req.report_type,
        "period_label":req.period_label,"date_from":req.date_from,"date_to":req.date_to,
        "recipients":req.recipients,"channels":req.channels,"custom_prompt":req.custom_prompt,
        "bi_data":{},"anomaly_summary":{},"report_sections":[],"executive_summary":"",
        "pdf_bytes":None,"pdf_filename":"","distribution_results":[],"error":None,
    }
    try:
        result = await report_graph.ainvoke(initial)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "success":              True,
        "report_type":          req.report_type,
        "period":               req.period_label,
        "pdf_filename":         result.get("pdf_filename"),
        "executive_summary":    result.get("executive_summary"),
        "sections":             [{"title":s["title"],"content":s["content"][:300]+"..."} for s in result.get("report_sections",[])],
        "distribution_results": result.get("distribution_results",[]),
    }

@router.get("/health")
async def report_health():
    return {"status":"healthy","pipeline":["gather_data","generate_content","render_pdf","distribute"]}
