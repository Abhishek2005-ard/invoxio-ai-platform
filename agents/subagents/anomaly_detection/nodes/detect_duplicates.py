"""
Node 2 — detect_duplicates

Responsibility:
  - Find EXACT duplicates: same invoice_number
  - Find FUZZY duplicates: same vendor + amount + date (within ±3 days)
  - Find AMOUNT+VENDOR duplicates: same vendor + amount (different dates)
  - Score each pair with a match_score 0.0–1.0
  - Flag risk level based on how suspicious the match is

Pipeline: ingest_invoices → [detect_duplicates] → detect_fraud → score_outliers → generate_report
"""

from itertools import combinations
from datetime import datetime, timedelta
from typing import Any, Dict, List
from subagents.anomaly_detection.state import AnomalyDetectionState


async def detect_duplicates_node(state: AnomalyDetectionState) -> dict:
    """
    Scans all invoice pairs for duplicates using 3 strategies.

    Reads:  invoices
    Writes: duplicates, duplicate_count
    """
    invoices = state.get("invoices", [])
    print(f"\n[detect_duplicates] Scanning {len(invoices)} invoices for duplicates...")

    duplicates: List[Dict[str, Any]] = []

    # Compare every pair of invoices
    for inv_a, inv_b in combinations(invoices, 2):

        # Strategy 1: Exact invoice_number match
        if (inv_a["invoice_number"]
                and inv_b["invoice_number"]
                and inv_a["invoice_number"] == inv_b["invoice_number"]):
            duplicates.append(_make_duplicate(
                inv_a, inv_b,
                match_type="exact",
                match_score=1.0,
                shared=["invoice_number"],
                risk="high",
                note="Identical invoice numbers — likely duplicate submission",
            ))
            continue

        # Strategy 2: Same vendor + amount + close dates (fuzzy)
        same_vendor = _vendor_similarity(inv_a["vendor_name"], inv_b["vendor_name"]) > 0.85
        same_amount = inv_a["amount"] > 0 and abs(inv_a["amount"] - inv_b["amount"]) < 0.01
        close_dates = _dates_within_days(inv_a["invoice_date"], inv_b["invoice_date"], days=3)

        if same_vendor and same_amount and close_dates:
            shared = ["vendor_name", "amount"]
            if close_dates:
                shared.append("invoice_date (±3 days)")
            duplicates.append(_make_duplicate(
                inv_a, inv_b,
                match_type="fuzzy",
                match_score=0.92,
                shared=shared,
                risk="high",
                note="Same vendor, same amount, submitted within 3 days — likely double-billing",
            ))
            continue

        # Strategy 3: Same vendor + same amount (different dates)
        if same_vendor and same_amount:
            duplicates.append(_make_duplicate(
                inv_a, inv_b,
                match_type="amount_vendor",
                match_score=0.75,
                shared=["vendor_name", "amount"],
                risk="medium",
                note="Same vendor and amount on different dates — possible recurring charge, review needed",
            ))

    print(f"[detect_duplicates] Found {len(duplicates)} duplicate pair(s)")
    for d in duplicates:
        print(f"  Warning: [{d['match_type'].upper()}] {d['invoice_id_a']} ↔ {d['invoice_id_b']} "
              f"| score: {d['match_score']} | risk: {d['risk_level']}")

    return {
        "duplicates":      duplicates,
        "duplicate_count": len(duplicates),
    }


# Helpers

def _make_duplicate(a, b, match_type, match_score, shared, risk, note) -> dict:
    return {
        "invoice_id_a":  a["id"],
        "invoice_id_b":  b["id"],
        "match_type":    match_type,
        "match_score":   match_score,
        "shared_fields": shared,
        "risk_level":    risk,
        "recommendation": note,
        # Extra context
        "vendor_a":  a["vendor_name"],
        "amount_a":  a["amount"],
        "amount_b":  b["amount"],
        "date_a":    a["invoice_date"],
        "date_b":    b["invoice_date"],
    }


def _vendor_similarity(a: str, b: str) -> float:
    """Simple character overlap similarity (0–1). No external libs needed."""
    if not a or not b:
        return 0.0
    a_lower, b_lower = a.lower().strip(), b.lower().strip()
    if a_lower == b_lower:
        return 1.0
    # Jaccard similarity on character bigrams
    def bigrams(s): return {s[i:i+2] for i in range(len(s) - 1)}
    set_a, set_b = bigrams(a_lower), bigrams(b_lower)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _dates_within_days(date_a: str, date_b: str, days: int = 3) -> bool:
    """Returns True if two date strings are within N days of each other."""
    try:
        dt_a = datetime.fromisoformat(date_a)
        dt_b = datetime.fromisoformat(date_b)
        return abs((dt_a - dt_b).days) <= days
    except Exception:
        return False
