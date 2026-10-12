from collections.abc import AsyncIterator
from datetime import datetime, timedelta
import pytest_asyncio
from elasticsearch.helpers import async_bulk
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, insert, text
from app.config import get_settings
from app.database import SessionFactory, engine
from app.init_index import init_index
from app.main import app, lifespan
from app.models import Base, Document

@pytest_asyncio.fixture
async def api_client() -> AsyncIterator[AsyncClient]:
    settings = get_settings()
    if (settings.postgres_db != "documents_test" or settings.elasticsearch_index != "documents_test"):
        raise RuntimeError("Тесты должны использовать только тестовую БД и индекс")
    async with lifespan(app):
        search_client = app.state.elasticsearch
        async with engine.begin() as connection:
            database_name = await connection.scalar(
                text("SELECT current_database()"))
            if database_name != "documents_test":
                raise RuntimeError("Подключение установлено не к тестовой БД")
            await connection.run_sync(Base.metadata.create_all)
        try:
            async with SessionFactory.begin() as session:
                await session.execute(delete(Document))
            await search_client.options(ignore_status=404,).indices.delete(index=settings.elasticsearch_index,)
            await init_index()
            base_date = datetime(2025, 1, 1, 12, 0, 0)
            documents = [{"id": document_id, "rubrics": ["Программирование"], "text": f"Документ о Python номер {document_id}", "created_date": base_date + timedelta(days=min(document_id, 25))} for document_id in range(1, 27)]
            documents.append({"id": 100, "rubrics": ["Садоводство"], "text": "Выращивание растений в саду", "created_date": datetime(2026, 1, 1, 12, 0, 0)})
            async with SessionFactory.begin() as session:
                await session.execute(insert(Document), documents)
            actions = ({"_op_type": "index", "_index": settings.elasticsearch_index, "_id": str(document["id"]), "_source": {"id": document["id"], "text": document["text"]}}
                for document in documents)
            await async_bulk(search_client, actions, refresh="wait_for")
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client
        finally:
            async with SessionFactory.begin() as session:
                await session.execute(delete(Document))
            await search_client.options(ignore_status=404).indices.delete(index=settings.elasticsearch_index)