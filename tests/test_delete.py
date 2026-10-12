import pytest
from httpx import AsyncClient
from app.config import get_settings
from app.database import SessionFactory
from app.main import app
from app.models import Document

async def test_delete_success(api_client: AsyncClient) -> None:
    response = await api_client.delete("/documents/1")
    assert response.status_code == 204
    assert response.content == b""
    async with SessionFactory() as session:
        document = await session.get(Document, 1)
        assert document is None
    settings = get_settings()
    search_client = app.state.elasticsearch
    exists = await search_client.exists(index=settings.elasticsearch_index, id="1")
    assert not bool(exists)
    repeated_response = await api_client.delete("/documents/1")
    assert repeated_response.status_code == 404
    assert repeated_response.json() == {"detail": "Документ не найден"}

async def test_delete_missing(api_client: AsyncClient) -> None:
    response = await api_client.delete("/documents/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Документ не найден"}

@pytest.mark.parametrize("document_id", [0, -1])
async def test_delete_invalid_id(api_client: AsyncClient, document_id: int) -> None:
    response = await api_client.delete(f"/documents/{document_id}")
    assert response.status_code == 422