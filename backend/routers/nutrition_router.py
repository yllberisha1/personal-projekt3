from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, status

from auth import get_current_user
from database import get_database_manager
from schemas import MessageResponse, NutritionCreate, NutritionResponse, NutritionUpdate
from services.nutrition_service import NutritionService

router = APIRouter(tags=["Nutrition"])


def get_nutrition_service() -> NutritionService:
    return NutritionService(get_database_manager())


@router.get("/meals", response_model=list[NutritionResponse], status_code=status.HTTP_200_OK)
def get_meals(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service),
) -> list[NutritionResponse]:
    rows = nutrition_service.list_meals(current_user["id"], start_date, end_date)
    return [NutritionResponse(**row) for row in rows]


@router.post("/meals", response_model=NutritionResponse, status_code=status.HTTP_201_CREATED)
def create_meal(
    payload: NutritionCreate,
    current_user: dict = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service),
) -> NutritionResponse:
    row = nutrition_service.add_meal(current_user["id"], payload)
    return NutritionResponse(**row)


@router.get("/meals/macros", status_code=status.HTTP_200_OK)
def get_daily_macros(
    date: str,
    current_user: dict = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service),
) -> dict:
    return nutrition_service.get_daily_macros(current_user["id"], date)


@router.put("/meals/{meal_id}", response_model=NutritionResponse, status_code=status.HTTP_200_OK)
def update_meal(
    meal_id: int,
    payload: NutritionUpdate,
    current_user: dict = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service),
) -> NutritionResponse:
    row = nutrition_service.update_meal(current_user["id"], meal_id, payload)
    return NutritionResponse(**row)


@router.delete("/meals/{meal_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def delete_meal(
    meal_id: int,
    current_user: dict = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service),
) -> MessageResponse:
    nutrition_service.delete_meal(current_user["id"], meal_id)
    return MessageResponse(message="Meal deleted.")
