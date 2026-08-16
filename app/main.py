from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.dependencies import database
from app.api.routes.receipts import router as receipts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.create_tables()
    yield


app = FastAPI(
    title="Smart Receipt Analyzer",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(receipts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok"
    }