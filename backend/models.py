from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    role: str
    created_at: str


@dataclass
class TokenRecord:
    id: int
    user_id: int
    token: str
    created_at: str


@dataclass
class Workout:
    id: int
    user_id: int
    workout_name: str
    duration_minutes: int
    calories_burned: int
    date: str


@dataclass
class NutritionMeal:
    id: int
    user_id: int
    meal_name: str
    calories: int
    protein: float
    carbs: float
    fats: float
    date: str


@dataclass
class WeightEntry:
    id: int
    user_id: int
    weight_kg: float
    date: str
    created_at: str
