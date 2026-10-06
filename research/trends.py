"""Collect Google Trends interest per keyword (no API key needed).

pytrends is unofficial: Google sometimes rate-limits it (HTTP 429).
If that happens, wait a while and rerun.
Usage: python -m research.trends [--geo DE] [--timeframe "today 5-y"]
"""
import argparse
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from pytrends.request import TrendReq

from research.common import DATA_DIR, KEYWORDS_FILE, load_keywords

BATCH_SIZE = 5  # Google Trends compares at most 5 terms per request
ANCHOR_INDEX = 0  # first keyword is repeated in every batch to make batches comparable
MIN_NONZERO_SHARE = 0.5  # below this share of non-zero weeks, a keyword's data is unreliable


def fetch_interest(keywords: list[str], geo: str, timeframe: str) -> pd.DataFrame:
    pytrends = TrendReq(hl="en-US", tz=60)
    anchor, others = keywords[ANCHOR_INDEX], keywords[1:]
    frames = []
    for start in range(0, max(len(others), 1), BATCH_SIZE - 1):
        batch = [anchor] + others[start:start + BATCH_SIZE - 1]
        pytrends.build_payload(batch, timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time().drop(columns="isPartial", errors="ignore")
        # Rescale so the anchor has the same average in every batch.
        anchor_mean = df[anchor].mean() or 1
        frames.append(df.div(anchor_mean).mul(100))
        time.sleep(5)
    combined = pd.concat(frames, axis=1)
    return combined.loc[:, ~combined.columns.duplicated()]


def summarize(interest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keyword in interest.columns:
        series = interest[keyword]
        last_year, prev_year = series.iloc[-52:].mean(), series.iloc[-104:-52].mean()
        monthly = series.groupby(series.index.month).mean()
        rows.append({
            "keyword": keyword,
            "trend_interest": series.iloc[-52:].mean(),
            "trend_growth": (last_year / prev_year - 1) if prev_year else np.nan,
            "peak_month": int(monthly.idxmax()),
            "seasonality": monthly.max() / monthly.mean() if monthly.mean() else np.nan,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geo", default="DE", help="country code, or 'world' for worldwide")
    parser.add_argument("--timeframe", default="today 5-y")
    parser.add_argument("--keywords", type=Path, default=KEYWORDS_FILE, help="term list to use")
    args = parser.parse_args()
    geo = "" if args.geo.lower() == "world" else args.geo

    interest = fetch_interest(load_keywords(args.keywords), geo, args.timeframe)
    sparse = interest.columns[(interest > 0).mean() < MIN_NONZERO_SHARE]
    if len(sparse):
        print(f"Warning: too little search volume in '{args.geo}' for: {', '.join(sparse)}.")
        print("Their numbers are noise. Try search terms in the local language or another --geo.\n")
    DATA_DIR.mkdir(exist_ok=True)
    interest.to_csv(DATA_DIR / f"trends_raw_{date.today()}.csv")
    summary = summarize(interest)
    out = DATA_DIR / f"trends_summary_{date.today()}.csv"
    summary.to_csv(out, index=False)
    print(summary.round(2).to_string(index=False))
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
