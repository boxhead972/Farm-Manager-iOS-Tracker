# analysis/check_thresholds.py
import asyncio
import tomllib
from dotenv import load_dotenv

load_dotenv()  # must run before importing repository

from db.repository import pool

QUERY = """
SELECT percentile_cont(%s) WITHIN GROUP (ORDER BY price)
FROM prices
WHERE name = %s AND type = %s;
"""

async def main():
    await pool.open()
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT DISTINCT name, type FROM prices;")
            pairs = await cur.fetchall()

            for name, item_type in pairs:
                pct = 0.9 if item_type == "crop" else 0.1
                await cur.execute(QUERY, (pct, name, item_type))
                result = (await cur.fetchone())[0]

                section = config.get("alerts", {}).get(item_type, {}).get(name, {})
                current = section.get("above" if item_type == "crop" else "below", "not set")

                label = "sell above" if item_type == "crop" else "buy below"
                print(f"{name} ({item_type}) — suggested {label}: {round(result, 2)} | current config: {current}")

    await pool.close()

if __name__ == "__main__":
    asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)