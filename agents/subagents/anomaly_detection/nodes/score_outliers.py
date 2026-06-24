"""
Node 4 — score_outliers

Responsibility:
  - Compute a statistical outlier score for EVERY invoice
  - Methods used:
      Z-Score  → how many standard deviations from the mean
      IQR Flag → whether the amount falls outside Q1 - 1.5*IQR or Q3 + 1.5*IQR
      Percentile → where the invoice sits in the overall distribution
  - Combine into a single is_outlier determination
  - Only amounts with |Z| > 2.5 OR IQR flag = True are marked outliers

Pipeline: ingest_invoices → detect_duplicates → detect_fraud → [score_outliers] → generate_report
"""

from typing import Any, Dict, List
from subagents.anomaly_detection.state import AnomalyDetectionState

Z_SCORE_THRESHOLD   = 2.5   # Standard deviations — beyond this = outlier
IQR_MULTIPLIER      = 1.5   # Standard Tukey fence multiplier


async def score_outliers_node(state: AnomalyDetectionState) -> dict:
    """
    Assigns an outlier score to every invoice using Z-score and IQR.

    Reads:  invoices, amount_stats
    Writes: outlier_scores, outlier_count
    """
    invoices     = state.get("invoices", [])
    stats        = state.get("amount_stats", {})

    mean   = stats.get("mean",   0.0)
    std    = stats.get("std",    0.0)
    q1     = stats.get("q1",     0.0)
    q3     = stats.get("q3",     0.0)
    min_v  = stats.get("min",    0.0)
    max_v  = stats.get("max",    0.0)

    iqr            = q3 - q1
    lower_fence    = q1 - IQR_MULTIPLIER * iqr
    upper_fence    = q3 + IQR_MULTIPLIER * iqr

    print(f"\n📊 [score_outliers] Scoring {len(invoices)} invoices...")
    print(f"  Stats: mean={mean}, std={std}, IQR=[{q1}, {q3}], fences=[{lower_fence:.0f}, {upper_fence:.0f}]")

    scores: List[Dict[str, Any]] = []
    outlier_count = 0

    amounts = [inv["amount"] for inv in invoices if inv["amount"] > 0]

    for inv in invoices:
        amount = inv["amount"]

        # ── Z-Score ───────────────────────────────────────────────────────
        z_score = (amount - mean) / std if std > 0 else 0.0

        # ── IQR Flag ──────────────────────────────────────────────────────
        iqr_flag = (amount < lower_fence) or (amount > upper_fence)

        # ── Percentile ────────────────────────────────────────────────────
        sorted_amounts = sorted(amounts)
        if sorted_amounts and max_v > min_v:
            rank = sum(1 for a in sorted_amounts if a <= amount)
            percentile = round((rank / len(sorted_amounts)) * 100, 1)
        else:
            percentile = 50.0

        # ── Final determination ───────────────────────────────────────────
        is_outlier = abs(z_score) > Z_SCORE_THRESHOLD or iqr_flag

        # Build reason string
        reasons = []
        if abs(z_score) > Z_SCORE_THRESHOLD:
            direction = "above" if z_score > 0 else "below"
            reasons.append(f"Z-score {z_score:.2f} ({abs(z_score):.1f}σ {direction} mean)")
        if iqr_flag:
            fence = "upper" if amount > upper_fence else "lower"
            reasons.append(f"Outside {fence} IQR fence ({fence == 'upper' and upper_fence or lower_fence:.0f})")

        outlier_reason = "; ".join(reasons) if reasons else "Within normal range"

        if is_outlier:
            outlier_count += 1
            print(f"  🔴 OUTLIER: {inv['id']} | amount={amount:,.2f} | z={z_score:.2f} | {outlier_reason}")

        scores.append({
            "invoice_id":     inv["id"],
            "vendor_name":    inv["vendor_name"],
            "amount":         amount,
            "z_score":        round(z_score, 4),
            "iqr_flag":       iqr_flag,
            "percentile":     percentile,
            "is_outlier":     is_outlier,
            "outlier_reason": outlier_reason,
        })

    print(f"✅ [score_outliers] {outlier_count}/{len(invoices)} invoices flagged as outliers")

    return {
        "outlier_scores": scores,
        "outlier_count":  outlier_count,
    }
