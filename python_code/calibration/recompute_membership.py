"""
Utility script to regenerate fuzzy membership parameters.

Usage:
    python3 -m calibration.recompute_membership

The script loads cached department totals (or fetches them if absent),
derives percentile- and MAD-based trapezoids, and overwrites
`summarizer/label_calibration.json`.
"""

from pathlib import Path

from summarizer import (
    YEARS,
    calibrate_level_mfs_from_quantiles,
    calibrate_trend_mfs_from_mad,
    compute_share_distribution,
    compute_trend_distribution,
    load_or_fetch,
)
from summarizer.zurich_budget_linguistic_summaries import save_calibration


def main() -> int:
    df = load_or_fetch(YEARS)
    if df.empty:
        print("No data available for calibration.")
        return 1

    share_samples = compute_share_distribution(df, spending_only=True)
    trend_samples = compute_trend_distribution(df, spending_only=True)
    level_mfs = calibrate_level_mfs_from_quantiles(share_samples)
    trend_mfs = calibrate_trend_mfs_from_mad(trend_samples)
    save_calibration(level_mfs, trend_mfs, df)
    cal_path = Path(__file__).resolve().parent.parent / "summarizer" / "label_calibration.json"
    print(f"Regenerated membership functions at {cal_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
