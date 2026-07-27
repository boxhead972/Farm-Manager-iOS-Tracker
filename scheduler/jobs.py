# scheduler/jobs.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper.scraper import scrape_prices
from db.repository import insert_prices
from bot.bot import check_and_alert

async def scrape_and_store():
    data = await scrape_prices()
    rows = [(r["timestamp"], r["name"], r["type"], r["price"]) for r in data]
    await insert_prices(rows)
    await check_and_alert(data)

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scrape_and_store, "interval", minutes=15)
    scheduler.start()
    return scheduler
