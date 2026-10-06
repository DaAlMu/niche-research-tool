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

## Etsy API access

A Seller App requires an active Etsy shop. Until you have one, register a **Personal App**
in the Etsy Developer Portal and describe the use case honestly (read-only market research
on public listing data, for internal use only). Check the caching rules in Section 1 of the
Etsy API Terms of Use before storing data long-term.

---

The term 'Etsy' is a trademark of Etsy, Inc. This application uses the Etsy API but is not
endorsed or certified by Etsy, Inc.
