from elasticsearch import AsyncElasticsearch
from app.config import get_settings

def get_elasticsearch_client() -> AsyncElasticsearch:
    settings = get_settings()
    return AsyncElasticsearch(hosts=[settings.elasticsearch_url], request_timeout=30)