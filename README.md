# Tim Hortons International Flyer Tracker

Streamlit dashboard and scraper for Tim Hortons CPG flyer offers outside Canada.

The app is structured around three starting markets:

- Mexico
- Saudi Arabia
- Korea

Saudi Arabia currently scrapes D4D Online for Jeddah Tea & Coffee offers by searching
`Tim Hortons`, opening each product, extracting the validated `Go to flyer` link,
and saving the associated retailer, price, discount, product link, flyer link,
flyer title, page spread, and validity details.

## Setup

```powershell
pip install -r requirements.txt
```

## Run The Dashboard

```powershell
streamlit run app.py
```

## Run The Saudi Arabia Scrape

```powershell
python scraper.py --market saudi-arabia --print
```

Results are saved to `data/offers.json`.
