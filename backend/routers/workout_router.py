from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, status

from auth import get_current_user
from database import get_database_manager
from schemas import MessageResponse, WorkoutCreate, WorkoutResponse, WorkoutUpdate
from services.workout_service import WorkoutService

router = APIRouter(tags=["Workouts"])


def get_workout_service() -> WorkoutService:
    return WorkoutService(get_database_manager())


@router.get("/workouts", response_model=list[WorkoutResponse], status_code=status.HTTP_200_OK)
def get_workouts(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
) -> list[WorkoutResponse]:
    rows = workout_service.list_workouts(current_user["id"], start_date, end_date)
    return [WorkoutResponse(**row) for row in rows]


@router.post("/workouts", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(
    payload: WorkoutCreate,
    current_user: dict = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
) -> WorkoutResponse:
    row = workout_service.add_workout(current_user["id"], payload)
    return WorkoutResponse(**row)


@router.get("/workouts/weekly-calories", status_code=status.HTTP_200_OK)
def weekly_calories(
    current_user: dict = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
) -> dict:
    return {"weekly_calories_burned": workout_service.get_weekly_calories_burned(current_user["id"])}


@router.get("/workouts/frequency", status_code=status.HTTP_200_OK)
def workout_frequency(
    current_user: dict = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
) -> list[dict]:
    return workout_service.get_workout_frequency_by_week(current_user["id"])


@router.put("/workouts/{workout_id}", response_model=WorkoutResponse, status_code=status.HTTP_200_OK)
def update_workout(
    workout_id: int,
    payload: WorkoutUpdate,
    current_user: dict = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
) -> WorkoutResponse:
    row = workout_service.update_workout(current_user["id"], workout_id, payload)
    return WorkoutResponse(**row)


@router.delete("/workouts/{workout_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def delete_workout(
    workout_id: int,
    current_user: dict = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
) -> MessageResponse:
    workout_service.delete_workout(current_user["id"], workout_id)
    return MessageResponse(message="Workout deleted.")
