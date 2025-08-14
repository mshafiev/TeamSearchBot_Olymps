from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests

from http_client import HttpClient


@dataclass
class CreateOlympiadResult:
    ok: bool
    status_code: int
    message: str
    response_json: Optional[Dict[str, Any]]


class DatabaseApiClient:
    def __init__(self, http: HttpClient):
        self.http = http

    def create_olympiad(self, olymp_data: Dict[str, Any]) -> CreateOlympiadResult:
        try:
            response = self.http.post("/olymp/create/", olymp_data)
        except requests.RequestException as exc:
            return CreateOlympiadResult(False, 0, f"network_error: {exc}", None)

        try:
            payload = response.json() if response.headers.get("Content-Type", "").startswith("application/json") else None
        except ValueError:
            payload = None

        if 200 <= response.status_code < 300:
            return CreateOlympiadResult(True, response.status_code, "created", payload)

        if response.status_code == 409:
            return CreateOlympiadResult(False, response.status_code, "conflict", payload)

        if response.status_code == 400:
            return CreateOlympiadResult(False, response.status_code, "bad_request", payload)

        if response.status_code == 401:
            return CreateOlympiadResult(False, response.status_code, "unauthorized", payload)

        if response.status_code == 429:
            return CreateOlympiadResult(False, response.status_code, "rate_limited", payload)

        if 500 <= response.status_code <= 599:
            return CreateOlympiadResult(False, response.status_code, "server_error", payload)

        return CreateOlympiadResult(False, response.status_code, "unknown_error", payload)