import ast
import asyncio
import csv
from datetime import datetime
from pathlib import Path
from elasticsearch.helpers import async_bulk
from sqlalchemy.dialects.postgresql import insert
from app.config import get_settings
from app.database import SessionFactory, engine
from app.models import Document
from app.search import get_elasticsearch_client

def load_documents(path: Path) -> list[dict]:
    documents = []
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required_fields = {"text", "created_date", "rubrics"}
        if not required_fields.issubset(reader.fieldnames or []):
            raise ValueError("CSV должен содержать поля text, created_date, rubrics")
        for document_id, row in enumerate(reader, start=1):
            if None in row or any(
                row.get(field) is None for field in required_fields):
                raise ValueError(f"Неправильная структура CSV в записи {document_id}")
            text = row["text"]
            if not text.strip(): raise ValueError(f"Пустой текст в записи: {document_id}")
            try:
                rubrics = ast.literal_eval(row["rubrics"])
                created_date = datetime.strptime(row["created_date"], "%Y-%m-%d %H:%M:%S")
            except (ValueError, SyntaxError) as error:
                raise ValueError(
                    f"Неверные рубрики или дата в записи {document_id}") from error
            if not isinstance(rubrics, list) or not all(isinstance(rubric, str) for rubric in rubrics):
                raise ValueError(f"Rubrics must be a list of strings at record {document_id}")
            documents.append({"id": document_id, "rubrics": rubrics, "text": text, "created_date": created_date})
    if not documents:
        raise ValueError("В CSV нет документов")
    return documents

async def import_data() -> None:
    try:
        settings = get_settings()
        documents = load_documents(Path("/app/data/posts.csv"))
        print(f"CSV проверен: {len(documents)}")
        async with get_elasticsearch_client() as client:
            if not await client.indices.exists(index=settings.elasticsearch_index):
                raise RuntimeError("Поисковый индекс не существует, сначала выполните python -m app.init_index")
            statement = insert(Document).values(documents)
            statement = statement.on_conflict_do_update(
                index_elements=[Document.id],
                set_={"rubrics": statement.excluded.rubrics,"text": statement.excluded.text, "created_date": statement.excluded.created_date})
            async with SessionFactory.begin() as session:
                await session.execute(statement)
            print(f"Сохранено: {len(documents)}")
            actions = ({"_op_type": "index", "_index": settings.elasticsearch_index, "_id": str(document["id"]), "_source": {"id": document["id"], "text": document["text"]}} for document in documents)
            indexed, _ = await async_bulk(client, actions, chunk_size=500, refresh="wait_for")
            print(f"Проиндексировано: {indexed}")
            result = await client.count(index=settings.elasticsearch_index)
            print(f"Всего документов: {result['count']}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(import_data())