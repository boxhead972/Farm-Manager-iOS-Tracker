"""
scraper/scraper.py
Scrapes crop/seed prices from webapp.farmmanager.cc
"""
from datetime import datetime, timezone
import re
import httpx
from bs4 import BeautifulSoup

URL = "https://webapp.farmmanager.cc"


async def scrape_prices() -> list[dict]:
    """
    Fetch and parse crop/seed prices.

    Fields extracted per record:
      - name: str   (crop name, e.g. "Wheat")
      - type: str   ('seed' or 'crop')
      - price: float

    Returns: list[dict]
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(URL)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "lxml")
    results = []
    ts = datetime.now(timezone.utc)

    for row in soup.select("div.result-row"):
        name_el = row.select_one("span.crop-name")
        if not name_el:
            continue
        name = name_el.get_text(strip=True)

        # Seed price: "Cost/kg: <span class="font-mono">2.87</span>"
        seed_price = _extract_price(row, "Cost/kg:")
        if seed_price is not None:
            results.append({"timestamp": ts, "name": name, "type": "seed", "price": seed_price})

        # Crop price: "Sell/1k: <span class="font-mono">1016.70</span>"
        crop_price = _extract_price(row, "Sell/1k:")
        if crop_price is not None:
            results.append({"timestamp": ts, "name": name, "type": "crop", "price": crop_price})

    return results


def _extract_price(row, label: str) -> float | None:
    """Find a <p> containing label text, return the numeric value from its font-mono span."""
    for p in row.find_all("p"):
        if label in p.get_text():
            span = p.find("span", class_="font-mono")
            if span:
                raw = span.get_text(strip=True).replace(",", "").replace(" ", "")
                try:
                    return float(raw)
                except ValueError:
                    return None
    return None

if __name__ == "__main__":
    import asyncio

    async def main():
        data = await scrape_prices()
        print(f"Total records: {len(data)}")
        for row in data[:10]:
            print(row)

    asyncio.run(main())