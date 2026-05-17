from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.main import router
from app.core.config import APP_VERSION

app = FastAPI(
    title="HireEdge API",
    description="AI-powered job application agent — CV tailoring, cover letters, and autonomous job hunting.",
    version=APP_VERSION,
)

# CORS — allow Flutter app and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "HireEdge API",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }
