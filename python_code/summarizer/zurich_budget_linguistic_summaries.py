import os
import sys
import math
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

try:
    import requests
except Exception:
    requests = None
import pandas as pd
import numpy as np

API_BASE = "https://api.stadt-zuerich.ch/rpkk-rs/v1"
# Public API key from https://data.stadt-zuerich.ch/dataset/fd_rpktool
API_KEY = os.environ.get("ZRH_API_KEY", "vopVcmhIMkeUCf8gQjk1GgU2wK+fKihAdlCl0WKJ")

HEADERS_CANDIDATES = [
    {"api-key": API_KEY},
]

YEARS = list(range(2019, 2025))
BETRAGS_TYP = "GEMEINDERAT_BESCHLUSS"

# Mapping common English topics to official Zurich department names
FIELD_TO_DEPT = {
    "education": "Schul- und Sportdepartement",
    "healthcare": "Gesundheits- und Umweltdepartement",
    "transport": "Tiefbau- und Entsorgungsdepartement",
    "energy": "Departement der Industriellen Betriebe",
    "digital infrastructure": "Departement der Industriellen Betriebe",
    "security": "Sicherheitsdepartement",
    "housing": "Hochbaudepartement",
    "presidency": "Präsidialdepartement",
    "administration": "Behörden und Gesamtverwaltung",
    "finance": "Finanzdepartement",
}

CALIBRATION_PATH = Path(__file__).with_name("label_calibration.json")
DEFAULT_LEVEL_MFS: Dict[str, Tuple[float, float, float, float]] = {
    "low": (0.0, 0.0, 7.5, 12.5),
    "medium": (10.0, 15.0, 22.5, 30.0),
    "high": (20.0, 27.5, 100.0, 100.0),
}
DEFAULT_TREND_MFS: Dict[str, Tuple[float, float, float, float]] = {
    "falling": (-100.0, -4.0, -2.0, -0.5),
    "stable": (-1.5, -1.0, 1.0, 1.5),
    "rising": (0.5, 2.0, 4.0, 100.0),
}
LEVEL_MFS_CACHE: Optional[Dict[str, Tuple[float, float, float, float]]] = None
TREND_MFS_CACHE: Optional[Dict[str, Tuple[float, float, float, float]]] = None


def calibrate_level_mfs_from_quantiles(share_pcts: np.ndarray) -> Dict[str, Tuple[float, float, float, float]]:
    """Calibrate level trapezoids from empirical quantiles to avoid arbitrary cutoffs."""
    s = np.asarray(share_pcts, dtype=float)
    s = s[np.isfinite(s)]
    if len(s) < 5:
        return DEFAULT_LEVEL_MFS
    q10, q30, q50, q70, q90 = np.quantile(s, [0.10, 0.30, 0.50, 0.70, 0.90])
    return {
        "low": (0.0, 0.0, float(q10), float(q30 if q30 > q10 else q10 + 1e-6)),
        "medium": (
            float(q10),
            float(q30 if q30 > q10 else q10 + 1e-6),
            float(q50 if q50 > q30 else q30 + 1e-6),
            float(q70 if q70 > q50 else q50 + 1e-6),
        ),
        "high": (
            float(q50),
            float(q70 if q70 > q50 else q50 + 1e-6),
            float(q90),
            100.0, # Let's hope Zurich is a stable city :)
        ),
    }


def mad(x: np.ndarray) -> float:
    arr = np.asarray(x, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return 1.0
    med = float(np.median(arr))
    return float(np.median(np.abs(arr - med))) + 1e-9


def calibrate_trend_mfs_from_mad(
    slopes_pct_of_mean: np.ndarray, k_stable: float = 1.0, k_rise: float = 2.0
) -> Dict[str, Tuple[float, float, float, float]]:
    """Calibrate trend trapezoids using robust dispersion to capture rising/stable/falling."""
    x = np.asarray(slopes_pct_of_mean, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 5:
        return DEFAULT_TREND_MFS
    m = float(np.median(x))
    s = mad(x)
    fall_start = m - k_stable * s
    rise_start = m + k_stable * s
    fall_full = m - k_rise * s
    rise_full = m + k_rise * s
    stable_a = m - k_rise * s
    stable_b = fall_start
    stable_c = rise_start
    stable_d = m + k_rise * s
    return {
        "falling": (-100.0, float(fall_full), float(fall_start), float(m)),
        "stable": (float(stable_a), float(stable_b), float(stable_c), float(stable_d)),
        "rising": (float(m), float(rise_start), float(rise_full), 100.0),
    }


def compute_share_distribution(df: pd.DataFrame, spending_only: bool = True) -> np.ndarray:
    if spending_only:
        df_use = df[df["betrag"] > 0].copy()
    else:
        df_use = df.copy()
    if df_use.empty:
        return np.array([], dtype=float)
    totals = df_use.groupby("jahr", as_index=False)["betrag"].sum().rename(columns={"betrag": "city_total"})
    merged = df_use.merge(totals, on="jahr", how="left")
    merged["share_pct"] = (merged["betrag"] / merged["city_total"]) * 100.0
    return merged["share_pct"].to_numpy()


def compute_trend_distribution(df: pd.DataFrame, spending_only: bool = True) -> np.ndarray:
    if spending_only:
        df_use = df[df["betrag"] > 0].copy()
    else:
        df_use = df.copy()
    if df_use.empty:
        return np.array([], dtype=float)
    totals = df_use.groupby("jahr", as_index=False)["betrag"].sum().rename(columns={"betrag": "city_total"})
    merged = df_use.merge(totals, on="jahr", how="left")
    merged["share_pct"] = (merged["betrag"] / merged["city_total"]) * 100.0
    values = []
    for _, grp in merged.groupby("departement_name"):
        grp = grp.sort_values("jahr")
        shares = grp["share_pct"].tolist()
        years = grp["jahr"].tolist()
        if len(shares) < 2:
            continue
        slope_abs = theil_sen_slope(years, shares)
        mean_level = np.mean(shares) if shares else 0.0
        slope_pct = 0.0 if mean_level == 0 else (slope_abs / mean_level) * 100.0
        values.append(slope_pct)
    return np.array(values, dtype=float)


def save_calibration(
    level_mfs: Dict[str, Tuple[float, float, float, float]],
    trend_mfs: Dict[str, Tuple[float, float, float, float]],
    df: Optional[pd.DataFrame] = None,
    path: Path = CALIBRATION_PATH,
) -> None:
    payload = {
        "source_years": None,
        "level_mfs": {k: list(v) for k, v in level_mfs.items()},
        "trend_mfs": {k: list(v) for k, v in trend_mfs.items()},
    }
    if df is not None and not df.empty:
        payload["source_years"] = [int(df["jahr"].min()), int(df["jahr"].max())]
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_calibration(path: Path = CALIBRATION_PATH) -> Optional[Tuple[Dict, Dict]]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    level_raw = data.get("level_mfs", {})
    trend_raw = data.get("trend_mfs", {})
    required_level = {"low", "medium", "high"}
    required_trend = {"falling", "stable", "rising"}
    if set(level_raw.keys()) != required_level or set(trend_raw.keys()) != required_trend:
        return None

    def _validate(entry: Dict[str, List[float]]) -> Dict[str, Tuple[float, float, float, float]]:
        out = {}
        for k, vals in entry.items():
            if not isinstance(vals, (list, tuple)) or len(vals) != 4:
                raise ValueError("Malformed calibration entry")
            out[k] = tuple(float(x) for x in vals)
        return out

    try:
        level = _validate(level_raw)
        trend = _validate(trend_raw)
    except Exception:
        return None
    return level, trend


def ensure_calibration(reference_df: Optional[pd.DataFrame] = None) -> Tuple[Dict, Dict]:
    global LEVEL_MFS_CACHE, TREND_MFS_CACHE
    if LEVEL_MFS_CACHE and TREND_MFS_CACHE:
        return LEVEL_MFS_CACHE, TREND_MFS_CACHE
    loaded = load_calibration()
    if loaded:
        LEVEL_MFS_CACHE, TREND_MFS_CACHE = loaded
        return loaded
    if reference_df is None or reference_df.empty:
        LEVEL_MFS_CACHE, TREND_MFS_CACHE = DEFAULT_LEVEL_MFS, DEFAULT_TREND_MFS
        return LEVEL_MFS_CACHE, TREND_MFS_CACHE
    share_samples = compute_share_distribution(reference_df, spending_only=True)
    slope_samples = compute_trend_distribution(reference_df, spending_only=True)
    level_mfs = calibrate_level_mfs_from_quantiles(share_samples)
    trend_mfs = calibrate_trend_mfs_from_mad(slope_samples)
    save_calibration(level_mfs, trend_mfs, reference_df)
    LEVEL_MFS_CACHE, TREND_MFS_CACHE = level_mfs, trend_mfs
    return level_mfs, trend_mfs

def http_get(url: str, params: Dict = None):
    if requests is None:
        raise RuntimeError("The 'requests' package is not installed; cannot fetch from API. Use local CSV or install requests.")
    last_exc = None
    for headers in HEADERS_CANDIDATES:
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            if resp.status_code == 200:
                return resp
            # If unauthorized, try the next header style
            if resp.status_code in (401, 403):
                last_exc = RuntimeError(f"Unauthorized with headers {headers.keys()}")
                continue
            # Propagate other HTTP errors
            resp.raise_for_status()
        except Exception as e:
            last_exc = e
    if last_exc:
        raise last_exc
    raise RuntimeError("HTTP request failed with no further detail.")

def get_departments() -> pd.DataFrame:
    url = f"{API_BASE}/departemente"
    resp = http_get(url)
    data = resp.json().get("value", [])
    return pd.DataFrame(data)

def get_sachkonto2_for_department(dept_key: int, years: List[int], betrags_typ: str) -> pd.DataFrame:
    # Endpoint fields: betrag (string CHF), betragsTyp, institution, jahr, sachkonto
    url = f"{API_BASE}/sachkonto2stellig"
    frames = []
    for y in years:
        params = {"departement": dept_key, "jahr": y, "betragsTyp": betrags_typ}
        resp = http_get(url, params=params)
        value = resp.json().get("value", [])
        if not value:
            continue
        df = pd.DataFrame(value)
        df["jahr"] = df["jahr"].astype(int)
        df["betrag"] = pd.to_numeric(df["betrag"], errors="coerce").fillna(0.0)
        frames.append(df)
        time.sleep(0.2)  # we are polite, right?
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=["betrag", "betragsTyp", "institution", "jahr", "sachkonto"])

def aggregate_department_totals(years: List[int]) -> pd.DataFrame:
    depts = get_departments()
    all_rows = []
    for _, row in depts.iterrows():
        dept_key = int(row["key"])
        dept_name = row["bezeichnung"]
        df = get_sachkonto2_for_department(dept_key, years, BETRAGS_TYP)
        if df.empty:
            continue
        # Sum across institutions and sachkonto per year
        grp = df.groupby("jahr", as_index=False)["betrag"].sum()
        grp["departement_key"] = dept_key
        grp["departement_name"] = dept_name
        all_rows.append(grp)
    if not all_rows:
        raise RuntimeError("No data retrieved. Check API key/header or years.")
    out = pd.concat(all_rows, ignore_index=True)
    return out

def theil_sen_slope(years: List[int], values: List[float]) -> float:
    # Median of pairwise slopes for robustness
    x = np.array(years, dtype=float)
    y = np.array(values, dtype=float)
    slopes = []
    for i in range(len(x)):
        for j in range(i+1, len(x)):
            dx = x[j] - x[i]
            if dx == 0:
                continue
            slopes.append((y[j] - y[i]) / dx)
    if not slopes:
        return 0.0
    return float(np.median(slopes))

def fuzzy_trapezoid(x: float, a: float, b: float, c: float, d: float) -> float:
    # Standard trapezoid membership curve
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if a < x < b:
        return (x - a) / (b - a)
    if c < x < d:
        return (d - x) / (d - c)
    return 0.0

def label_level(
    share_pct: float, mfs: Optional[Dict[str, Tuple[float, float, float, float]]] = None
) -> Tuple[str, float]:
    params = mfs or LEVEL_MFS_CACHE or DEFAULT_LEVEL_MFS
    low = fuzzy_trapezoid(share_pct, *params["low"])
    med = fuzzy_trapezoid(share_pct, *params["medium"])
    high = fuzzy_trapezoid(share_pct, *params["high"])
    labels = {"low": low, "medium": med, "high": high}
    label = max(labels, key=labels.get)
    return label, labels[label]

def label_trend(
    slope_pct_per_year: float, mfs: Optional[Dict[str, Tuple[float, float, float, float]]] = None
) -> Tuple[str, float]:
    params = mfs or TREND_MFS_CACHE or DEFAULT_TREND_MFS
    falling = fuzzy_trapezoid(slope_pct_per_year, *params["falling"])
    stable = fuzzy_trapezoid(slope_pct_per_year, *params["stable"])
    rising = fuzzy_trapezoid(slope_pct_per_year, *params["rising"])
    labels = {"falling": falling, "stable": stable, "rising": rising}
    label = max(labels, key=labels.get)
    return label, labels[label]

def summarize(
    out_df: pd.DataFrame,
    spending_only: bool = True,
    level_mfs: Optional[Dict[str, Tuple[float, float, float, float]]] = None,
    trend_mfs: Optional[Dict[str, Tuple[float, float, float, float]]] = None,
) -> pd.DataFrame:
    # Compute city totals, department shares, slopes, and summary sentences
    if spending_only:
        df = out_df[out_df["betrag"] > 0].copy()
    else:
        df = out_df.copy()

    if df.empty:
        return pd.DataFrame(columns=[
            "departement", "last_year", "share_last_pct", "slope_pp_per_year",
            "slope_pct_of_mean", "level_label", "level_mu", "trend_label", "trend_mu", "sentence"
        ])

    totals = df.groupby("jahr", as_index=False)["betrag"].sum().rename(columns={"betrag": "city_total"})
    merged = df.merge(totals, on="jahr", how="left")
    merged["share_pct"] = (merged["betrag"] / merged["city_total"]) * 100.0

    summaries = []
    for dept, grp in merged.groupby("departement_name"):
        grp = grp.sort_values("jahr")
        shares = grp["share_pct"].tolist()
        years = grp["jahr"].tolist()
        last_share = shares[-1]
        mean_level = np.mean(shares) if shares else 0.0

        # Use slope relative to mean for scale invariance
        slope_abs = theil_sen_slope(years, shares)  # percentage points per year
        slope_pct_of_mean = 0.0 if mean_level == 0 else (slope_abs / mean_level) * 100.0

        level_label, level_mu = label_level(last_share, level_mfs)
        trend_label, trend_mu = label_trend(slope_pct_of_mean, trend_mfs)

        sentence = (f"{dept}: share is {level_label.upper()} and {trend_label.upper()} "
                    f"({slope_abs:+.2f} pp/yr; {years[0]}→{years[-1]}: {shares[0]:.2f}%→{shares[-1]:.2f}%).")
        summaries.append({
            "departement": dept,
            "last_year": years[-1],
            "share_last_pct": last_share,
            "slope_pp_per_year": slope_abs,
            "slope_pct_of_mean": slope_pct_of_mean,
            "level_label": level_label,
            "level_mu": level_mu,
            "trend_label": trend_label,
            "trend_mu": trend_mu,
            "sentence": sentence
        })
    return pd.DataFrame(summaries).sort_values(["last_year", "share_last_pct"], ascending=[False, False])


def load_or_fetch(years: List[int]) -> pd.DataFrame:
    """Load precomputed CSV if available, otherwise fetch from API.
    Keeps behavior deterministic when network is unavailable.
    """
    csv_candidates = [
        Path("zrh_budget_by_dept_year.csv"),
        Path(__file__).resolve().parents[1] / "zrh_budget_by_dept_year.csv",
    ]
    for csv_path in csv_candidates:
        if csv_path.exists():
            return pd.read_csv(csv_path)
    return aggregate_department_totals(years)


def _flex_match_department(dept_query: str, available: List[str]) -> Optional[str]:
    q = dept_query.strip().lower()
    # First check direct mappings (English → official name)
    if q in FIELD_TO_DEPT:
        return FIELD_TO_DEPT[q]
    # Then try a substring match against the canonical names
    for name in available:
        if q == name.lower() or q in name.lower():
            return name
    return None


def answer_request(request: Dict) -> Dict:
    """Serve a minimal request/response, aligning with the slide artifact.

    Expected request fields (examples):
      - timeline: "all" (default) or {"since": 2019}
      - field: department/topic (e.g., "education" or official German name) or "all"
      - generalization_level: 0, 1, or 2 (string or int)
    """
    # Parse timeline filters
    timeline = request.get("timeline", "all")
    since_year = None
    if isinstance(timeline, dict) and "since" in timeline:
        since_year = int(timeline["since"]) if timeline["since"] is not None else None
    elif isinstance(timeline, (int, str)) and str(timeline).isdigit():
        since_year = int(timeline)

    # Prefer cached CSVs; fall back to API fetch
    df_all = load_or_fetch(YEARS)
    level_mfs, trend_mfs = ensure_calibration(df_all)
    df = df_all.copy()
    if since_year is not None:
        df = df[df["jahr"] >= since_year]
    if df.empty:
        return {"message": "No data available for the requested timeline.", "request": request}

    # Summaries use spending only to mirror public-spending narratives
    summaries = summarize(df, spending_only=True, level_mfs=level_mfs, trend_mfs=trend_mfs)
    if summaries.empty:
        return {"message": "No spending data found for the requested timeline.", "request": request}

    # Normalize the requested field
    field = (request.get("field") or "all").strip().lower()
    generalization_level = request.get("generalization_level", 1)
    try:
        gen_level = int(generalization_level)
    except Exception:
        gen_level = 1

    # Track the year window for the filtered slice
    start_year = int(df["jahr"].min())
    end_year = int(df["jahr"].max())

    # Helper: recompute slopes within the filtered window
    def _compute_slopes() -> pd.DataFrame:
        # Recompute shares within the window (spending only)
        df_win = df[df["betrag"] > 0].copy()
        totals = df_win.groupby("jahr", as_index=False)["betrag"].sum().rename(columns={"betrag": "city_total"})
        merged = df_win.merge(totals, on="jahr", how="left")
        merged["share_pct"] = (merged["betrag"] / merged["city_total"]) * 100.0
        rows = []
        for dept, grp in merged.groupby("departement_name"):
            grp = grp.sort_values("jahr")
            shares = grp["share_pct"].tolist()
            years = grp["jahr"].tolist()
            if len(shares) < 2:
                continue
            slope = theil_sen_slope(years, shares)
            rows.append({"departement": dept, "slope_pp_per_year": slope, "last_share": shares[-1]})
        return pd.DataFrame(rows)

    slopes_df = _compute_slopes()

    if field == "all":
        # Report the biggest movers across departments
        top_inc = slopes_df.sort_values("slope_pp_per_year", ascending=False).head(2)
        top_dec = slopes_df.sort_values("slope_pp_per_year", ascending=True).head(2)
        inc_list = [f"{r['departement']} ({r['slope_pp_per_year']:+.2f} pp/yr)" for _, r in top_inc.iterrows()]
        dec_list = [f"{r['departement']} ({r['slope_pp_per_year']:+.2f} pp/yr)" for _, r in top_dec.iterrows()]
        msg = (
            f"Between {start_year} and {end_year}, the biggest increases are in "
            f"{', '.join(inc_list)}."
        )
        if gen_level >= 1 and len(dec_list) > 0:
            msg += f" Decreases are led by {', '.join(dec_list)}."
        return {
            "message": msg,
            "request": request,
            "top_increases": top_inc.to_dict(orient="records"),
            "top_decreases": top_dec.to_dict(orient="records"),
        }

    # Resolve the department from the provided field text
    dept_names = summaries["departement"].unique().tolist()
    dept = _flex_match_department(field, dept_names)
    if not dept:
        return {"message": f"Unknown field '{field}'. Try one of: all, education, healthcare, transport, energy.", "request": request}

    row = summaries[summaries["departement"] == dept].sort_values("last_year", ascending=False).head(1)
    if row.empty:
        return {"message": f"No data found for '{dept}' in the requested timeline.", "request": request}

    r = row.iloc[0]
    # Optionally mention where the biggest increases are citywide
    extra = ""
    if gen_level >= 1 and not slopes_df.empty:
        top_inc = slopes_df.sort_values("slope_pp_per_year", ascending=False).head(2)
        inc_list = [f"{x['departement']}" for _, x in top_inc.iterrows()]
        extra = f" Meanwhile, the biggest increases are in {', '.join(inc_list)}."

    msg = (
        f"Since {start_year}, {dept} is {r['trend_label']} and currently {r['level_label']} "
        f"({r['share_last_pct']:.1f}% in {end_year}, {r['slope_pp_per_year']:+.2f} pp/yr).{extra}"
    )
    return {
        "message": msg,
        "request": request,
        "department": dept,
        "summary": {
            "level": r["level_label"],
            "level_mu": float(r["level_mu"]),
            "trend": r["trend_label"],
            "trend_mu": float(r["trend_mu"]),
            "share_last_pct": float(r["share_last_pct"]),
            "slope_pp_per_year": float(r["slope_pp_per_year"]),
            "slope_pct_of_mean": float(r["slope_pct_of_mean"]),
            "years": {"start": start_year, "end": end_year},
        },
    }

def main():
    # Serve API-style responses when --request is provided; otherwise run batch mode and persist CSVs
    if "--request" in sys.argv:
        idx = sys.argv.index("--request")
        payload = None
        if idx + 1 < len(sys.argv):
            arg = sys.argv[idx + 1]
            # If the argument points to a file, read it; otherwise parse the JSON string
            if os.path.exists(arg):
                with open(arg, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            else:
                payload = json.loads(arg)
        else:
            # Fall back to stdin for the payload
            payload = json.load(sys.stdin)
        resp = answer_request(payload or {})
        print(json.dumps(resp, ensure_ascii=False))
        return

    print("Preparing Zurich budget summaries (spending-only) ...", file=sys.stderr)
    out = load_or_fetch(YEARS)
    level_mfs, trend_mfs = ensure_calibration(out)
    print(f"Rows available: {len(out)}", file=sys.stderr)
    summaries = summarize(out, spending_only=True, level_mfs=level_mfs, trend_mfs=trend_mfs)
    print("\n=== TOP 8 SUMMARIES (latest year) ===")
    if not summaries.empty:
        latest_year = summaries["last_year"].max()
        top = summaries[summaries["last_year"] == latest_year].head(8)
        for s in top["sentence"]:
            print("- " + s)
    else:
        print("No summaries available.")

    # Save CSV outputs for offline runs
    out_path1 = "zrh_budget_by_dept_year.csv"
    out_path2 = "zrh_budget_linguistic_summaries.csv"
    out.to_csv(out_path1, index=False)
    summaries.to_csv(out_path2, index=False)
    print(f"\nSaved: {out_path1} and {out_path2}")

if __name__ == "__main__":
    main()
