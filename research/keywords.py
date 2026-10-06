"""Find related search terms for the seeds in keywords.txt via Google Trends.

Review the output and copy the promising terms into keywords.txt by hand.
Usage: python -m research.keywords [--geo DE] [--timeframe "today 12-m"]
"""
import argparse
import time
from datetime import date

import pandas as pd
from pytrends.exceptions import TooManyRequestsError
from pytrends.request import TrendReq

from research.common import DATA_DIR, load_keywords

RETRIES = 3
RETRY_WAIT = 60  # seconds, multiplied by the attempt number


def fetch_related(pytrends: TrendReq, seed: str) -> dict:
    for attempt in range(1, RETRIES + 1):
        try:
            return pytrends.related_queries().get(seed) or {}
        except (IndexError, KeyError):  # pytrends fails on seeds without related data
            return {}
        except TooManyRequestsError:
            wait = RETRY_WAIT * attempt
            print(f"  rate-limited by Google, waiting {wait}s (attempt {attempt}/{RETRIES})")
            time.sleep(wait)
    raise SystemExit("Still rate-limited. Wait an hour and rerun.")


def related_terms(pytrends: TrendReq, seed: str, geo: str, timeframe: str) -> list[dict]:
    pytrends.build_payload([seed], timeframe=timeframe, geo=geo)
    related = fetch_related(pytrends, seed)
    rows = []
    for kind in ("top", "rising"):
        df = related.get(kind)
        if df is None:
            continue
        for _, row in df.iterrows():
            # "top" values are relative popularity (0-100), "rising" values are growth in %.
            rows.append({"seed": seed, "term": row["query"], "kind": kind, "value": row["value"]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geo", default="DE", help="country code, or 'world' for worldwide")
    parser.add_argument("--timeframe", default="today 12-m")
    args = parser.parse_args()
    geo = "" if args.geo.lower() == "world" else args.geo

    pytrends = TrendReq(hl="de-DE", tz=60)
    rows = []
    for seed in load_keywords():
        found = related_terms(pytrends, seed, geo, args.timeframe)
        print(f"{seed}: {len(found)} related terms")
        rows.extend(found)
        time.sleep(5)

    if not rows:
        raise SystemExit("No related terms found. Try broader seeds or another --geo.")
    ideas = pd.DataFrame(rows)
    known = set(load_keywords())
    ideas = ideas[~ideas["term"].isin(known)].drop_duplicates(["term", "kind"])

    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / f"keyword_ideas_{date.today()}.csv"
    ideas.to_csv(out, index=False)
    for kind in ("top", "rising"):
        subset = ideas[ideas["kind"] == kind].sort_values("value", ascending=False)
        print(f"\n{kind.upper()} ({len(subset)}):")
        print(subset.head(25).to_string(index=False))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
