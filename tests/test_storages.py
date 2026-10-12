from sqlalchemy import text
from app.config import get_settings
from app.database import engine
from app.search import get_elasticsearch_client

async def test_storage_connections() -> None:
    settings = get_settings()
    assert settings.postgres_db == "documents_test"
    assert settings.elasticsearch_index == "documents_test"
    try:
        async with engine.connect() as connection:
            database_name = await connection.scalar(text("SELECT current_database()"))
            assert database_name == "documents_test"
        async with get_elasticsearch_client() as client:
            info = await client.info()
            assert info["version"]["number"] == "8.17.1"
    finally:
        await engine.dispose()