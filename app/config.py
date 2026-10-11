import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    elasticsearch_url: str
    elasticsearch_index: str

def get_settings() -> Settings:
    return Settings(
        postgres_db=os.getenv("POSTGRES_DB", "documents"),
        postgres_user=os.getenv("POSTGRES_USER", "search"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "local_search_password"),
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        elasticsearch_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200",),
        elasticsearch_index=os.getenv("ELASTICSEARCH_INDEX", "documents"))