import asyncio
from dotenv import load_dotenv
load_dotenv()
from db.repository import pool

async def check():
    await pool.open()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT DISTINCT name, type FROM prices ORDER BY name LIMIT 20")
            rows = await cur.fetchall()
            for r in rows:
                print(r)
    await pool.close()

if __name__ == "__main__":
    asyncio.run(check(), loop_factory=asyncio.SelectorEventLoop)