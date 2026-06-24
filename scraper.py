#!/usr/bin/env python3
"""
International Tim Hortons flyer scraper.

Current source coverage:
- Saudi Arabia / Jeddah / D4D Tea & Coffee search for "Tim Hortons"
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).parent / "data"
OFFERS_FILE = DATA_DIR / "offers.json"

SOURCE_D4D_SAUDI_JEDDAH_TEA_COFFEE = (
    "https://d4donline.com/en/saudi-arabia/jeddah/products/43/tea-coffee"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MARKETS: dict[str, dict[str, str]] = {
    "mexico": {
        "name": "Mexico",
        "country": "Mexico",
        "currency": "MXN",
    },
    "saudi-arabia": {
        "name": "Saudi Arabia",
        "country": "Saudi Arabia",
        "currency": "SAR",
    },
    "korea": {
        "name": "Korea",
        "country": "Korea",
        "currency": "KRW",
    },
}

PRODUCT_NAME_OVERRIDES = {
    # D4D leaves these product-title fields blank. Names were validated from
    # the product crop/flyer image after clicking the product detail page.
    "91256619": "Tim Hortons Coffee Capsules 52g",
    "91256622": "Tim Hortons Coffee Assorted 300g",
    "91252332": "Tim Hortons Coffee 300gm",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def blank_data() -> dict[str, Any]:
    return {
        "last_updated": None,
        "markets": [
            {
                "key": key,
                "name": meta["name"],
                "country": meta["country"],
                "currency": meta["currency"],
                "offers": [],
            }
            for key, meta in MARKETS.items()
        ],
    }


def load_offer_data(path: Path = OFFERS_FILE) -> dict[str, Any]:
    if not path.exists():
        return blank_data()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return blank_data()

    known = {market["key"]: market for market in data.get("markets", [])}
    normalized = blank_data()
    normalized["last_updated"] = data.get("last_updated")
    for market in normalized["markets"]:
        previous = known.get(market["key"], {})
        market["offers"] = previous.get("offers", [])
    return normalized


def save_offer_data(data: dict[str, Any], path: Path = OFFERS_FILE) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def replace_market_offers(
    data: dict[str, Any],
    market_key: str,
    offers: list[dict[str, Any]],
) -> dict[str, Any]:
    data = deepcopy(data)
    for market in data["markets"]:
        if market["key"] == market_key:
            market["offers"] = sorted(
                offers,
                key=lambda row: (
                    str(row.get("retailer", "")),
                    str(row.get("item", "")),
                    str(row.get("product_url", "")),
                ),
            )
            data["last_updated"] = utc_now_iso()
            return data
    raise KeyError(f"Unknown market key: {market_key}")


def fetch_soup(url: str, *, params: dict[str, str] | None = None) -> BeautifulSoup:
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def money_from_text(text: str) -> str:
    text = clean_text(text)
    match = re.search(r"\b([A-Z]{3})\s*([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return text
    return f"{match.group(1)} {float(match.group(2)):,.2f}"


def number_from_money(text: str) -> float | None:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text or "")
    return float(match.group(1)) if match else None


def infer_d4d_asset_date(*urls: str) -> str:
    for url in urls:
        match = re.search(r"/(\d{2})/(\d{2})/(\d{2})/", url or "")
        if not match:
            continue
        year = 2000 + int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        try:
            return datetime(year, month, day).date().isoformat()
        except ValueError:
            continue
    return ""


def month_label(date_text: str) -> str:
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").strftime("%B %Y")
    except (TypeError, ValueError):
        return "Unknown"


def infer_name_from_card(card: BeautifulSoup, product_id: str) -> str:
    if product_id in PRODUCT_NAME_OVERRIDES:
        return PRODUCT_NAME_OVERRIDES[product_id]

    title = clean_text(card.select_one(".product-title").get_text(" ", strip=True)) if card.select_one(".product-title") else ""
    if "tim hortons" in title.lower():
        return title

    for attr in ("title", "data-image-title"):
        value = clean_text(card.get(attr))
        if value and value.lower() not in {"available at"}:
            product = re.sub(r"\s+available at.+$", "", value, flags=re.IGNORECASE).strip()
            if product and product.lower() != "available":
                return f"Tim Hortons {product}" if "tim hortons" not in product.lower() else product

    slug = str(card.get("href", "")).rstrip("/").split("/")[-1].replace("-", " ").strip()
    if slug and slug != "top product":
        return f"Tim Hortons {slug.title()}"
    return "Tim Hortons product - review image for exact variant"


def extract_json_ld_product(soup: BeautifulSoup) -> dict[str, Any]:
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text("", strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        records = payload if isinstance(payload, list) else [payload]
        for record in records:
            if isinstance(record, dict) and record.get("@type") == "Product":
                return record
    return {}


def extract_product_details(product_url: str) -> dict[str, Any]:
    soup = fetch_soup(product_url)
    product_json = extract_json_ld_product(soup)
    offer_json = product_json.get("offers", {}) if isinstance(product_json, dict) else {}

    go_to_flyer = ""
    shop_link = soup.select_one("a.shop-now-btn")
    if shop_link and shop_link.get("href"):
        go_to_flyer = urljoin(product_url, shop_link["href"])

    discount = ""
    description = soup.select_one(".description")
    valid_text = clean_text(description.get_text(" ", strip=True)) if description else ""

    price_list_text = clean_text(" ".join(soup.select_one(".price").stripped_strings)) if soup.select_one(".price") else ""
    discount_match = re.search(r"(SAR\s*[0-9]+(?:\.[0-9]+)?)\s*\(([0-9.]+)\s*%\)", price_list_text)
    if discount_match:
        discount = f"{money_from_text(discount_match.group(1))} off ({discount_match.group(2)}%)"

    return {
        "go_to_flyer_url": go_to_flyer,
        "valid_until": offer_json.get("priceValidUntil", ""),
        "validity_text": valid_text,
        "detail_discount": discount,
        "schema_currency": offer_json.get("priceCurrency", ""),
        "schema_price": offer_json.get("price", ""),
        "detail_page_title": clean_text(soup.title.get_text(" ", strip=True)) if soup.title else "",
    }


def validate_flyer_details(flyer_url: str) -> dict[str, str]:
    if not flyer_url:
        return {
            "flyer_url_validated": "No",
            "flyer_title": "",
            "flyer_validity": "",
            "flyer_market_line": "",
            "flyer_page": "",
            "flyer_total_pages": "",
            "flyer_image_url": "",
        }

    soup = fetch_soup(flyer_url)

    page_spread = ""
    total_pages = ""
    for span in soup.find_all("span"):
        text = clean_text(span.get_text(" ", strip=True))
        if re.fullmatch(r"\d+\s*(?:&|and)\s*\d+", text):
            page_spread = text
        total_match = re.search(r"Total\s+(\d+)\s+Pages", text, flags=re.IGNORECASE)
        if total_match:
            total_pages = total_match.group(1)

    info = soup.select_one("#info-popup")
    market_line = clean_text(info.select_one("h2").get_text(" ", strip=True)) if info and info.select_one("h2") else ""
    flyer_title = clean_text(info.select_one("h4").get_text(" ", strip=True)) if info and info.select_one("h4") else ""
    h3_values = [clean_text(node.get_text(" ", strip=True)) for node in soup.select("#info-popup h3")]
    flyer_validity = next((value for value in h3_values if value.lower().startswith("till")), "")

    flyer_img = soup.select_one("img.flyer-img")
    flyer_image_url = urljoin(flyer_url, flyer_img.get("src")) if flyer_img and flyer_img.get("src") else ""

    return {
        "flyer_url_validated": "Yes",
        "flyer_title": flyer_title or (clean_text(soup.title.get_text(" ", strip=True)) if soup.title else ""),
        "flyer_validity": flyer_validity,
        "flyer_market_line": market_line,
        "flyer_page": page_spread,
        "flyer_total_pages": total_pages,
        "flyer_image_url": flyer_image_url,
    }


def parse_d4d_product_card(card: BeautifulSoup, scraped_at: str) -> dict[str, Any]:
    product_id = clean_text(card.get("data-product-id"))
    product_url = urljoin(SOURCE_D4D_SAUDI_JEDDAH_TEA_COFFEE, card.get("href", ""))

    regular_price = money_from_text(card.select_one(".sub_txt").get_text(" ", strip=True)) if card.select_one(".sub_txt") else ""
    price = money_from_text(card.select_one(".product-amount").get_text(" ", strip=True)) if card.select_one(".product-amount") else ""
    discount_pct = clean_text(card.select_one(".offer_tag").get_text(" ", strip=True)) if card.select_one(".offer_tag") else ""
    discount_pct = discount_pct.replace(" %", "%").replace("% Off", "% off")
    retailer = clean_text(card.get("data-pic-desc")) or (
        clean_text(card.select_one(".product-description").get_text(" ", strip=True))
        if card.select_one(".product-description")
        else ""
    )

    product_details = extract_product_details(product_url)
    validated_flyer_url = product_details.get("go_to_flyer_url") or card.get("data-url", "")
    flyer_details = validate_flyer_details(validated_flyer_url)
    image_url = card.get("data-image-tr", "")
    offer_start_date = infer_d4d_asset_date(
        image_url,
        flyer_details.get("flyer_image_url", ""),
        product_url,
        validated_flyer_url,
    )

    price_value = number_from_money(price)
    regular_value = number_from_money(regular_price)
    discount_value = ""
    if regular_value is not None and price_value is not None:
        discount_value = f"SAR {regular_value - price_value:,.2f} off"

    offer_details = [
        detail
        for detail in (
            discount_pct,
            discount_value,
            product_details.get("detail_discount"),
            flyer_details.get("flyer_validity"),
            "D4D notes that prices are AI-generated; official flyer prices prevail.",
        )
        if detail
    ]

    return {
        "id": f"d4d-sa-jeddah-{product_id}",
        "market": "saudi-arabia",
        "market_name": "Saudi Arabia",
        "country": "Saudi Arabia",
        "city": "Jeddah",
        "source": "D4D Online",
        "source_url": f"{SOURCE_D4D_SAUDI_JEDDAH_TEA_COFFEE}?search=Tim+Hortons",
        "product_id": product_id,
        "retailer": retailer,
        "item": infer_name_from_card(card, product_id),
        "price": price,
        "regular_price": regular_price,
        "currency": product_details.get("schema_currency") or "SAR",
        "discount": discount_pct,
        "offer_details": " | ".join(dict.fromkeys(offer_details)),
        "offer_start_date": offer_start_date,
        "offer_month": month_label(offer_start_date),
        "offer_month_key": offer_start_date[:7] if offer_start_date else "unknown",
        "valid_until": product_details.get("valid_until"),
        "product_url": product_url,
        "flyer_url": validated_flyer_url,
        "flyer_url_validated": flyer_details.get("flyer_url_validated"),
        "flyer_title": flyer_details.get("flyer_title"),
        "flyer_validity": flyer_details.get("flyer_validity"),
        "flyer_page": flyer_details.get("flyer_page"),
        "flyer_total_pages": flyer_details.get("flyer_total_pages"),
        "flyer_image_url": flyer_details.get("flyer_image_url"),
        "image_url": image_url,
        "scraped_at": scraped_at,
    }


def scrape_d4d_saudi_tim_hortons() -> list[dict[str, Any]]:
    scraped_at = utc_now_iso()
    soup = fetch_soup(SOURCE_D4D_SAUDI_JEDDAH_TEA_COFFEE, params={"search": "Tim Hortons"})
    cards = soup.select("a.product-card")
    return [parse_d4d_product_card(card, scraped_at) for card in cards]


def scrape_market_to_file(market_key: str = "saudi-arabia") -> dict[str, Any]:
    if market_key != "saudi-arabia":
        raise NotImplementedError(f"No scraper is configured for {MARKETS[market_key]['name']} yet.")
    offers = scrape_d4d_saudi_tim_hortons()
    data = replace_market_offers(load_offer_data(), market_key, offers)
    save_offer_data(data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape international Tim Hortons flyer offers.")
    parser.add_argument(
        "--market",
        choices=["saudi-arabia"],
        default="saudi-arabia",
        help="Market scraper to run.",
    )
    parser.add_argument("--print", action="store_true", help="Print scraped offers as JSON.")
    args = parser.parse_args()

    offers = scrape_d4d_saudi_tim_hortons()
    data = replace_market_offers(load_offer_data(), args.market, offers)
    save_offer_data(data)

    if args.print:
        print(json.dumps(offers, indent=2, ensure_ascii=False))
    else:
        print(f"Saved {len(offers)} {MARKETS[args.market]['name']} offer(s) to {OFFERS_FILE}")


if __name__ == "__main__":
    main()
