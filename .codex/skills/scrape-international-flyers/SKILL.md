---
name: scrape-international-flyers
description: Scrape and maintain Tim Hortons retailer flyer offers for Saudi Arabia using D4D Jeddah search. Use when Codex needs to find current Saudi Arabia Tim Hortons offers, run a test scrape, update the International Flyer Scrapper project data, preserve the dashboard offer schema, or upload detected Saudi offers to GitHub.
---

# Scrape Saudi Arabia Flyers

## Workflow

1. Read the tracker project files before editing:
   - `scraper.py`
   - `data/offers.json`
   - `app.py` when changing displayed columns.
2. Use the Saudi Arabia source in `references/sources.md`.
3. Keep the offer schema stable. Each offer must include dates, retailer, item, price, and a link to the offer, plus the existing optional fields used by the dashboard.
4. Treat source pages as volatile. Run a live scrape before updating `data/offers.json`; do not rely only on previous saved data.
5. Do not invent offers. If D4D returns no Tim Hortons product cards, keep Saudi Arabia offers empty and report that no current D4D offers were detected.
6. After scraping, update the Saudi Arabia offers in `data/offers.json`, summarize the Saudi count, and upload changed project files to GitHub when requested.

## Project Schema

Maintain this Saudi Arabia market layout:

```json
{
  "last_updated": "ISO-8601 UTC timestamp",
  "markets": [
    {"key": "saudi-arabia", "name": "Saudi Arabia", "country": "Saudi Arabia", "currency": "SAR", "offers": []}
  ]
}
```

Each offer should preserve these fields where possible:

```json
{
  "id": "stable-source-market-product-id",
  "market": "saudi-arabia",
  "market_name": "Saudi Arabia",
  "country": "Saudi Arabia",
  "city": "Jeddah",
  "source": "D4D Online",
  "source_url": "D4D search URL",
  "product_id": "D4D product id",
  "retailer": "retailer",
  "item": "offer item",
  "price": "SAR amount",
  "regular_price": "regular price when available",
  "currency": "SAR",
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

## Saudi Arabia Notes

- Search D4D Jeddah for `Tim Hortons`.
- Parse `a.product-card` elements from the Tea & Coffee product results.
- Use card attributes for product ID, retailer, product image, and initial flyer URL.
- Use `.sub_txt`, `.product-amount`, and `.offer_tag` for regular price, current price, and discount.
- Open product/flyer links when needed to validate flyer title, page, validity, and flyer image metadata.
- Keep D4D's disclaimer in `offer_details`: prices may be AI-generated and official flyer prices prevail.

## Validation

- Confirm the Saudi Arabia offer count after every scrape.
- Check that required dashboard columns are populated: date, retailer, item, price, and offer link.
- If Python is unavailable, a one-off PowerShell/.NET scrape may refresh `data/offers.json`, but keep `scraper.py` as the canonical implementation.
