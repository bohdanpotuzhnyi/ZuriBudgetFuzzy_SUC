"""Summarizer package exposing budget aggregation utilities."""

from .zurich_budget_linguistic_summaries import (  # noqa: F401
    FIELD_TO_DEPT,
    YEARS,
    answer_request,
    calibrate_level_mfs_from_quantiles,
    calibrate_trend_mfs_from_mad,
    compute_share_distribution,
    compute_trend_distribution,
    ensure_calibration,
    label_level,
    label_trend,
    load_or_fetch,
    summarize,
)

__all__ = [
    "FIELD_TO_DEPT",
    "YEARS",
    "answer_request",
    "calibrate_level_mfs_from_quantiles",
    "calibrate_trend_mfs_from_mad",
    "compute_share_distribution",
    "compute_trend_distribution",
    "ensure_calibration",
    "label_level",
    "label_trend",
    "load_or_fetch",
    "summarize",
]
