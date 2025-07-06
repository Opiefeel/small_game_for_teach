
import asyncio
from app.database import engine
from app.models import Base

async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Тут создай таблицы через запуск
if __name__ == "__main__":
    asyncio.run(create_all())
