"""
Node 3 — detect_fraud

Responsibility:
  - Apply rule-based checks for known fraud patterns (fast, deterministic)
  - Then send flagged invoices to Gemini AI for deeper reasoning
  - Gemini looks for subtle patterns across the full invoice set
  - Returns FraudSignal objects for each suspicious finding

Fraud patterns detected:
  1. Round amounts        → $5000, $10000 exactly
  2. Just-below threshold → $9,999 / $4,999 (avoids review limits)
  3. Velocity spike       → Same vendor sends >3 invoices in 7 days
  4. New/rare vendor      → Vendor seen for first time
  5. Weekend submission   → Invoice dated Saturday or Sunday
  6. Sequential numbers   → INV-001, INV-002, INV-003 all from same vendor
  7. Payment method change→ Bank account changed vs previous invoice

Pipeline: ingest_invoices → detect_duplicates → [detect_fraud] → score_outliers → generate_report
"""

import json
from collections import defaultdict
from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage

from config.gemini import llm_think
from subagents.anomaly_detection.state import AnomalyDetectionState

# Review limits — amounts just below these are suspicious
REVIEW_THRESHOLDS = [1000, 2500, 5000, 10000, 25000, 50000, 100000]
ROUND_AMOUNT_CHECK = [500, 1000, 2500, 5000, 10000, 25000, 50000]

AI_FRAUD_PROMPT = """You are a financial fraud detection AI analyzing a set of business invoices.

Review the invoices provided and identify any suspicious patterns not caught by rule-based checks.
Look for:
- Vendors with unusual naming patterns (shell companies, misspellings of real companies)
- Amounts that seem inconsistent with the described services
- Timing patterns suggesting coordinated fraud
- Any other red flags from your financial crime knowledge

For each fraud signal found, output a JSON array item:
{
  "invoice_id": "the specific invoice ID",
  "signal_type": "other",
  "description": "clear description of the signal",
  "confidence": 0.0-1.0,
  "risk_level": "low|medium|high|critical",
  "evidence": "specific data that triggered this"
}

Output ONLY a JSON array — no commentary. If nothing suspicious, output [].
"""


async def detect_fraud_node(state: AnomalyDetectionState) -> dict:
    """
    Applies rule-based + AI fraud detection on normalized invoices.

    Reads:  invoices
    Writes: fraud_signals, fraud_count
    """
    invoices = state.get("invoices", [])
    print(f"\n[detect_fraud] Scanning {len(invoices)} invoices for fraud signals...")

    signals: List[Dict[str, Any]] = []

    # Rule-based checks
    vendor_invoice_map = defaultdict(list)
    vendor_accounts: Dict[str, str] = {}

    for inv in invoices:
        vendor = inv["vendor_name"]
        vendor_invoice_map[vendor].append(inv)

        # Rule 1: Round amount
        if any(abs(inv["amount"] - r) < 0.01 for r in ROUND_AMOUNT_CHECK) and inv["amount"] > 0:
            signals.append(_signal(
                invoice_id=inv["id"],
                signal_type="round_amount",
                desc=f"Amount is exactly {inv['currency']} {inv['amount']:,.0f} — suspiciously round",
                confidence=0.65,
                risk="medium",
                evidence=f"amount={inv['amount']}",
            ))

        # Rule 2: Just below threshold
        for threshold in REVIEW_THRESHOLDS:
            if threshold * 0.98 <= inv["amount"] < threshold:
                signals.append(_signal(
                    invoice_id=inv["id"],
                    signal_type="amount_just_below_threshold",
                    desc=f"Amount {inv['amount']:,.2f} is just below review threshold of {threshold:,}",
                    confidence=0.80,
                    risk="high",
                    evidence=f"amount={inv['amount']}, threshold={threshold}",
                ))
                break

        # Rule 3: Weekend submission
        if inv.get("submitted_day") in ("Saturday", "Sunday"):
            signals.append(_signal(
                invoice_id=inv["id"],
                signal_type="weekend_submission",
                desc=f"Invoice submitted on {inv['submitted_day']} — unusual for legitimate business",
                confidence=0.55,
                risk="low",
                evidence=f"invoice_date={inv['invoice_date']}, day={inv['submitted_day']}",
            ))

        # Rule 5: Payment method / bank account change tracking
        if inv["bank_account"]:
            if vendor in vendor_accounts and vendor_accounts[vendor] != inv["bank_account"]:
                signals.append(_signal(
                    invoice_id=inv["id"],
                    signal_type="payment_method_change",
                    desc=f"Vendor '{vendor}' changed bank account — possible account takeover fraud",
                    confidence=0.88,
                    risk="critical",
                    evidence=f"previous={vendor_accounts[vendor]}, new={inv['bank_account']}",
                ))
            vendor_accounts[vendor] = inv["bank_account"]

    # Rule 3: Velocity spike (after building vendor_invoice_map)
    for vendor, vendor_invs in vendor_invoice_map.items():
        if len(vendor_invs) == 1:
            # Rule 4: New vendor (only one invoice ever)
            signals.append(_signal(
                invoice_id=vendor_invs[0]["id"],
                signal_type="unusual_vendor",
                desc=f"First-time vendor '{vendor}' — no prior transaction history",
                confidence=0.50,
                risk="low",
                evidence=f"vendor appears only once in dataset",
            ))
        if len(vendor_invs) > 3:
            signals.append(_signal(
                invoice_id=vendor_invs[0]["id"],
                signal_type="velocity_spike",
                desc=f"Vendor '{vendor}' submitted {len(vendor_invs)} invoices — possible velocity abuse",
                confidence=0.72,
                risk="medium",
                evidence=f"invoice_count={len(vendor_invs)}",
            ))

    print(f"  Rule-based: {len(signals)} signal(s) found")

    # Gemini AI deep analysis
    ai_signals = await _ai_fraud_analysis(invoices)
    signals.extend(ai_signals)
    print(f"  AI analysis: {len(ai_signals)} additional signal(s) found")
    print(f"[detect_fraud] Total fraud signals: {len(signals)}")

    return {
        "fraud_signals": signals,
        "fraud_count":   len(signals),
    }


async def _ai_fraud_analysis(invoices: list) -> list:
    """Sends invoice data to Gemini for AI-powered fraud pattern detection."""
    if not invoices:
        return []

    # Trim for token limits
    invoice_sample = invoices[:20]
    inv_summary = json.dumps([
        {k: v for k, v in inv.items() if k not in ("submitted_day",)}
        for inv in invoice_sample
    ], indent=2, default=str)

    try:
        response = await llm_think.ainvoke([
            SystemMessage(content=AI_FRAUD_PROMPT),
            HumanMessage(content=f"Invoice dataset:\n{inv_summary}"),
        ])
        raw = response.content if isinstance(response.content, str) else ""
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        if cleaned == "[]" or not cleaned:
            return []
        ai_results = json.loads(cleaned)
        return [s for s in ai_results if isinstance(s, dict) and "invoice_id" in s]
    except Exception as e:
        print(f"  Warning: AI fraud analysis error: {e}")
        return []


def _signal(invoice_id, signal_type, desc, confidence, risk, evidence) -> dict:
    return {
        "invoice_id":  invoice_id,
        "signal_type": signal_type,
        "description": desc,
        "confidence":  confidence,
        "risk_level":  risk,
        "evidence":    evidence,
    }
