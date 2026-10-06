"""Combine the latest Etsy and Trends data into one niche score per keyword.

Works with whatever data exists: Trends only, Etsy only, or both.
Usage: python -m research.score
"""
from datetime import date

import numpy as np
import pandas as pd

from research.common import DATA_DIR


def latest(pattern: str) -> pd.DataFrame | None:
    files = sorted(DATA_DIR.glob(pattern))
    return pd.read_csv(files[-1]) if files else None


def etsy_metrics(listings: pd.DataFrame) -> pd.DataFrame:
    return listings.groupby("keyword").agg(
        competition=("total_results", "first"),
        median_price=("price", "median"),
        median_favorites=("favorites", "median"),
        median_shop_sales=("shop_sales", "median"),
        # How concentrated is the market? High = a few big shops dominate.
        top_shop_share=("shop_id", lambda s: s.value_counts(normalize=True).iloc[0]),
    ).reset_index()


def rank(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Percentile rank 0..1, so metrics on different scales can be combined."""
    return series.rank(pct=True, ascending=higher_is_better)


def score(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    if "trend_interest" in df:
        parts += [rank(df["trend_interest"]), rank(df["trend_growth"])]
    if "competition" in df:
        parts += [
            rank(df["median_favorites"]),
            rank(df["median_shop_sales"]),
            rank(df["median_price"]),
            rank(df["competition"], higher_is_better=False),
        ]
    df["niche_score"] = np.nanmean(parts, axis=0).round(2)
    return df.sort_values("niche_score", ascending=False)


def main() -> None:
    trends, listings = latest("trends_summary_*.csv"), latest("etsy_listings_*.csv")
    frames = [trends] if trends is not None else []
    if listings is not None:
        frames.append(etsy_metrics(listings))
    if not frames:
        raise SystemExit("No data yet. Run research.trends and/or research.etsy first.")

    result = frames[0]
    for frame in frames[1:]:
        result = result.merge(frame, on="keyword", how="outer")
    result = score(result)

    out = DATA_DIR / f"niche_scores_{date.today()}.csv"
    result.to_csv(out, index=False)
    print(result.round(2).to_string(index=False))
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
