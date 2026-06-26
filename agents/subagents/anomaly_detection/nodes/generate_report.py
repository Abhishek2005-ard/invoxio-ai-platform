"""
Node 5 — generate_report

Responsibility:
  - Consolidate ALL findings: duplicates + fraud signals + outlier scores
  - Compute summary stats (total at-risk amount, critical count, etc.)
  - Ask Gemini to write a plain-English narrative of the findings
  - Produce actionable recommendations ranked by risk
  - Return the final AnomalyReport dict

Pipeline: ingest_invoices → detect_duplicates → detect_fraud → score_outliers → [generate_report]
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from langchain_core.messages import SystemMessage, HumanMessage
from config.gemini import llm_think
from subagents.anomaly_detection.state import AnomalyDetectionState

NARRATIVE_PROMPT = """You are a financial risk analyst writing a concise executive summary.

Based on the anomaly detection results below, write a clear 3-5 sentence summary covering:
1. The overall risk level of this invoice dataset
2. The most serious findings (duplicates, fraud signals, outliers)
3. The most urgent action required

Be direct and specific — include vendor names, amounts, and invoice IDs where relevant.
Write for a CFO or finance manager, not a technical audience.
"""

RECOMMENDATIONS_PROMPT = """Based on these anomaly detection findings, list the top 5 most important 
actionable recommendations, ordered by urgency (most urgent first).

Each recommendation must be:
- Specific (mention invoice IDs, vendors, amounts)  
- Actionable (what to DO, not just what to investigate)
- Brief (one sentence each)

Output ONLY a JSON array of strings:
["Recommendation 1", "Recommendation 2", ...]
"""


async def generate_report_node(state: AnomalyDetectionState) -> dict:
    """
    Compiles all detection results into a final structured AnomalyReport.

    Reads:  invoices, invoice_count, duplicates, fraud_signals, outlier_scores, tenant_id
    Writes: report, ai_narrative, recommendations
    """
    tenant_id      = state["tenant_id"]
    invoices       = state.get("invoices", [])
    duplicates     = state.get("duplicates", [])
    fraud_signals  = state.get("fraud_signals", [])
    outlier_scores = state.get("outlier_scores", [])

    print(f"\n[generate_report] Compiling final anomaly report...")

    # Compute summary stats
    critical_count = sum(
        1 for s in fraud_signals if s.get("risk_level") == "critical"
    ) + sum(
        1 for d in duplicates if d.get("risk_level") == "high"
    )

    outlier_invoices = [s for s in outlier_scores if s.get("is_outlier")]

    # Total amount at risk = outlier amounts + high-risk fraud amounts + duplicates
    at_risk_ids = set()
    for s in fraud_signals:
        if s.get("risk_level") in ("high", "critical"):
            at_risk_ids.add(s["invoice_id"])
    for d in duplicates:
        at_risk_ids.add(d["invoice_id_a"])
    for o in outlier_invoices:
        at_risk_ids.add(o["invoice_id"])

    total_at_risk = sum(
        inv["amount"] for inv in invoices if inv["id"] in at_risk_ids
    )

    summary = {
        "total_invoices_analyzed": len(invoices),
        "duplicate_pairs_found":   len(duplicates),
        "fraud_signals_found":     len(fraud_signals),
        "outliers_found":          len(outlier_invoices),
        "critical_alerts":         critical_count,
        "total_amount_at_risk":    round(total_at_risk, 2),
    }

    print(f"  Summary: {json.dumps(summary)}")

    # Build context for Gemini
    context = _build_context(summary, duplicates, fraud_signals, outlier_invoices)

    # Gemini: plain-English narrative
    narrative = await _get_narrative(context)

    # Gemini: ranked recommendations
    recommendations = await _get_recommendations(context)

    print(f"[generate_report] Report complete — "
          f"{critical_count} critical alerts | "
          f"${total_at_risk:,.2f} at risk")

    report = {
        "tenant_id":       tenant_id,
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "summary":         summary,
        "duplicates":      duplicates,
        "fraud_signals":   fraud_signals,
        "outliers":        outlier_invoices,
        "ai_narrative":    narrative,
        "recommendations": recommendations,
    }

    return {
        "report":          report,
        "ai_narrative":    narrative,
        "recommendations": recommendations,
    }


async def _get_narrative(context: str) -> str:
    """Ask Gemini to write the executive summary narrative."""
    try:
        response = await llm_think.ainvoke([
            SystemMessage(content=NARRATIVE_PROMPT),
            HumanMessage(content=context),
        ])
        return response.content if isinstance(response.content, str) else "Narrative generation failed."
    except Exception as e:
        print(f"  Warning: Narrative generation error: {e}")
        return "Automated narrative unavailable — review raw findings below."


async def _get_recommendations(context: str) -> List[str]:
    """Ask Gemini to produce ranked, actionable recommendations."""
    try:
        response = await llm_think.ainvoke([
            SystemMessage(content=RECOMMENDATIONS_PROMPT),
            HumanMessage(content=context),
        ])
        raw = response.content if isinstance(response.content, str) else "[]"
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(cleaned)
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"  Warning: Recommendations error: {e}")
        return ["Review flagged invoices manually.", "Contact vendors with multiple duplicate submissions."]


def _build_context(summary: dict, duplicates: list, fraud_signals: list, outliers: list) -> str:
    """Builds a concise text summary of all findings for Gemini input."""
    lines = [
        f"ANOMALY DETECTION RESULTS",
        f"Total invoices analyzed: {summary['total_invoices_analyzed']}",
        f"Duplicate pairs found: {summary['duplicate_pairs_found']}",
        f"Fraud signals found: {summary['fraud_signals_found']}",
        f"Outliers found: {summary['outliers_found']}",
        f"Critical alerts: {summary['critical_alerts']}",
        f"Total amount at risk: ${summary['total_amount_at_risk']:,.2f}",
        "",
        "TOP DUPLICATES:",
    ]
    for d in duplicates[:5]:
        lines.append(f"  - [{d['match_type'].upper()}] {d['invoice_id_a']} ↔ {d['invoice_id_b']} "
                     f"| vendor: {d.get('vendor_a','')} | amount: ${d.get('amount_a',0):,.2f} "
                     f"| risk: {d['risk_level']}")

    lines.append("\nTOP FRAUD SIGNALS:")
    for s in sorted(fraud_signals, key=lambda x: x.get("confidence", 0), reverse=True)[:5]:
        lines.append(f"  - [{s['risk_level'].upper()}] {s['invoice_id']} | {s['signal_type']} "
                     f"| confidence: {s.get('confidence',0):.0%} | {s['description']}")

    lines.append("\nTOP OUTLIERS:")
    for o in sorted(outliers, key=lambda x: abs(x.get("z_score", 0)), reverse=True)[:5]:
        lines.append(f"  - {o['invoice_id']} | amount: ${o['amount']:,.2f} "
                     f"| z-score: {o['z_score']:.2f} | {o['outlier_reason']}")

    return "\n".join(lines)
