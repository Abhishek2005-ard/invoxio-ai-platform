"""
Node 1 — ingest_invoices

Responsibility:
  - Accept raw invoice list (from API) OR fetch from MongoDB
  - Normalize fields: ensure amount is float, dates are strings, IDs exist
  - Compute statistical baseline: mean, std, median, min, max of amounts
  - This baseline is used by score_outliers for Z-score calculation

Pipeline: [ingest_invoices] → detect_duplicates → detect_fraud → score_outliers → generate_report
"""

import statistics
import uuid
from typing import Any, Dict, List
from subagents.anomaly_detection.state import AnomalyDetectionState


async def ingest_invoices_node(state: AnomalyDetectionState) -> dict:
    """
    Normalizes invoices and computes the statistical baseline.

    Reads:  input_invoices, tenant_id
    Writes: invoices, invoice_count, amount_stats
    """
    raw = state.get("input_invoices", [])
    tenant_id = state["tenant_id"]

    print(f"\n📥 [ingest_invoices] Processing {len(raw)} invoices for tenant: {tenant_id}")

    if not raw:
        # ── Stub: load sample invoices when none are passed ───────────────
        print("  ℹ️  No invoices provided — using sample dataset")
        raw = _get_sample_invoices(tenant_id)

    # ── Normalize each invoice ────────────────────────────────────────────
    invoices: List[Dict[str, Any]] = []
    for inv in raw:
        normalized = {
            "id":             inv.get("id") or inv.get("_id") or str(uuid.uuid4()),
            "invoice_number": str(inv.get("invoice_number", "")),
            "vendor_name":    str(inv.get("vendor", {}).get("name", "") if isinstance(inv.get("vendor"), dict) else inv.get("vendor_name", "")),
            "client_name":    str(inv.get("client", {}).get("name", "") if isinstance(inv.get("client"), dict) else inv.get("client_name", "")),
            "amount":         _to_float(inv.get("total_amount") or inv.get("amount", 0)),
            "invoice_date":   str(inv.get("invoice_date", "")),
            "due_date":       str(inv.get("due_date", "")),
            "status":         str(inv.get("status", "unpaid")),
            "payment_method": str(inv.get("payment_method", "")),
            "bank_account":   str(inv.get("bank_account", "")),
            "line_item_count": len(inv.get("line_items", [])),
            "currency":       str(inv.get("currency", "USD")),
            "submitted_day":  _day_of_week(inv.get("invoice_date", "")),
        }
        invoices.append(normalized)

    # ── Compute amount statistics ─────────────────────────────────────────
    amounts = [inv["amount"] for inv in invoices if inv["amount"] > 0]
    if len(amounts) >= 2:
        mean   = statistics.mean(amounts)
        std    = statistics.stdev(amounts)
        median = statistics.median(amounts)
    elif len(amounts) == 1:
        mean, std, median = amounts[0], 0.0, amounts[0]
    else:
        mean = std = median = 0.0

    amount_stats = {
        "mean":   round(mean, 2),
        "std":    round(std, 2),
        "median": round(median, 2),
        "min":    round(min(amounts, default=0), 2),
        "max":    round(max(amounts, default=0), 2),
        "count":  len(amounts),
        # IQR bounds for outlier detection
        "q1":     round(_percentile(sorted(amounts), 25), 2),
        "q3":     round(_percentile(sorted(amounts), 75), 2),
    }

    print(f"✅ [ingest_invoices] {len(invoices)} normalized | "
          f"Amounts — mean: {amount_stats['mean']}, std: {amount_stats['std']}, "
          f"range: [{amount_stats['min']}, {amount_stats['max']}]")

    return {
        "invoices":      invoices,
        "invoice_count": len(invoices),
        "amount_stats":  amount_stats,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_float(v) -> float:
    """Safely converts any value to float."""
    try:
        if isinstance(v, str):
            v = v.replace("$", "").replace(",", "").replace("₹", "").strip()
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _day_of_week(date_str: str) -> str:
    """Returns day name (e.g. 'Saturday') from a date string."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(str(date_str))
        return dt.strftime("%A")
    except Exception:
        return "Unknown"


def _percentile(sorted_data: list, pct: float) -> float:
    """Simple percentile calculation without numpy."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * pct / 100
    f, c = int(k), int(k) + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def _get_sample_invoices(tenant_id: str) -> list:
    """Returns sample invoice data for development/demo."""
    return [
        {"id": "INV-001", "invoice_number": "2024-001", "vendor": {"name": "Acme Corp"},   "client": {"name": "Beta Ltd"},  "total_amount": 5000,   "invoice_date": "2024-03-15", "status": "paid"},
        {"id": "INV-002", "invoice_number": "2024-002", "vendor": {"name": "Acme Corp"},   "client": {"name": "Beta Ltd"},  "total_amount": 5000,   "invoice_date": "2024-03-15", "status": "paid"},   # ← Duplicate
        {"id": "INV-003", "invoice_number": "2024-003", "vendor": {"name": "XYZ Traders"}, "client": {"name": "Beta Ltd"},  "total_amount": 10000,  "invoice_date": "2024-03-16", "status": "unpaid"},  # ← Round amount
        {"id": "INV-004", "invoice_number": "2024-004", "vendor": {"name": "New Vendor"},  "client": {"name": "Beta Ltd"},  "total_amount": 9999,   "invoice_date": "2024-03-17", "status": "unpaid"},  # ← Just below threshold
        {"id": "INV-005", "invoice_number": "2024-005", "vendor": {"name": "Acme Corp"},   "client": {"name": "Beta Ltd"},  "total_amount": 4800,   "invoice_date": "2024-03-18", "status": "paid"},
        {"id": "INV-006", "invoice_number": "2024-006", "vendor": {"name": "Acme Corp"},   "client": {"name": "Beta Ltd"},  "total_amount": 5200,   "invoice_date": "2024-03-19", "status": "paid"},
        {"id": "INV-007", "invoice_number": "2024-007", "vendor": {"name": "Ghost LLC"},   "client": {"name": "Beta Ltd"},  "total_amount": 87500,  "invoice_date": "2024-03-20", "status": "unpaid"},  # ← Outlier
        {"id": "INV-008", "invoice_number": "2024-008", "vendor": {"name": "Acme Corp"},   "client": {"name": "Beta Ltd"},  "total_amount": 5100,   "invoice_date": "2024-03-23", "status": "paid"},    # ← Weekend
        {"id": "INV-009", "invoice_number": "2024-009", "vendor": {"name": "XYZ Traders"}, "client": {"name": "Beta Ltd"},  "total_amount": 4950,   "invoice_date": "2024-03-21", "status": "unpaid"},
        {"id": "INV-010", "invoice_number": "2024-010", "vendor": {"name": "Acme Corp"},   "client": {"name": "Beta Ltd"},  "total_amount": 5050,   "invoice_date": "2024-03-22", "status": "paid"},
    ]
