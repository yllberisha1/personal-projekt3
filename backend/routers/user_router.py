from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, status

from auth import AuthService, get_auth_service, get_current_token, get_current_user
from database import get_database_manager
from schemas import (
    DashboardResponse,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    WeightCreate,
    WeightResponse,
    WeightUpdate,
)
from services.user_service import UserService

router = APIRouter(tags=["Users & Auth"])


def get_user_service() -> UserService:
    return UserService(get_database_manager())


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    auth_service.create_user(payload)
    return MessageResponse(message="User registered successfully.")


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_user(
    payload: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return TokenResponse(**auth_service.authenticate_user(payload))


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def logout_user(
    _current_user: dict = Depends(get_current_user),
    token: str = Depends(get_current_token),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    auth_service.logout(token)
    return MessageResponse(message="Logged out successfully.")


@router.get("/dashboard", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
def get_dashboard(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> DashboardResponse:
    return DashboardResponse(**user_service.get_dashboard_stats(current_user["id"]))


@router.get("/weights", response_model=list[WeightResponse], status_code=status.HTTP_200_OK)
def list_weights(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> list[WeightResponse]:
    rows = user_service.list_weight_entries(current_user["id"], start_date, end_date)
    return [WeightResponse(**row) for row in rows]


@router.post("/weights", response_model=WeightResponse, status_code=status.HTTP_201_CREATED)
def create_weight(
    payload: WeightCreate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> WeightResponse:
    row = user_service.add_weight_entry(current_user["id"], payload)
    return WeightResponse(**row)


@router.put("/weights/{weight_id}", response_model=WeightResponse, status_code=status.HTTP_200_OK)
def update_weight(
    weight_id: int,
    payload: WeightUpdate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> WeightResponse:
    row = user_service.update_weight_entry(current_user["id"], weight_id, payload)
    return WeightResponse(**row)


@router.delete("/weights/{weight_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def delete_weight(
    weight_id: int,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> MessageResponse:
    user_service.delete_weight_entry(current_user["id"], weight_id)
    return MessageResponse(message="Weight entry deleted.")
