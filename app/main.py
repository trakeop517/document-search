from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query, Request, Path, Response
from app.database import SessionFactory, engine
from app.document_service import search_documents, delete_document
from app.schemas import DocumentResponse
from app.search import get_elasticsearch_client
import logging
from elasticsearch import ApiError
from elastic_transport import TransportError
from sqlalchemy.exc import SQLAlchemyError

@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    try:
        async with get_elasticsearch_client() as client:
            application.state.elasticsearch = client
            yield
    finally:
        await engine.dispose()

app = FastAPI(title="Document Search API", description="Сервис поиска по текстам документов", version="0.1.0", lifespan=lifespan)
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/search", response_model=list[DocumentResponse], summary="Поиск документов по тексту")
async def search(request: Request, q: Annotated[str, Query(min_length=1, description="Текст поискового запроса")]) -> list[DocumentResponse]:
    query = q.strip()
    if not query:
        raise HTTPException(
            status_code=422,
            detail="Поисковый запрос не должен быть пустым")
    async with SessionFactory() as session:
        documents = await search_documents(
            query=query,
            session=session,
            client=request.app.state.elasticsearch)
        return [DocumentResponse.model_validate(document) for document in documents]

@app.delete("/documents/{document_id}", status_code=204, response_class=Response, summary="Удаление документа по ID", responses={404: {"description": "Документ не найден"}, 503: {"description": "Хранилище временно недоступно"}})
async def remove_document(document_id: Annotated[int, Path(gt=0)], request: Request) -> Response:
    try:
        async with SessionFactory() as session:
            deleted = await delete_document(document_id=document_id, session=session, client=request.app.state.elasticsearch)
    except (ApiError, TransportError, SQLAlchemyError) as error:
        logging.getLogger(__name__).exception("Ошибка удаления документа %s", document_id)
        raise HTTPException(status_code=503, detail="Не удалось завершить удаление. Повторите запрос позже.") from error
    if not deleted:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return Response(status_code=204)