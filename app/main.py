from fastapi import FastAPI

app = FastAPI(title="Document Search API", description="Сервис поиска по текстам документов", version="0.1.0")
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}