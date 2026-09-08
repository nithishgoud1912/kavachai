"""
KavachAI — Data/Analytics Agent
Implements: FR-DAT-1 (retrieve time-series), FR-DAT-2 (deterministic stats via pandas),
            FR-DAT-3 (return computed result + underlying data points)

Contract (API_Reference.md §8.3):
    analyze(metric: str, equipment_id: str, dataset_id: str)
        -> {trend, pct_change, data_points, threshold_breach}

CRITICAL: This module uses ONLY pandas for computation. NO LLM calls.
          FR-DAT-2 / FR-SYN-3: "The LLM never does arithmetic."
"""

import pandas as pd
from typing import Optional

from app.agents.base import DataAnalysisResult, DataPoint, TrendDirection
from app.db.tabular_store import tabular_store


def analyze(
    metric: str,
    equipment_id: str,
    dataset_id: str,
    threshold: Optional[float] = None,
) -> DataAnalysisResult:
    """
    Compute deterministic trend analysis for a metric on an equipment.
    Implements: FR-DAT-1, FR-DAT-2, FR-DAT-3

    THIS IS PURE PANDAS CODE. No LLM call. No model_router import.
    Testable independently of any model (NFR-MNT-1).

    Args:
        metric: e.g. "vibration", "temperature"
        equipment_id: e.g. "P-102"
        dataset_id: identifier for the dataset to query
        threshold: optional threshold value for breach detection

    Returns:
        DataAnalysisResult with trend, pct_change, data_points, threshold_breach
    """
    # Resolve table name
    table_name = f"dataset_{dataset_id.replace('-', '_')}"

    # FR-DAT-1: Retrieve time-series records
    df = tabular_store.query_by_equipment(table_name, equipment_id, metric)

    if df.empty:
        return DataAnalysisResult(
            trend=TrendDirection.STABLE,
            pct_change=0.0,
            data_points=[],
            threshold_breach=None,
        )

    # Ensure sorted by timestamp
    df = df.sort_values("timestamp").reset_index(drop=True)

    # FR-DAT-3: Build data points for citation
    data_points = []
    for _, row in df.iterrows():
        data_points.append(DataPoint(
            timestamp=str(row["timestamp"]),
            value=float(row["value"]),
            unit=str(row["unit"]),
        ))

    # FR-DAT-2: Compute trend direction (deterministic, pandas only)
    values = df["value"].astype(float).tolist()
    trend = _compute_trend(values)

    # FR-DAT-2: Compute percentage change (first to last)
    pct_change = _compute_pct_change(values)

    # Threshold breach detection
    threshold_breach = None
    if threshold is not None:
        latest_value = values[-1]
        threshold_breach = latest_value > threshold

    return DataAnalysisResult(
        trend=trend,
        pct_change=round(pct_change, 1),
        data_points=data_points,
        threshold_breach=threshold_breach,
    )


def _compute_trend(values: list[float]) -> TrendDirection:
    """
    Determine trend direction from a sequence of values.
    Uses simple linear regression slope sign.
    Pure pandas/math — no LLM.
    """
    if len(values) < 2:
        return TrendDirection.STABLE

    # Simple: compare first half average to second half average
    mid = len(values) // 2
    first_half_avg = sum(values[:mid]) / max(mid, 1)
    second_half_avg = sum(values[mid:]) / max(len(values) - mid, 1)

    diff_pct = ((second_half_avg - first_half_avg) / max(abs(first_half_avg), 0.001)) * 100

    if diff_pct > 5:
        return TrendDirection.INCREASING
    elif diff_pct < -5:
        return TrendDirection.DECREASING
    else:
        return TrendDirection.STABLE


def _compute_pct_change(values: list[float]) -> float:
    """
    Compute percentage change from first to last value.
    Pure arithmetic — no LLM.
    """
    if len(values) < 2 or values[0] == 0:
        return 0.0

    return ((values[-1] - values[0]) / abs(values[0])) * 100
