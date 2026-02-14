from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status

from database import DatabaseManager
from schemas import NutritionCreate, NutritionUpdate


class NutritionService:
    """Meal CRUD and macro calculations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def list_meals(
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
            SELECT id, user_id, meal_name, calories, protein, carbs, fats, date
            FROM nutrition
            WHERE {' AND '.join(conditions)}
            ORDER BY date DESC, id DESC
        """
        return self.db.execute(query, params, fetchall=True) or []

    def add_meal(self, user_id: int, meal: NutritionCreate) -> dict:
        self.db.execute(
            """
            INSERT INTO nutrition (user_id, meal_name, calories, protein, carbs, fats, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                meal.meal_name,
                meal.calories,
                meal.protein,
                meal.carbs,
                meal.fats,
                meal.date.isoformat(),
            ),
            commit=True,
        )

        return self.db.execute(
            """
            SELECT id, user_id, meal_name, calories, protein, carbs, fats, date
            FROM nutrition
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
            fetchone=True,
        )

    def update_meal(self, user_id: int, meal_id: int, meal: NutritionUpdate) -> dict:
        existing = self.db.execute(
            """
            SELECT id, user_id, meal_name, calories, protein, carbs, fats, date
            FROM nutrition
            WHERE id = ? AND user_id = ?
            """,
            (meal_id, user_id),
            fetchone=True,
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal not found.",
            )

        update_fields = meal.model_dump(exclude_none=True)
        if not update_fields:
            return existing

        set_clauses = []
        values: list[object] = []
        for key, value in update_fields.items():
            set_clauses.append(f"{key} = ?")
            values.append(value.isoformat() if hasattr(value, "isoformat") else value)

        values.extend([meal_id, user_id])
        query = f"UPDATE nutrition SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?"
        self.db.execute(query, values, commit=True)

        return self.db.execute(
            """
            SELECT id, user_id, meal_name, calories, protein, carbs, fats, date
            FROM nutrition
            WHERE id = ? AND user_id = ?
            """,
            (meal_id, user_id),
            fetchone=True,
        )

    def delete_meal(self, user_id: int, meal_id: int) -> None:
        existing = self.db.execute(
            "SELECT id FROM nutrition WHERE id = ? AND user_id = ?",
            (meal_id, user_id),
            fetchone=True,
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal not found.",
            )

        self.db.execute(
            "DELETE FROM nutrition WHERE id = ? AND user_id = ?",
            (meal_id, user_id),
            commit=True,
        )

    def get_daily_macros(self, user_id: int, target_date: str) -> dict:
        macros = self.db.execute(
            """
            SELECT
                COALESCE(SUM(protein), 0) AS total_protein,
                COALESCE(SUM(carbs), 0) AS total_carbs,
                COALESCE(SUM(fats), 0) AS total_fats,
                COALESCE(SUM(calories), 0) AS total_calories
            FROM nutrition
            WHERE user_id = ? AND date = ?
            """,
            (user_id, target_date),
            fetchone=True,
        )
        return {
            "date": target_date,
            "total_protein": float(macros["total_protein"]),
            "total_carbs": float(macros["total_carbs"]),
            "total_fats": float(macros["total_fats"]),
            "total_calories": int(macros["total_calories"]),
        }
