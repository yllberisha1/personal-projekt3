from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from database import DatabaseManager
from schemas import WeightCreate, WeightUpdate


class UserService:
    """User profile and dashboard related operations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_user_by_id(self, user_id: int) -> dict:
        user = self.db.execute(
            "SELECT id, username, email, role, created_at FROM users WHERE id = ?",
            (user_id,),
            fetchone=True,
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    def get_dashboard_stats(self, user_id: int) -> dict:
        user = self.get_user_by_id(user_id)

        workout_stats = self.db.execute(
            """
            SELECT COUNT(*) AS total_workouts,
                   COALESCE(SUM(calories_burned), 0) AS total_calories_burned
            FROM workouts
            WHERE user_id = ?
            """,
            (user_id,),
            fetchone=True,
        )

        meal_stats = self.db.execute(
            """
            SELECT COALESCE(SUM(calories), 0) AS total_calories_consumed
            FROM nutrition
            WHERE user_id = ?
            """,
            (user_id,),
            fetchone=True,
        )

        return {
            "username": user["username"],
            "total_workouts": int(workout_stats["total_workouts"]),
            "total_calories_burned": int(workout_stats["total_calories_burned"]),
            "total_calories_consumed": int(meal_stats["total_calories_consumed"]),
        }

    def add_weight_entry(self, user_id: int, payload: WeightCreate) -> dict:
        now = datetime.utcnow().isoformat(timespec="seconds")
        self.db.execute(
            """
            INSERT INTO weights (user_id, weight_kg, date, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, payload.weight_kg, payload.date.isoformat(), now),
            commit=True,
        )

        return self.db.execute(
            """
            SELECT id, user_id, weight_kg, date, created_at
            FROM weights
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
            fetchone=True,
        )

    def list_weight_entries(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict]:
        conditions = ["user_id = ?"]
        params: list[object] = [user_id]

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)

        query = f"""
            SELECT id, user_id, weight_kg, date, created_at
            FROM weights
            WHERE {' AND '.join(conditions)}
            ORDER BY date ASC, id ASC
        """
        return self.db.execute(query, params, fetchall=True) or []

    def update_weight_entry(self, user_id: int, weight_id: int, payload: WeightUpdate) -> dict:
        existing = self.db.execute(
            "SELECT id, user_id, weight_kg, date, created_at FROM weights WHERE id = ? AND user_id = ?",
            (weight_id, user_id),
            fetchone=True,
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weight entry not found.",
            )

        update_fields = payload.model_dump(exclude_none=True)
        if not update_fields:
            return existing

        set_clauses = []
        values: list[object] = []
        for key, value in update_fields.items():
            set_clauses.append(f"{key} = ?")
            values.append(value.isoformat() if hasattr(value, "isoformat") else value)

        values.extend([weight_id, user_id])
        query = f"UPDATE weights SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?"

        self.db.execute(query, values, commit=True)

        return self.db.execute(
            "SELECT id, user_id, weight_kg, date, created_at FROM weights WHERE id = ? AND user_id = ?",
            (weight_id, user_id),
            fetchone=True,
        )

    def delete_weight_entry(self, user_id: int, weight_id: int) -> None:
        existing = self.db.execute(
            "SELECT id FROM weights WHERE id = ? AND user_id = ?",
            (weight_id, user_id),
            fetchone=True,
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weight entry not found.",
            )

        self.db.execute(
            "DELETE FROM weights WHERE id = ? AND user_id = ?",
            (weight_id, user_id),
            commit=True,
        )
