from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (async_sessionmaker, create_async_engine)
from app.config import get_settings

settings = get_settings()
database_url = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_db)
engine = create_async_engine(database_url, pool_pre_ping=True)
SessionFactory = async_sessionmaker(bind=engine,expire_on_commit=False)