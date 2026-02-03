import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../../portfolio.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                symbol TEXT,
                shares INTEGER,
                avg_price REAL
            )
        """)
        # Insert test data if the table is empty
        cursor = await db.execute("SELECT COUNT(*) FROM portfolio")
        if (await cursor.fetchone())[0] == 0:
            await db.execute("INSERT INTO portfolio (user_id, symbol, shares, avg_price) VALUES ('user123', 'AAPL', 10, 150.5)")
            await db.execute("INSERT INTO portfolio (user_id, symbol, shares, avg_price) VALUES ('user123', 'NVDA', 5, 450.0)")
            await db.commit()

async def get_portfolio(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM portfolio WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]