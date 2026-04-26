import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Medical Diagnosis Multi-Agent System",
    description="Multi-agent collaborative medical diagnosis with GraphRAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import chat, diagnosis

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(diagnosis.router, prefix="/api", tags=["Diagnosis"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "MedicalAgent"}
