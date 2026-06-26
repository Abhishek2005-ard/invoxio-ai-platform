"""
Anomaly Detection Routes — FastAPI endpoints

POST /api/anomaly/scan          → Run full anomaly detection on provided invoices
POST /api/anomaly/scan-tenant   → Fetch all tenant invoices from DB and scan
GET  /api/anomaly/health        → Health check
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from subagents.anomaly_detection.graph import anomaly_graph

router = APIRouter()


# Request Models

class InvoiceScanRequest(BaseModel):
    """Scan a provided list of invoices for anomalies."""
    tenant_id: str = Field(default="demo-tenant")
    invoices:  List[Dict[str, Any]] = Field(
        default=[],
        description="List of invoice dicts. Leave empty to use built-in sample data.",
    )


# POST /scan

@router.post("/scan")
async def scan_invoices(request: InvoiceScanRequest):
    """
    Run the full Anomaly Detection pipeline on a list of invoices.

    Pipeline:
      ingest_invoices → detect_duplicates → detect_fraud → score_outliers → generate_report

    Returns a complete AnomalyReport with:
      - Duplicate pairs (exact, fuzzy, amount+vendor)
      - Fraud signals (rule-based + AI-detected)
      - Outlier scores (Z-score + IQR)
      - AI narrative and recommendations
    """
    print(f"\n[POST /anomaly/scan] tenant={request.tenant_id} | "
          f"invoices={len(request.invoices)} (0 = use sample data)")

    initial_state = {
        "tenant_id":       request.tenant_id,
        "input_invoices":  request.invoices,   # empty → ingest_node uses sample data
        "invoices":        [],
        "invoice_count":   0,
        "amount_stats":    {},
        "duplicates":      [],
        "duplicate_count": 0,
        "fraud_signals":   [],
        "fraud_count":     0,
        "outlier_scores":  [],
        "outlier_count":   0,
        "report":          None,
        "ai_narrative":    "",
        "recommendations": [],
        "error":           None,
    }

    try:
        result = await anomaly_graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly scan failed: {str(e)}")

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    report = result.get("report", {})

    return JSONResponse(content={
        "success": True,
        "report":  report,
    })


# GET /health

@router.get("/health")
async def anomaly_health():
    return {
        "status":   "healthy",
        "pipeline": [
            "ingest_invoices",
            "detect_duplicates",
            "detect_fraud",
            "score_outliers",
            "generate_report",
        ],
    }
