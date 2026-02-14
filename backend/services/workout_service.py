from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException, status

from database import DatabaseManager
from schemas import WorkoutCreate, WorkoutUpdate


class WorkoutService:
    """Workout CRUD and workout analytics."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def list_workouts(
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
            SELECT id, user_id, workout_name, duration_minutes, calories_burned, date
            FROM workouts
            WHERE {' AND '.join(conditions)}
            ORDER BY date DESC, id DESC
        """
        return self.db.execute(query, params, fetchall=True) or []

    def add_workout(self, user_id: int, workout: WorkoutCreate) -> dict:
        self.db.execute(
            """
            INSERT INTO workouts (user_id, workout_name, duration_minutes, calories_burned, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                workout.workout_name,
                workout.duration_minutes,
                workout.calories_burned,
                workout.date.isoformat(),
            ),
            commit=True,
        )

        return self.db.execute(
            """
            SELECT id, user_id, workout_name, duration_minutes, calories_burned, date
            FROM workouts
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
            fetchone=True,
        )

    def update_workout(self, user_id: int, workout_id: int, workout: WorkoutUpdate) -> dict:
        existing = self.db.execute(
            """
            SELECT id, user_id, workout_name, duration_minutes, calories_burned, date
            FROM workouts
            WHERE id = ? AND user_id = ?
            """,
            (workout_id, user_id),
            fetchone=True,
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found.",
            )

        update_fields = workout.model_dump(exclude_none=True)
        if not update_fields:
            return existing

        set_clauses = []
        values: list[object] = []
        for key, value in update_fields.items():
            set_clauses.append(f"{key} = ?")
            values.append(value.isoformat() if hasattr(value, "isoformat") else value)

        values.extend([workout_id, user_id])
        query = f"UPDATE workouts SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?"

        self.db.execute(query, values, commit=True)

        return self.db.execute(
            """
            SELECT id, user_id, workout_name, duration_minutes, calories_burned, date
            FROM workouts
            WHERE id = ? AND user_id = ?
            """,
            (workout_id, user_id),
            fetchone=True,
        )

    def delete_workout(self, user_id: int, workout_id: int) -> None:
        existing = self.db.execute(
            "SELECT id FROM workouts WHERE id = ? AND user_id = ?",
            (workout_id, user_id),
            fetchone=True,
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found.",
            )

        self.db.execute(
            "DELETE FROM workouts WHERE id = ? AND user_id = ?",
            (workout_id, user_id),
            commit=True,
        )

    def get_weekly_calories_burned(self, user_id: int) -> int:
        week_start = (date.today() - timedelta(days=7)).isoformat()
        result = self.db.execute(
            """
            SELECT COALESCE(SUM(calories_burned), 0) AS weekly_calories
            FROM workouts
            WHERE user_id = ? AND date >= ?
            """,
            (user_id, week_start),
            fetchone=True,
        )
        return int(result["weekly_calories"])

    def get_workout_frequency_by_week(self, user_id: int) -> list[dict]:
        return self.db.execute(
            """
            SELECT strftime('%Y-W%W', date) AS week, COUNT(*) AS workout_count
            FROM workouts
            WHERE user_id = ?
            GROUP BY strftime('%Y-W%W', date)
            ORDER BY week ASC
            """,
            (user_id,),
            fetchall=True,
        ) or []
