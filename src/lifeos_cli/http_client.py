from __future__ import annotations

import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from lifeos_cli.errors import CliConfigError
from lifeos_cli.schema import SCHEMA_VERSION


_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
_SENSITIVE_KEYS = {
    "authorization",
    "password",
    "token",
    "user_token",
    "usertoken",
    "x_lifeos_user_token",
    "x-lifeos-user-token",
}


class LifeOSCliHttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        user_token: str | None = None,
        allow_remote_http: bool = False,
        insecure_tls: bool = False,
    ) -> None:
        parsed = urlparse(base_url)
        host = parsed.hostname or ""
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            raise CliConfigError("base-url must start with http:// or https://")
        if scheme == "http" and host not in _LOOPBACK_HOSTS and not allow_remote_http:
            raise CliConfigError(
                "remote plain HTTP base-url requires --allow-remote-http; use HTTPS for cloud APIs"
            )
        self._base_url = base_url.rstrip("/")
        self._user_token = user_token
        self._ssl_context = (
            ssl._create_unverified_context() if scheme == "https" and insecure_tls else None
        )

    def set_user_token(self, user_token: str) -> None:
        self._user_token = user_token

    def schema(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/cli/schema")

    def diagnose(self, user_id: str | None = None) -> dict[str, Any]:
        query = urlencode({"user_id": user_id} if user_id else {})
        suffix = f"?{query}" if query else ""
        return self._request("GET", f"/api/v1/cli/diagnose{suffix}")

    def register_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/users/register", payload)

    def login_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/users/login", payload)

    def add_fact(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/cli/facts", payload)

    def record(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/cli/records", payload)

    def add_asset(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/cli/assets", payload)

    def backfill_assets(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/cli/assets/backfill", payload)

    def list_assets(self, user_id: str, limit: int | None = None) -> dict[str, Any]:
        query = urlencode({"user_id": user_id, "limit": limit} if limit is not None else {"user_id": user_id})
        return self._request("GET", f"/api/v1/cli/assets?{query}")

    def save_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/cli/plans/draft", payload)

    def get_plan_draft(self, user_id: str, date: str | None = None) -> dict[str, Any]:
        query = urlencode({key: value for key, value in {"user_id": user_id, "date": date}.items() if value})
        return self._request("GET", f"/api/v1/cli/plans/draft?{query}")

    def update_plan_draft_action(self, action_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/api/v1/cli/plans/draft/actions/{quote(action_id, safe='')}", payload)

    def confirm_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/cli/plans/confirm", payload)

    def get_plan(self, user_id: str, date: str | None = None) -> dict[str, Any]:
        query = urlencode({key: value for key, value in {"user_id": user_id, "date": date}.items() if value})
        return self._request("GET", f"/api/v1/cli/plans?{query}")

    def plan_history(self, user_id: str, limit: int | None = None) -> dict[str, Any]:
        query = urlencode({key: value for key, value in {"user_id": user_id, "limit": limit}.items() if value is not None})
        return self._request("GET", f"/api/v1/cli/plans/history?{query}")

    def list_actions(self, user_id: str, date: str | None = None) -> dict[str, Any]:
        query = urlencode({key: value for key, value in {"user_id": user_id, "date": date}.items() if value})
        return self._request("GET", f"/api/v1/cli/actions?{query}")

    def update_action(self, action_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/api/v1/cli/actions/{quote(action_id, safe='')}", payload)

    def complete_action(self, action_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/cli/actions/{quote(action_id, safe='')}/done", payload)

    def get_scores(self, user_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/cli/scores?{urlencode({'user_id': user_id})}")

    def get_profile(self, user_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/cli/profile?{urlencode({'user_id': user_id})}")

    def init_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/cli/profile/init", payload)

    def snapshot(self, user_id: str, params: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(params)
        dimensions = normalized.get("dimensions")
        if isinstance(dimensions, list):
            normalized["dimensions"] = ",".join(str(item) for item in dimensions)
        query = urlencode({key: value for key, value in normalized.items() if value is not None})
        suffix = f"?{query}" if query else ""
        return self._request("GET", f"/api/v1/cli/users/{quote(user_id, safe='')}/snapshot{suffix}")

    def _request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data = None
        headers = {}
        if self._user_token:
            headers["X-LifeOS-User-Token"] = self._user_token
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self._base_url}{path}",
            data=data,
            method=method,
            headers=headers,
        )
        try:
            with urlopen(request, timeout=20, context=self._ssl_context) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(body)
            except json.JSONDecodeError:
                detail = {"detail": body}
            safe_detail = _sanitize_error_detail(detail)
            message = safe_detail.get("detail") if isinstance(safe_detail, dict) else safe_detail
            return {
                "ok": False,
                "schemaVersion": SCHEMA_VERSION,
                "code": "auth_or_not_found" if exc.code in (401, 404) else "storage_or_http_error",
                "message": str(message or safe_detail),
                "retryable": exc.code >= 500,
            }
        except URLError as exc:
            return {
                "ok": False,
                "schemaVersion": SCHEMA_VERSION,
                "code": "storage_or_http_error",
                "message": str(exc.reason),
                "retryable": True,
            }


def _sanitize_error_detail(value: Any, *, sensitive_context: bool = False) -> Any:
    if isinstance(value, dict):
        loc = value.get("loc")
        is_sensitive = sensitive_context or (
            isinstance(loc, list)
            and any(_is_sensitive_key(str(item)) for item in loc)
        )
        safe: dict[str, Any] = {}
        for key, item in value.items():
            if _is_sensitive_key(str(key)) or (is_sensitive and key == "input"):
                safe[key] = "[redacted]"
            else:
                safe[key] = _sanitize_error_detail(item, sensitive_context=is_sensitive)
        return safe
    if isinstance(value, list):
        return [
            _sanitize_error_detail(item, sensitive_context=sensitive_context)
            for item in value
        ]
    return value


def _is_sensitive_key(value: str) -> bool:
    normalized = value.replace("-", "_").lower()
    return normalized in _SENSITIVE_KEYS
