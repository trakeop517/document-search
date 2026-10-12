import asyncio
from app.config import get_settings
from app.search import get_elasticsearch_client

async def init_index() -> None:
    settings = get_settings()
    index_name = settings.elasticsearch_index
    async with get_elasticsearch_client() as client:
        if await client.indices.exists(index=index_name):
            print(f"Index already exists: {index_name}")
            return
        await client.indices.create(index=index_name, settings={"number_of_shards": 1, "number_of_replicas": 0}, mappings={"properties": {"id": {"type": "long",}, "text": {"type": "text", "analyzer": "russian"}}})
        print(f"Index created: {index_name}")

if __name__ == "__main__":
    asyncio.run(init_index())