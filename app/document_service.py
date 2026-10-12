from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_scan
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.models import Document
from elasticsearch import NotFoundError

async def search_documents(query: str, session: AsyncSession, client: AsyncElasticsearch) -> list[Document]:
    settings = get_settings()
    document_ids = []
    async for hit in async_scan(client, index=settings.elasticsearch_index, query={"query": {"match": {"text": query}}, "_source": ["id"]}, size=500):
        document_ids.append(hit["_source"]["id"])
    if not document_ids:
        return []
    statement = (select(Document).where(Document.id.in_(document_ids)).order_by(Document.created_date.desc(), Document.id.desc()).limit(20))
    result = await session.scalars(statement)
    return list(result.all())

async def delete_document(document_id: int, session: AsyncSession, client: AsyncElasticsearch) -> bool:
    settings = get_settings()
    async with session.begin():
        statement = (delete(Document).where(Document.id == document_id).returning(Document.id))
        result = await session.execute(statement)
        deleted_from_database = result.scalar_one_or_none() is not None
        deleted_from_index = False
        try:
            response = await client.delete(index=settings.elasticsearch_index, id=str(document_id), refresh="wait_for")
            deleted_from_index = response["result"] == "deleted"
        except NotFoundError as error:
            if (not isinstance(error.body, dict) or error.body.get("result") != "not_found"):
                raise
    return deleted_from_database or deleted_from_index