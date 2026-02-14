from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable, Optional


class DatabaseManager:
    """Simple sqlite3 database manager with thread-safe execution."""

    def __init__(self, db_path: str = "fitness.db") -> None:
        self.db_path = str(Path(db_path))
        self._lock = threading.Lock()

    def _get_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def execute(
        self,
        query: str,
        params: Iterable[Any] = (),
        *,
        fetchone: bool = False,
        fetchall: bool = False,
        commit: bool = False,
    ) -> Optional[Any]:
        with self._lock:
            with self._get_connection() as connection:
                cursor = connection.execute(query, tuple(params))
                if commit:
                    connection.commit()
                if fetchone:
                    row = cursor.fetchone()
                    return dict(row) if row else None
                if fetchall:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                return None

    def init_db(self) -> None:
        schema_statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                workout_name TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                calories_burned INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS nutrition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                meal_name TEXT NOT NULL,
                calories INTEGER NOT NULL,
                protein REAL NOT NULL,
                carbs REAL NOT NULL,
                fats REAL NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS weights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                weight_kg REAL NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_tokens_token ON tokens(token);",
            "CREATE INDEX IF NOT EXISTS idx_workouts_user_date ON workouts(user_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_nutrition_user_date ON nutrition(user_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_weights_user_date ON weights(user_id, date);",
        ]

        with self._lock:
            with self._get_connection() as connection:
                for statement in schema_statements:
                    connection.execute(statement)
                self._run_migrations(connection)
                connection.commit()

    def _run_migrations(self, connection: sqlite3.Connection) -> None:
        """Apply lightweight schema migrations for existing databases."""
        migrations = {
            "users": {
                "username": "TEXT NOT NULL DEFAULT ''",
                "email": "TEXT NOT NULL DEFAULT ''",
                "password_hash": "TEXT NOT NULL DEFAULT ''",
                "role": "TEXT NOT NULL DEFAULT 'user'",
                "created_at": "TEXT NOT NULL DEFAULT ''",
            },
            "tokens": {
                "user_id": "INTEGER NOT NULL DEFAULT 0",
                "token": "TEXT NOT NULL DEFAULT ''",
                "created_at": "TEXT NOT NULL DEFAULT ''",
            },
            "workouts": {
                "user_id": "INTEGER NOT NULL DEFAULT 0",
                "workout_name": "TEXT NOT NULL DEFAULT ''",
                "duration_minutes": "INTEGER NOT NULL DEFAULT 0",
                "calories_burned": "INTEGER NOT NULL DEFAULT 0",
                "date": "TEXT NOT NULL DEFAULT ''",
            },
            "nutrition": {
                "user_id": "INTEGER NOT NULL DEFAULT 0",
                "meal_name": "TEXT NOT NULL DEFAULT ''",
                "calories": "INTEGER NOT NULL DEFAULT 0",
                "protein": "REAL NOT NULL DEFAULT 0",
                "carbs": "REAL NOT NULL DEFAULT 0",
                "fats": "REAL NOT NULL DEFAULT 0",
                "date": "TEXT NOT NULL DEFAULT ''",
            },
            "weights": {
                "user_id": "INTEGER NOT NULL DEFAULT 0",
                "weight_kg": "REAL NOT NULL DEFAULT 0",
                "date": "TEXT NOT NULL DEFAULT ''",
                "created_at": "TEXT NOT NULL DEFAULT ''",
            },
        }

        for table_name, columns in migrations.items():
            for column_name, column_sql in columns.items():
                self._ensure_column(
                    connection,
                    table_name=table_name,
                    column_name=column_name,
                    column_sql=column_sql,
                )

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_sql: str,
    ) -> None:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        existing_columns = {row[1] for row in rows}
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
            )


_db_manager: Optional[DatabaseManager] = None


def get_database_manager(db_path: str = "fitness.db") -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
        _db_manager.init_db()
    return _db_manager
