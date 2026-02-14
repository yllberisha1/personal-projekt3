from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import get_database_manager
from routers import nutrition_router, user_router, workout_router

app = FastAPI(
    title="Fitness Web App API",
    version="1.0.0",
    description="FastAPI backend for workouts, nutrition, and user progress tracking.",
)

# Initialize database and tables at startup.
get_database_manager().init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router.router)
app.include_router(workout_router.router)
app.include_router(nutrition_router.router)


@app.get("/", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok", "message": "Fitness API is running."}
