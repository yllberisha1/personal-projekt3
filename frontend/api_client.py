from __future__ import annotations

from typing import Any, Optional

import requests


class APIClient:
    """Small requests-based client for the FastAPI backend."""

    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def set_token(self, token: str) -> None:
        self.token = token

    def clear_token(self) -> None:
        self.token = None

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> tuple[bool, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            return False, {"detail": f"Could not connect to API: {exc}"}

        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {"detail": response.text or "Unknown response"}

        if response.ok:
            return True, data

        detail = data.get("detail") if isinstance(data, dict) else str(data)
        return False, {"detail": detail or "Request failed", "status_code": response.status_code}

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> tuple[bool, Any]:
        return self._request("GET", path, params=params)

    def post(self, path: str, payload: Optional[dict[str, Any]] = None) -> tuple[bool, Any]:
        return self._request("POST", path, payload=payload)

    def put(self, path: str, payload: Optional[dict[str, Any]] = None) -> tuple[bool, Any]:
        return self._request("PUT", path, payload=payload)

    def delete(self, path: str) -> tuple[bool, Any]:
        return self._request("DELETE", path)
