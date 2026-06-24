"""
Tim Hortons International Flyer Tracker - Streamlit UI
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from scraper import MARKETS, load_offer_data


APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "assets" / "tim-hortons-logo.svg"


st.set_page_config(
    page_title="Tim Hortons International Flyer Tracker",
    page_icon=":coffee:",
    layout="wide",
)


def load_logo_svg() -> str:
    try:
        return LOGO_PATH.read_text(encoding="utf-8")
    except OSError:
        return "<strong>Tim Hortons</strong>"


def format_display_date(value: str | None) -> str:
    if not value:
        return "Not yet"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value[:10]
    return parsed.strftime("%b %d, %Y")


def flyer_display_url(url: str | None, page: str | None) -> str:
    if not url:
        return ""
    page_label = f"Page {page}" if page else "Page"
    return f"{url}#{page_label}"


def offers_to_df(offers: list[dict]) -> pd.DataFrame:
    if not offers:
        return pd.DataFrame(
            columns=[
                "Image",
                "Month",
                "Offer Start",
                "Valid Until",
                "Retailer",
                "Item",
                "Price",
                "Regular Price",
                "Discount",
                "Offer Details",
                "Flyer",
                "Product",
                "Flyer Title",
                "Flyer Page",
                "Scraped At",
                "Month Key",
            ]
        )

    df = pd.DataFrame(offers)
    return pd.DataFrame(
        {
            "Image": df.get("image_url", ""),
            "Month": df.get("offer_month", "Unknown"),
            "Offer Start": df.get("offer_start_date", ""),
            "Valid Until": df.get("valid_until", ""),
            "Retailer": df.get("retailer", ""),
            "Item": df.get("item", ""),
            "Price": df.get("price", ""),
            "Regular Price": df.get("regular_price", ""),
            "Discount": df.get("discount", ""),
            "Offer Details": df.get("offer_details", ""),
            "Flyer": [
                flyer_display_url(url, page)
                for url, page in zip(
                    df.get("flyer_url", [""] * len(df)),
                    df.get("flyer_page", [""] * len(df)),
                )
            ],
            "Product": df.get("product_url", ""),
            "Flyer Title": df.get("flyer_title", ""),
            "Flyer Page": df.get("flyer_page", ""),
            "Scraped At": df.get("scraped_at", ""),
            "Month Key": df.get("offer_month_key", "unknown"),
        }
    )


def month_sort_key(month_label: str) -> str:
    try:
        return datetime.strptime(month_label, "%B %Y").strftime("%Y-%m")
    except ValueError:
        return "9999-99"


def render_market_section(
    market: dict,
    query: str,
    selected_months: list[str],
    selected_retailers: list[str],
) -> None:
    offers = market.get("offers", [])
    df = offers_to_df(offers)

    if query.strip() and not df.empty:
        needle = query.strip()
        mask = (
            df["Item"].str.contains(needle, case=False, na=False)
            | df["Retailer"].str.contains(needle, case=False, na=False)
            | df["Offer Details"].str.contains(needle, case=False, na=False)
        )
        df = df[mask]

    if selected_months and not df.empty:
        df = df[df["Month"].isin(selected_months)]

    if selected_retailers and not df.empty:
        df = df[df["Retailer"].isin(selected_retailers)]

    with st.container():
        left, right = st.columns([4, 1])
        with left:
            st.subheader(market["name"])
        with right:
            st.metric("Offers", len(df))

        if df.empty:
            st.info("No offers loaded yet.")
            return

        visible_columns = [
            "Image",
            "Month",
            "Offer Start",
            "Valid Until",
            "Retailer",
            "Item",
            "Price",
            "Regular Price",
            "Discount",
            "Offer Details",
            "Flyer",
        ]

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_order=visible_columns,
            column_config={
                "Image": st.column_config.ImageColumn("Image", width="small"),
                "Month": st.column_config.TextColumn("Month", width="small"),
                "Offer Start": st.column_config.TextColumn("Start", width="small"),
                "Valid Until": st.column_config.TextColumn("Valid Until", width="small"),
                "Retailer": st.column_config.TextColumn("Retailer", width="medium"),
                "Item": st.column_config.TextColumn("Item", width="large"),
                "Price": st.column_config.TextColumn("Price", width="small"),
                "Regular Price": st.column_config.TextColumn("Regular", width="small"),
                "Discount": st.column_config.TextColumn("Discount", width="small"),
                "Offer Details": st.column_config.TextColumn("Offer Details", width="large"),
                "Flyer": st.column_config.LinkColumn("Flyer", display_text="#(Page.*)$"),
                "Product": st.column_config.LinkColumn("Product", display_text="Open product"),
                "Flyer Title": st.column_config.TextColumn("Flyer Title", width="medium"),
                "Flyer Page": st.column_config.TextColumn("Page", width="small"),
                "Scraped At": st.column_config.TextColumn("Scraped At", width="medium"),
            },
        )

        st.download_button(
            f"Download {market['name']} CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"tim_hortons_{market['key'].replace('-', '_')}_offers.csv",
            mime="text/csv",
            key=f"download_{market['key']}",
        )
    st.divider()


st.markdown(
    """
    <style>
    :root {
        --fresh-white: #FFFCF8;
        --always-red: #C8102E;
        --donut-cream: #F2E4D4;
        --french-vanilla: #E7D7AA;
        --maple-glaze: #9A6437;
        --warm-red: #8D1727;
        --roasted-espresso: #3A2020;
        --soft-border: #E8D8C8;
        --muted-text: #725C52;
    }
    .stApp {
        background:
            linear-gradient(180deg, rgba(255, 252, 248, 0.98) 0%, rgba(250, 244, 236, 0.95) 100%);
    }
    .block-container {
        padding-top: 1.15rem;
        padding-bottom: 2rem;
        max-width: 1380px;
    }
    .th-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: .9rem 1rem;
        margin-bottom: .75rem;
        border: 1px solid var(--soft-border);
        border-left: 5px solid var(--always-red);
        border-radius: 8px;
        background: rgba(255, 255, 255, .72);
    }
    .th-logo {
        width: 126px;
        flex: 0 0 auto;
        overflow: hidden;
    }
    .th-logo svg {
        width: 126px !important;
        height: auto !important;
        max-height: 34px;
        display: block;
    }
    .th-title h1 {
        color: var(--roasted-espresso);
        font-size: 1.5rem;
        margin: 0;
        line-height: 1.2;
        font-weight: 760;
    }
    .th-title p {
        margin: .24rem 0 0 0;
        color: var(--muted-text);
        font-size: .9rem;
    }
    h2, h3 {
        color: var(--roasted-espresso);
    }
    [data-testid="stSidebar"] {
        background: #F6E9DB;
        border-right: 1px solid var(--soft-border);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--warm-red);
    }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, .68);
        border: 1px solid var(--soft-border);
        border-radius: 8px;
        padding: .75rem .85rem;
    }
    div[data-testid="stMetricValue"] {
        color: var(--warm-red);
        font-size: 1.18rem;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--muted-text);
    }
    .stDownloadButton {
        margin-top: .35rem;
    }
    .stDownloadButton button {
        border-color: var(--always-red);
        color: var(--always-red);
        background: rgba(255, 255, 255, .75);
    }
    .stDownloadButton button:hover {
        border-color: var(--warm-red);
        color: var(--warm-red);
        background: #FFF7EF;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--soft-border);
        border-radius: 8px;
        overflow: hidden;
        background: #FFFFFF;
    }
    .stAlert {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="th-header">
        <div class="th-logo">{load_logo_svg()}</div>
        <div class="th-title">
            <h1>International Flyer Tracker</h1>
            <p>Tim Hortons CPG offer tracking across Mexico, Saudi Arabia, and Korea</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

data = load_offer_data()
markets = data.get("markets", [])
all_offers = [offer for market in markets for offer in market.get("offers", [])]
all_df = pd.DataFrame(all_offers)

with st.sidebar:
    st.header("Filters")
    query = st.text_input("Search", placeholder="Item, retailer, offer detail")

    month_options = (
        sorted(all_df["offer_month"].dropna().unique().tolist(), key=month_sort_key)
        if not all_df.empty and "offer_month" in all_df
        else []
    )
    selected_months = st.multiselect("Month", month_options, default=month_options)

    retailer_options = (
        sorted(all_df["retailer"].dropna().unique().tolist())
        if not all_df.empty and "retailer" in all_df
        else []
    )
    selected_retailers = st.multiselect("Retailer", retailer_options, default=retailer_options)

st.divider()

metric_cols = st.columns(4)
metric_cols[0].metric("Total Offers", len(all_offers))
metric_cols[1].metric(
    "Retailers",
    all_df["retailer"].nunique() if not all_df.empty and "retailer" in all_df else 0,
)
metric_cols[2].metric(
    "Markets With Offers",
    sum(1 for market in markets if market.get("offers")),
)
metric_cols[3].metric("Last Updated", format_display_date(data.get("last_updated")))

for market_key in ("mexico", "saudi-arabia", "korea"):
    market = next(
        (
            item
            for item in markets
            if item.get("key") == market_key
        ),
        {
            "key": market_key,
            "name": MARKETS[market_key]["name"],
            "offers": [],
        },
    )
    render_market_section(market, query, selected_months, selected_retailers)
