import asyncio
from scraper.scraper import scrape_prices

async def main():
    data = await scrape_prices()
    print(f"Total records: {len(data)}")
    for row in data[:10]:
        print(row)

asyncio.run(main())