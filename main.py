# main.py
import os
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()  # must run before db.repository import

from db.repository import pool
from bot.bot import bot
from scheduler.jobs import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    await pool.open(wait=True, timeout=10)

    bot_task = asyncio.create_task(bot.start(os.environ["DISCORD_TOKEN"]))

    ready_task = asyncio.create_task(bot.wait_until_ready())
    done, pending = await asyncio.wait(
        {bot_task, ready_task}, return_when=asyncio.FIRST_COMPLETED
    )

    if bot_task in done:
        bot_task.result()

    logger.info("Bot ready — starting scheduler")

    scheduler = start_scheduler()

    try:
        await bot_task
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down...")
        scheduler.shutdown()
        await bot.close()
        await pool.close()


if __name__ == "__main__":
    try:
        asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
    except KeyboardInterrupt:
        pass