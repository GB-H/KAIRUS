from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from backend.routes.chat import router as chat_router
from backend.database.db import init_db
from backend.middleware import rate_limit_middleware


# Carregar .env antes de tudo
load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(
    title="KAIRUS API",
    description="Backend da plataforma de inteligencia artificial KAIRUS.",
    version="0.3.0",
    lifespan=lifespan,
)


# =========================
# MIDDLEWARE
# =========================

app.middleware("http")(rate_limit_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ROTAS
# =========================

app.include_router(chat_router)


@app.get("/api/status")
async def status():
    from ai.llm import is_available, get_model_name
    return {
        "name": "KAIRUS",
        "version": "0.3.0",
        "status": "online",
        "llm_available": is_available(),
        "llm_model": get_model_name() if is_available() else None,
        "features": [
            "chat",
            "memory",
            "persistence",
            "tools",
            "rate_limiting",
            "llm_hybrid",
        ]
    }


@app.get("/api/health")
async def health():
    return {
        "status": "healthy"
    }


@app.get("/api/tools")
async def list_tools():
    from ai.tools import get_available_tools
    return {"tools": get_available_tools()}


# =========================
# FRONTEND
# =========================

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)