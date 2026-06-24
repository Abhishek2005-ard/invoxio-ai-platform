"""
Anomaly Detection Sub-Agent — State

Shared TypedDict that flows through all 5 nodes:
    ingest_invoices → detect_duplicates → detect_fraud → score_outliers → generate_report
"""

from typing import TypedDict, List, Dict, Any, Optional


class AnomalyDetectionState(TypedDict):
    """Shared state for the Anomaly Detection pipeline."""

    # ── Input ─────────────────────────────────────────────────────────────
    tenant_id:         str
    # Raw invoices passed in OR fetched from DB in ingest node
    input_invoices:    List[Dict[str, Any]]

    # ── ingest_invoices node ──────────────────────────────────────────────
    invoices:          List[Dict[str, Any]]   # Normalized invoice dicts
    invoice_count:     int
    amount_stats:      Dict[str, float]       # mean, std, min, max, median

    # ── detect_duplicates node ────────────────────────────────────────────
    duplicates:        List[Dict[str, Any]]   # DuplicateAnomaly dicts
    duplicate_count:   int

    # ── detect_fraud node ─────────────────────────────────────────────────
    fraud_signals:     List[Dict[str, Any]]   # FraudSignal dicts
    fraud_count:       int

    # ── score_outliers node ───────────────────────────────────────────────
    outlier_scores:    List[Dict[str, Any]]   # OutlierScore dicts
    outlier_count:     int

    # ── generate_report node ──────────────────────────────────────────────
    report:            Optional[Dict[str, Any]]   # Final AnomalyReport dict
    ai_narrative:      str
    recommendations:   List[str]

    # ── Error ─────────────────────────────────────────────────────────────
    error:             Optional[str]
