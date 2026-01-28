from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.models import Base
import os

# Use /data directory for persistence in Amvera, or local directory for dev
DB_PATH = "/data/mvp.db" if os.path.exists("/data") else "mvp.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
