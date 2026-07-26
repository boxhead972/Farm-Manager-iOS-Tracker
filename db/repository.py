import os
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.environ["DATABASE_URL"]
pool = AsyncConnectionPool(
    DATABASE_URL,
    open=False,
    min_size=0,
    max_size=5,
    timeout=10,
)


async def insert_prices(rows: list[tuple]) -> None:
    """rows: list of (timestamp, name, type, price) tuples."""
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(
                "INSERT INTO prices (timestamp, name, type, price) VALUES (%s, %s, %s, %s)",
                rows,
            )


async def get_latest(name: str, type: str) -> dict | None:
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT timestamp, name, type, price
                FROM prices
                WHERE name = %s AND type = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (name, type),
            )
            row = await cur.fetchone()
            if row is None:
                return None
            return {"timestamp": row[0], "name": row[1], "type": row[2], "price": row[3]}


async def get_trend(name: str, type: str, hours: int) -> list[dict]:
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT date_trunc('hour', timestamp) AS bucket, avg(price) AS avg_price
                FROM prices
                WHERE name = %s AND type = %s
                  AND timestamp >= now() - (%s * interval '1 hour')
                GROUP BY bucket
                ORDER BY bucket
                """,
                (name, type, hours),
            )
            rows = await cur.fetchall()
            return [{"bucket": r[0], "avg_price": r[1]} for r in rows]
            
async def get_all_names() -> list[str]:
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT DISTINCT name FROM prices ORDER BY name")
            rows = await cur.fetchall()
            return [r[0] for r in rows]
