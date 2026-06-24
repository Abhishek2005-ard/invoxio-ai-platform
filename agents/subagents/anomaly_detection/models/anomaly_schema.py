"""
Anomaly Detection Sub-Agent — Pydantic Models

Defines structured types for all anomaly findings:
  - DuplicateAnomaly   → exact or fuzzy duplicate invoices
  - FraudSignal        → AI-detected suspicious patterns
  - OutlierScore       → statistical deviation score per invoice
  - AnomalyReport      → final consolidated report
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class DuplicateAnomaly(BaseModel):
    """Two invoices that look like duplicates."""
    invoice_id_a:     str
    invoice_id_b:     str
    match_type:       Literal["exact", "fuzzy", "amount_vendor"]
    match_score:      float = Field(ge=0.0, le=1.0)   # 1.0 = identical
    shared_fields:    List[str]                         # e.g. ["vendor","amount","date"]
    risk_level:       Literal["low", "medium", "high"]
    recommendation:   str


class FraudSignal(BaseModel):
    """An AI-detected fraud pattern on a specific invoice."""
    invoice_id:   str
    signal_type:  Literal[
        "round_amount",          # Suspiciously round numbers (e.g. exactly $10,000)
        "unusual_vendor",        # First-time or rare vendor
        "velocity_spike",        # Too many invoices from same vendor in short time
        "weekend_submission",    # Submitted on weekend/holiday
        "sequential_numbers",    # Invoice numbers incremented by 1 repeatedly
        "amount_just_below_threshold",  # e.g. $9,999 to avoid $10k review
        "missing_required_fields",
        "payment_method_change", # Vendor suddenly changed bank account
        "other",
    ]
    description:  str
    confidence:   float = Field(ge=0.0, le=1.0)
    risk_level:   Literal["low", "medium", "high", "critical"]
    evidence:     str   # Specific data points that triggered this signal


class OutlierScore(BaseModel):
    """Statistical outlier score for a single invoice."""
    invoice_id:      str
    amount:          float
    z_score:         float   # Standard deviations from mean (|z| > 2.5 = outlier)
    iqr_flag:        bool    # True if outside IQR * 1.5 bounds
    percentile:      float   # Where this invoice sits in the amount distribution
    is_outlier:      bool    # Final determination
    outlier_reason:  str


class AnomalySummary(BaseModel):
    """High-level summary counts for the report header."""
    total_invoices_analyzed:  int
    duplicate_pairs_found:    int
    fraud_signals_found:      int
    outliers_found:           int
    critical_alerts:          int
    total_amount_at_risk:     float


class AnomalyReport(BaseModel):
    """Final consolidated anomaly detection report."""
    tenant_id:       str
    generated_at:    str   # ISO datetime
    summary:         AnomalySummary
    duplicates:      List[DuplicateAnomaly]  = Field(default_factory=list)
    fraud_signals:   List[FraudSignal]       = Field(default_factory=list)
    outliers:        List[OutlierScore]      = Field(default_factory=list)
    ai_narrative:    str    # Gemini's plain-English summary of all findings
    recommendations: List[str]
