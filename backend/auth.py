from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from database import DatabaseManager, get_database_manager
from schemas import UserCreate, UserLogin


class TokenManager:
    """Handles token generation and expiration checks."""

    def __init__(self, ttl_hours: int = 24) -> None:
        self.ttl = timedelta(hours=ttl_hours)

    def generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def is_token_expired(self, created_at: str) -> bool:
        token_time = datetime.fromisoformat(created_at)
        return datetime.utcnow() - token_time > self.ttl


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AuthService:
    """Authentication use-cases and token lifecycle."""

    def __init__(self, db_manager: DatabaseManager, token_manager: TokenManager) -> None:
        self.db = db_manager
        self.token_manager = token_manager

    def create_user(self, user_data: UserCreate) -> dict:
        existing_user = self.db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (user_data.username, user_data.email),
            fetchone=True,
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists.",
            )

        now = datetime.utcnow().isoformat(timespec="seconds")
        self.db.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_data.username,
                user_data.email,
                hash_password(user_data.password),
                now,
            ),
            commit=True,
        )
        return {"username": user_data.username}

    def authenticate_user(self, credentials: UserLogin) -> dict:
        user = self.db.execute(
            """
            SELECT id, username, email, password_hash, role, created_at
            FROM users
            WHERE username = ? OR email = ?
            """,
            (credentials.username_or_email, credentials.username_or_email),
            fetchone=True,
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        if user["password_hash"] != hash_password(credentials.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        token = self.generate_token(user["id"])
        return {
            "token": token,
            "token_type": "bearer",
            "username": user["username"],
            "user_id": user["id"],
        }

    def generate_token(self, user_id: int) -> str:
        # Keep one active token per user for predictable session behavior.
        self.db.execute("DELETE FROM tokens WHERE user_id = ?", (user_id,), commit=True)

        token = self.token_manager.generate_token()
        created_at = datetime.utcnow().isoformat(timespec="seconds")

        self.db.execute(
            "INSERT INTO tokens (user_id, token, created_at) VALUES (?, ?, ?)",
            (user_id, token, created_at),
            commit=True,
        )
        return token

    def validate_token(self, token: str) -> dict:
        token_row = self.db.execute(
            """
            SELECT users.id, users.username, users.email, users.role, users.created_at,
                   tokens.token, tokens.created_at AS token_created_at
            FROM tokens
            INNER JOIN users ON users.id = tokens.user_id
            WHERE tokens.token = ?
            """,
            (token,),
            fetchone=True,
        )
        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
            )

        if self.token_manager.is_token_expired(token_row["token_created_at"]):
            self.db.execute("DELETE FROM tokens WHERE token = ?", (token,), commit=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired. Please log in again.",
            )

        return {
            "id": token_row["id"],
            "username": token_row["username"],
            "email": token_row["email"],
            "role": token_row["role"],
            "created_at": token_row["created_at"],
        }

    def logout(self, token: str) -> None:
        self.db.execute("DELETE FROM tokens WHERE token = ?", (token,), commit=True)


def parse_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing.",
        )

    parts = authorization.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization must be in format: Bearer <token>.",
        )
    return parts[1]


_token_manager = TokenManager(ttl_hours=24)
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(get_database_manager(), _token_manager)
    return _auth_service


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    token = parse_bearer_token(authorization)
    return auth_service.validate_token(token)


def get_current_token(authorization: Optional[str] = Header(default=None)) -> str:
    return parse_bearer_token(authorization)
