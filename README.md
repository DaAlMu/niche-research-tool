# Etsy niche research

Finds product niches with high demand and weak competition, using only official APIs
and Google Trends (no screen-scraping, which Etsy's API terms forbid).

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # then add your Etsy key
```

## Usage

1. Put your search terms into `keywords.txt`.
2. Collect data:
   - `python -m research.trends`: Google Trends, works without a key
     (`--geo DE` is the default; use `--geo world` or `--geo US` for English search terms)
   - `python -m research.etsy`: Etsy listings and shop sales, needs an API key
3. `python -m research.score`: combines everything into `data/niche_scores_<date>.csv`

## Metrics

| Column | Source | Meaning |
|---|---|---|
| trend_interest | Google Trends | Average search interest over the last 12 months (relative) |
| trend_growth | Google Trends | Change vs. the 12 months before |
| peak_month / seasonality | Google Trends | When demand peaks and how strongly |
| competition | Etsy | Number of active listings for the keyword |
| median_price | Etsy | Typical price point |
| median_favorites | Etsy | Buyer interest per listing |
| median_shop_sales | Etsy | Sales of the shops selling it, the best public demand proxy |
| top_shop_share | Etsy | Share of results from the biggest shop (market concentration) |
| niche_score | Combined | Average percentile rank of the metrics above (0–1, higher is better) |

The score only ranks your keywords against each other. Treat it as a shortlist, not a verdict.

## Research funnel

1. **Broad** (`categories.txt`, Google Trends): which categories are big, growing, seasonal?
2. **Narrower** (`keywords.txt`, Etsy API, later eBay): which products, at what price, against how much competition?
3. **Detail** (Keyword Planner, eRank): exact search terms for listings.

## Data sources

### Google Trends (`research/trends.py`, `research/keywords.py`)

- **Origin:** Google web searches (not YouTube or Shopping), default region Germany,
  last 5 years, one value per week. Results can be checked manually at https://trends.google.com.
- **Access:** via [pytrends](https://github.com/GeneralMills/pytrends), an **unofficial** library that
  sends the same requests as the Trends website. Google may temporarily block it (HTTP 429);
  the scripts wait and retry. Switch to Google's official Trends API once access is available.
- **Relative, not absolute:** Google scales every query from 0 to 100 and never publishes real
  search counts. Values are based on a sample of searches and vary slightly between runs.
- **Anchor scaling:** Google compares at most 5 terms per query. The first term of the list is
  repeated in every batch, and all values are rescaled so that the anchor's 5-year average is 100.
  A value of 1,900 means roughly 19x the anchor's search interest.
- **Low volume:** rare terms come back as 0. Terms with data in fewer than half of the weeks are
  flagged as unreliable. This makes Google Trends suitable for broad categories, not niche products.

### Etsy Open API v3 (`research/etsy.py`)

- **Origin:** official API, public endpoints only (active listings, shop profiles). No OAuth needed.
- **Competition:** total number of active listings per keyword.
- **Demand proxies:** favorites per listing and total sales of the shops selling the product
  (Etsy does not publish sales per listing).

## Etsy API access

A Seller App requires an active Etsy shop. Until you have one, register a **Personal App**
in the Etsy Developer Portal and describe the use case honestly (read-only market research
on public listing data, for internal use only). Check the caching rules in Section 1 of the
Etsy API Terms of Use before storing data long-term.

---

The term 'Etsy' is a trademark of Etsy, Inc. This application uses the Etsy API but is not
endorsed or certified by Etsy, Inc.
