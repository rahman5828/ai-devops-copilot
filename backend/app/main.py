from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.incident import router as incident_router
from app.database.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI DevOps Copilot",
    description="AI-powered DevOps assistant for incident analysis and automation.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(incident_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to AI DevOps Copilot 🚀",
        "status": "running",
        "version": "0.1.0",
    }
