import asyncio
from app.database import engine
from app.models import Base, Document

async def init_db() -> None:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        print("Таблицы PostgreSQL созданы")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())