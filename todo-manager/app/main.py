"""Application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from . import models  # noqa: F401  (registers tables with SQLAlchemy)
from .database import Base, engine
from .routers import tasks

INDEX_FILE = Path(__file__).parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # create tables on first run
    yield


app = FastAPI(
    title="Task / To-Do Manager API",
    description="A simple CRUD backend built with FastAPI and SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(tasks.router)


@app.get("/", tags=["Root"])
def root():
    return FileResponse(INDEX_FILE)


@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}
