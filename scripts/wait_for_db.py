import asyncio
import asyncpg
import os
import sys

async def wait_for_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        sys.exit(1)
    # преобразуем postgresql+asyncpg:// -> postgresql://
    dsn = db_url.replace("postgresql+asyncpg://", "postgresql://")
    while True:
        try:
            conn = await asyncpg.connect(dsn)
            await conn.close()
            print("Database is ready")
            break
        except Exception as e:
            print(f"Waiting for database... {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(wait_for_db())