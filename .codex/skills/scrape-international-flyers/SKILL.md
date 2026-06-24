---
name: scrape-international-flyers
description: Scrape and maintain Tim Hortons retailer flyer and promotion offers for Mexico, Saudi Arabia, and South Korea. Use when Codex needs to find current Tim Hortons offers, run a test scrape, update the International Flyer Scrapper project data, preserve the dashboard offer schema, or upload detected flyer offers to GitHub.
---

# Scrape International Flyers

## Workflow

1. Read the tracker project files before editing:
   - `scraper.py`
   - `data/offers.json`
   - `app.py` when changing displayed columns.
2. Use the market sources in `references/sources.md`.
3. Keep the offer schema stable. Each offer must include dates, retailer, item, price, and a link to the offer, plus the existing optional fields used by the dashboard.
4. Treat source pages as volatile. Run a live scrape before updating `data/offers.json`; do not rely only on previous saved data.
5. Do not invent offers. If a market has no direct flyer/promotion source, keep its `offers` array empty and explain the source gap.
6. After scraping, update `data/offers.json`, summarize counts by market, and upload changed project files to GitHub when requested.

## Project Schema

Maintain this market layout:

```json
{
  "last_updated": "ISO-8601 UTC timestamp",
  "markets": [
    {"key": "mexico", "name": "Mexico", "country": "Mexico", "currency": "MXN", "offers": []},
    {"key": "saudi-arabia", "name": "Saudi Arabia", "country": "Saudi Arabia", "currency": "SAR", "offers": []},
    {"key": "korea", "name": "Korea", "country": "Korea", "currency": "KRW", "offers": []}
  ]
}
```

Each offer should preserve these fields where possible:

```json
{
  "id": "stable-source-market-product-id",
  "market": "mexico|saudi-arabia|korea",
  "market_name": "display market",
  "country": "country",
  "city": "city or Multiple",
  "source": "source name",
  "source_url": "source search or promo URL",
  "product_id": "source product or promo id",
  "retailer": "retailer",
  "item": "offer item",
  "price": "currency amount",
  "regular_price": "regular price when available",
  "currency": "MXN|SAR|KRW",
  "discount": "discount text",
  "offer_details": "extra terms",
  "offer_start_date": "YYYY-MM-DD",
  "offer_month": "Month YYYY",
  "offer_month_key": "YYYY-MM",
  "valid_until": "YYYY-MM-DD",
  "product_url": "product or promo URL",
  "flyer_url": "flyer or promo URL",
  "flyer_url_validated": "Yes|No",
  "flyer_title": "flyer title",
  "flyer_validity": "source validity text",
  "flyer_page": "page text",
  "flyer_total_pages": "page count",
  "flyer_image_url": "image URL",
  "image_url": "product image URL",
  "scraped_at": "ISO-8601 UTC timestamp"
}
```

## Market Notes

- Saudi Arabia: search D4D Jeddah for `Tim Hortons`, parse `a.product-card`, then open each product/flyer link when needed to validate flyer metadata.
- Mexico: parse active offers from the official Tim Hortons Mexico promotions terms page. Normalize Spanish accents internally for date parsing, but keep readable offer titles/details.
- South Korea: do not use press coverage as offer data. Only populate rows from a direct retailer flyer, promotion, or product search source.

## Validation

- Confirm counts by market after every scrape.
- Check that required dashboard columns are populated: date, retailer, item, price, and offer link.
- If Python is unavailable, a one-off PowerShell/.NET scrape may refresh `data/offers.json`, but keep `scraper.py` as the canonical implementation.
