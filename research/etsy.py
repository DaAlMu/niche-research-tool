"""Collect active Etsy listings per keyword via the official Open API v3.

Uses only public endpoints, which need an API key but no OAuth login.
Usage: python -m research.etsy [--pages 2]
"""
import argparse
import os
import time
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv

from research.common import DATA_DIR, load_keywords

BASE_URL = "https://openapi.etsy.com/v3/application"
PAGE_SIZE = 100  # API maximum
REQUEST_PAUSE = 0.25  # stay well below Etsy's per-second rate limit


class EtsyClient:
    def __init__(self, api_key: str, shared_secret: str):
        self.session = requests.Session()
        self.session.headers["x-api-key"] = f"{api_key}:{shared_secret}"

    def _get(self, path: str, params: dict | None = None) -> dict:
        time.sleep(REQUEST_PAUSE)
        response = self.session.get(f"{BASE_URL}{path}", params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def search_listings(self, keyword: str, pages: int) -> tuple[int, list[dict]]:
        """Return (total number of results, listings from the first pages)."""
        total, listings = 0, []
        for page in range(pages):
            data = self._get(
                "/listings/active",
                {"keywords": keyword, "limit": PAGE_SIZE, "offset": page * PAGE_SIZE},
            )
            total = data["count"]
            listings.extend(data["results"])
            if len(data["results"]) < PAGE_SIZE:
                break
        return total, listings

    def get_shop(self, shop_id: int) -> dict:
        return self._get(f"/shops/{shop_id}")


def listing_row(keyword: str, total: int, listing: dict) -> dict:
    price = listing.get("price") or {}
    return {
        "keyword": keyword,
        "total_results": total,
        "listing_id": listing["listing_id"],
        "shop_id": listing["shop_id"],
        "title": listing["title"],
        "price": price.get("amount", 0) / (price.get("divisor") or 1),
        "currency": price.get("currency_code"),
        "favorites": listing.get("num_favorers", 0),
        "created": pd.to_datetime(listing.get("original_creation_timestamp"), unit="s"),
        "tags": "|".join(listing.get("tags") or []),
        "url": listing.get("url"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=2, help="result pages per keyword (100 each)")
    args = parser.parse_args()

    load_dotenv()
    api_key, shared_secret = os.getenv("ETSY_API_KEY"), os.getenv("ETSY_SHARED_SECRET")
    if not api_key or not shared_secret:
        raise SystemExit("Etsy credentials missing: copy .env.example to .env and fill in both values.")
    client = EtsyClient(api_key, shared_secret)

    rows = []
    for keyword in load_keywords():
        total, listings = client.search_listings(keyword, args.pages)
        print(f"{keyword}: {total} results, {len(listings)} collected")
        rows.extend(listing_row(keyword, total, listing) for listing in listings)
    listings_df = pd.DataFrame(rows)

    # Shop sales counts are the best public proxy for real demand.
    shops = []
    for shop_id in listings_df["shop_id"].unique():
        shop = client.get_shop(int(shop_id))
        shops.append({
            "shop_id": shop_id,
            "shop_sales": shop.get("transaction_sold_count", 0),
            "shop_reviews": shop.get("review_count", 0),
            "shop_rating": shop.get("review_average"),
        })
    listings_df = listings_df.merge(pd.DataFrame(shops), on="shop_id", how="left")

    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / f"etsy_listings_{date.today()}.csv"
    listings_df.to_csv(out, index=False)
    print(f"Saved {len(listings_df)} listings to {out}")


if __name__ == "__main__":
    main()
