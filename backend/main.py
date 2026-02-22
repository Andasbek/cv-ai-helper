from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_tables
from backend.api.cv import router as cv_router
from backend.api.jd import router as jd_router
from backend.api.interview import router as interview_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="CV AI Helper API",
    description="API for CV analysis, JD matching, and interview preparation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv_router)
app.include_router(jd_router)
app.include_router(interview_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
