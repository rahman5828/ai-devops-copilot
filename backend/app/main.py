from fastapi import FastAPI

from app.api.routes.incident import router as incident_router

app = FastAPI(
    title="AI DevOps Copilot",
    description="AI-powered DevOps assistant for incident analysis and automation.",
    version="0.1.0",
)

app.include_router(incident_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to AI DevOps Copilot 🚀",
        "status": "running",
        "version": "0.1.0",
    }
