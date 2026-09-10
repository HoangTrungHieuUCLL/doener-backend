import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, exercises, plan, sessions, stats, together

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Doener API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(plan.router)
app.include_router(sessions.router)
app.include_router(stats.router)
app.include_router(together.router)


@app.get("/health")
def health():
    return {"status": "ok"}
