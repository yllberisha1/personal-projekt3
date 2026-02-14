from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[A-Za-z0-9_]+$",
        description="Unique username with letters, numbers, and underscores.",
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Valid email address.",
    )
    password: str = Field(..., min_length=6, max_length=128)

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "fit_user",
                "email": "fit_user@example.com",
                "password": "StrongPass123",
            }
        }
    }


class UserLogin(BaseModel):
    username_or_email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=6, max_length=128)

    model_config = {
        "json_schema_extra": {
            "example": {
                "username_or_email": "fit_user",
                "password": "StrongPass123",
            }
        }
    }


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    username: str
    user_id: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "n1X....",
                "token_type": "bearer",
                "username": "fit_user",
                "user_id": 1,
            }
        }
    }


class MessageResponse(BaseModel):
    message: str


class WorkoutCreate(BaseModel):
    workout_name: str = Field(..., min_length=1, max_length=100)
    duration_minutes: int = Field(..., gt=0, le=600)
    calories_burned: int = Field(..., ge=0, le=5000)
    date: date

    model_config = {
        "json_schema_extra": {
            "example": {
                "workout_name": "Running",
                "duration_minutes": 45,
                "calories_burned": 430,
                "date": "2026-02-10",
            }
        }
    }


class WorkoutUpdate(BaseModel):
    workout_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    duration_minutes: Optional[int] = Field(default=None, gt=0, le=600)
    calories_burned: Optional[int] = Field(default=None, ge=0, le=5000)
    date: Optional[date] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "workout_name": "Cycling",
                "duration_minutes": 35,
                "calories_burned": 390,
                "date": "2026-02-11",
            }
        }
    }


class WorkoutResponse(BaseModel):
    id: int
    user_id: int
    workout_name: str
    duration_minutes: int
    calories_burned: int
    date: date


class NutritionCreate(BaseModel):
    meal_name: str = Field(..., min_length=1, max_length=100)
    calories: int = Field(..., ge=0, le=10000)
    protein: float = Field(..., ge=0, le=1000)
    carbs: float = Field(..., ge=0, le=1000)
    fats: float = Field(..., ge=0, le=1000)
    date: date

    model_config = {
        "json_schema_extra": {
            "example": {
                "meal_name": "Chicken Salad",
                "calories": 420,
                "protein": 36.5,
                "carbs": 20.0,
                "fats": 18.0,
                "date": "2026-02-10",
            }
        }
    }


class NutritionUpdate(BaseModel):
    meal_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    calories: Optional[int] = Field(default=None, ge=0, le=10000)
    protein: Optional[float] = Field(default=None, ge=0, le=1000)
    carbs: Optional[float] = Field(default=None, ge=0, le=1000)
    fats: Optional[float] = Field(default=None, ge=0, le=1000)
    date: Optional[date] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "meal_name": "Oatmeal",
                "calories": 320,
                "protein": 13.5,
                "carbs": 51.0,
                "fats": 7.0,
                "date": "2026-02-11",
            }
        }
    }


class NutritionResponse(BaseModel):
    id: int
    user_id: int
    meal_name: str
    calories: int
    protein: float
    carbs: float
    fats: float
    date: date


class WeightCreate(BaseModel):
    weight_kg: float = Field(..., gt=0, le=500)
    date: date

    model_config = {
        "json_schema_extra": {
            "example": {
                "weight_kg": 72.4,
                "date": "2026-02-10",
            }
        }
    }


class WeightUpdate(BaseModel):
    weight_kg: Optional[float] = Field(default=None, gt=0, le=500)
    date: Optional[date] = None


class WeightResponse(BaseModel):
    id: int
    user_id: int
    weight_kg: float
    date: date
    created_at: str


class DashboardResponse(BaseModel):
    username: str
    total_workouts: int
    total_calories_burned: int
    total_calories_consumed: int
