from __future__ import annotations

import json
from typing import Any

from lifeos_cli.schema import EXIT_CODES, SCHEMA_VERSION


def error_payload(
    *,
    command: str,
    code: str,
    message: str,
    retryable: bool = False,
    field_errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "schemaVersion": SCHEMA_VERSION,
        "command": command,
        "code": code,
        "message": message,
        "retryable": retryable,
        "fieldErrors": field_errors or [],
    }


def exit_code(payload: dict[str, Any]) -> int:
    if payload.get("ok") is True:
        return EXIT_CODES["success"]
    return EXIT_CODES.get(str(payload.get("code") or "unexpected_error"), EXIT_CODES["unexpected_error"])


def write_json(payload: dict[str, Any], stream) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    stream.write("\n")
