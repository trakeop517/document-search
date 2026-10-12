from httpx import AsyncClient
import pytest

async def test_search_results(api_client: AsyncClient) -> None:
    response = await api_client.get("/search", params={"q": "python"})
    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 20
    expected_ids = list(range(26, 6, -1))
    assert [document["id"] for document in documents] == expected_ids
    for document in documents:
        assert set(document) == {"id", "rubrics", "text", "created_date"}
    assert documents[0] == {"id": 26, "rubrics": ["Программирование"], "text": "Документ о Python номер 26", "created_date": "2025-01-26T12:00:00"}

async def test_nomatches(api_client: AsyncClient,) -> None:
    response = await api_client.get("/search", params={"q": "несуществующеесловодлятеста"})
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.parametrize("params", [{}, {"q": ""}, {"q": "   "}], ids=["missing-query", "empty-query", "whitespace-query"])
async def test_query(api_client: AsyncClient, params: dict[str, str]) -> None:
    response = await api_client.get("/search", params=params)
    assert response.status_code == 422