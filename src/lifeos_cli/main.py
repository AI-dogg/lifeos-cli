from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from lifeos_cli.errors import CliConfigError, CliValidationError
from lifeos_cli.http_client import LifeOSCliHttpClient
from lifeos_cli.output import error_payload, exit_code, write_json
from lifeos_cli.schema import CLI_SOURCE, EXIT_CODES, SCHEMA_VERSION, cli_schema


DEFAULT_BASE_URL = "https://106.55.134.110/lifeos"
DEFAULT_INSECURE_TLS = True
_AUTHENTICATED_COMMANDS = {
    "snapshot",
    "fact.add",
    "asset.add",
    "asset.list",
    "profile.capture",
    "profile.get",
    "assets.backfill",
    "plan.save",
    "plan.get",
    "plan.draft.get",
    "plan.draft.update",
    "plan.confirm",
    "plan.history",
    "action.list",
    "action.update",
    "action.done",
    "score.get",
}
HELP_TEXT = """LifeOS 成长护照

把计划、行动、目标、复盘、成果和重要经历记录到你的个人成长护照里。
你可以自己用命令记录，也可以让 AI 助手帮你记录。

第一次使用：
  lifeos register --name "你的名字" --password "你的密码"
  lifeos diagnose

常用记录：
  lifeos snapshot
      查看当前成长护照快照

  lifeos plan save --date 2026-06-18 --action "09:00|写今日计划" --action "11:00|复盘成长记录"
      保存某一天的计划

  lifeos plan confirm --date 2026-06-18
      确认计划，进入行动清单

  lifeos action list --date 2026-06-18
      查看当天行动

  lifeos action done --action-id ACTION_ID --text "已完成并验证结果"
      记录某个行动已经完成

  lifeos fact add --dimension long_term_goal --statement "未来三年持续建设个人成长系统"
      记录长期目标、里程碑、重要事实

  lifeos profile capture --dimension life_stage --statement "我正在从执行者转向产品负责人"
      记录人生阶段、关键决定、长期目标、认知变化

  lifeos asset add --kind method_asset --title "每日复盘流程" --summary "用于沉淀计划、行动和成长证据"
      记录可复用的成果、方法、资源或经验

怎么选择：
  未来要做的事       用 plan
  已经确认的行动     用 action
  长期事实和里程碑   用 fact
  人生阶段和目标     用 profile
  可复用成果和方法   用 asset
  查看已有信息       用 snapshot

账号：
  换设备或登录信息丢失时，用：
    lifeos login --name "你的名字" --password "你的密码"

提醒：
  只是讨论、草稿、假设计划时不要记录。
  明确要记录、保存、沉淀时再写入成长护照。
  action done 表示真的完成了一个行动，不要随便使用。
  看到 ok: true 就表示记录成功。
"""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliValidationError(message)


def main(argv: list[str] | None = None, stdout=None, stderr=None) -> int:
    _ = stderr
    stdout = stdout or sys.stdout
    try:
        parser = build_parser()
        namespace = parser.parse_args(argv)
        payload = dispatch(namespace)
    except CliValidationError as exc:
        payload = error_payload(
            command=exc.command,
            code="validation_error",
            message=exc.message,
            field_errors=[{"field": "arguments", "reason": "parse_error"}],
        )
    except CliConfigError as exc:
        payload = error_payload(command="config", code="config_error", message=str(exc))
    except Exception as exc:  # noqa: BLE001 - CLI must never emit a traceback to callers
        payload = error_payload(
            command="unexpected",
            code="unexpected_error",
            message=str(exc),
            retryable=False,
        )
    if isinstance(payload, str):
        stdout.write(payload.rstrip())
        stdout.write("\n")
        return EXIT_CODES["success"]
    write_json(payload, stdout)
    return exit_code(payload)


def build_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(prog="lifeos", add_help=True, argument_default=argparse.SUPPRESS)
    _add_common(parser)
    sub = parser.add_subparsers(dest="root_command", required=True)

    help_command = sub.add_parser("help", argument_default=argparse.SUPPRESS)
    help_command.set_defaults(command="help")

    configure = sub.add_parser("configure", argument_default=argparse.SUPPRESS)
    _add_common(configure)
    configure.add_argument("--user", dest="user")
    configure.set_defaults(command="configure")

    register = sub.add_parser("register", argument_default=argparse.SUPPRESS)
    _add_common(register)
    register.add_argument("--user", dest="user")
    register.set_defaults(command="register")

    login = sub.add_parser("login", argument_default=argparse.SUPPRESS)
    _add_common(login)
    login.set_defaults(command="login")

    schema = sub.add_parser("schema", argument_default=argparse.SUPPRESS)
    _add_common(schema)
    schema.set_defaults(command="schema")

    diagnose = sub.add_parser("diagnose", argument_default=argparse.SUPPRESS)
    _add_common(diagnose)
    diagnose.add_argument("--user", dest="user")
    diagnose.set_defaults(command="diagnose")

    snapshot = sub.add_parser("snapshot", argument_default=argparse.SUPPRESS)
    _add_common(snapshot)
    snapshot.add_argument("--user")
    snapshot.add_argument("--facts-limit", dest="facts_limit", type=int)
    snapshot.add_argument("--assets-limit", dest="assets_limit", type=int)
    snapshot.add_argument("--dimensions")
    snapshot.add_argument("--since")
    snapshot.add_argument("--include-profile", dest="include_profile")
    snapshot.add_argument("--include-facts", dest="include_facts")
    snapshot.add_argument("--include-assets", dest="include_assets")
    snapshot.add_argument("--max-statement-length", dest="max_statement_length", type=int)
    snapshot.add_argument("--cursor")
    snapshot.set_defaults(command="snapshot")

    plan = sub.add_parser("plan", argument_default=argparse.SUPPRESS)
    plan_sub = plan.add_subparsers(dest="plan_command", required=True)
    plan_save = plan_sub.add_parser("save", argument_default=argparse.SUPPRESS)
    _add_common(plan_save)
    plan_save.add_argument("--input-json", dest="input_json")
    plan_save.add_argument("--user")
    plan_save.add_argument("--date", dest="biz_date")
    plan_save.add_argument("--source-prompt", dest="source_prompt")
    plan_save.add_argument("--session-id", dest="session_id")
    plan_save.add_argument("--action", dest="actions", action="append")
    plan_save.set_defaults(command="plan.save")

    plan_get = plan_sub.add_parser("get", argument_default=argparse.SUPPRESS)
    _add_common(plan_get)
    plan_get.add_argument("--user")
    plan_get.add_argument("--date", dest="biz_date")
    plan_get.set_defaults(command="plan.get")

    plan_confirm = plan_sub.add_parser("confirm", argument_default=argparse.SUPPRESS)
    _add_common(plan_confirm)
    plan_confirm.add_argument("--input-json", dest="input_json")
    plan_confirm.add_argument("--user")
    plan_confirm.add_argument("--date", dest="biz_date")
    plan_confirm.set_defaults(command="plan.confirm")

    plan_history = plan_sub.add_parser("history", argument_default=argparse.SUPPRESS)
    _add_common(plan_history)
    plan_history.add_argument("--user")
    plan_history.add_argument("--limit", type=int)
    plan_history.set_defaults(command="plan.history")

    plan_draft = plan_sub.add_parser("draft", argument_default=argparse.SUPPRESS)
    plan_draft_sub = plan_draft.add_subparsers(dest="plan_draft_command", required=True)
    plan_draft_get = plan_draft_sub.add_parser("get", argument_default=argparse.SUPPRESS)
    _add_common(plan_draft_get)
    plan_draft_get.add_argument("--user")
    plan_draft_get.add_argument("--date", dest="biz_date")
    plan_draft_get.set_defaults(command="plan.draft.get")
    plan_draft_update = plan_draft_sub.add_parser("update", argument_default=argparse.SUPPRESS)
    _add_common(plan_draft_update)
    plan_draft_update.add_argument("--input-json", dest="input_json")
    plan_draft_update.add_argument("--user")
    plan_draft_update.add_argument("--action-id", dest="action_id")
    plan_draft_update.add_argument("--time")
    plan_draft_update.add_argument("--action")
    plan_draft_update.set_defaults(command="plan.draft.update")

    action = sub.add_parser("action", argument_default=argparse.SUPPRESS)
    action_sub = action.add_subparsers(dest="action_command", required=True)
    action_list = action_sub.add_parser("list", argument_default=argparse.SUPPRESS)
    _add_common(action_list)
    action_list.add_argument("--user")
    action_list.add_argument("--date", dest="biz_date")
    action_list.set_defaults(command="action.list")
    action_update = action_sub.add_parser("update", argument_default=argparse.SUPPRESS)
    _add_common(action_update)
    action_update.add_argument("--input-json", dest="input_json")
    action_update.add_argument("--user")
    action_update.add_argument("--action-id", dest="action_id")
    action_update.add_argument("--time")
    action_update.add_argument("--action")
    action_update.add_argument("--status", choices=["pending", "done", "skipped"])
    action_update.set_defaults(command="action.update")
    action_done = action_sub.add_parser("done", argument_default=argparse.SUPPRESS)
    _add_common(action_done)
    action_done.add_argument("--input-json", dest="input_json")
    action_done.add_argument("--user")
    action_done.add_argument("--action-id", dest="action_id")
    action_done.add_argument("--text")
    action_done.add_argument("--date", dest="biz_date")
    action_done.add_argument("--session-id", dest="session_id")
    action_done.set_defaults(command="action.done")

    score = sub.add_parser("score", argument_default=argparse.SUPPRESS)
    score_sub = score.add_subparsers(dest="score_command", required=True)
    score_get = score_sub.add_parser("get", argument_default=argparse.SUPPRESS)
    _add_common(score_get)
    score_get.add_argument("--user")
    score_get.set_defaults(command="score.get")

    fact = sub.add_parser("fact", argument_default=argparse.SUPPRESS)
    fact_sub = fact.add_subparsers(dest="fact_command", required=True)
    fact_add = fact_sub.add_parser("add", argument_default=argparse.SUPPRESS)
    _add_common(fact_add)
    _add_write_common(fact_add)
    fact_add.add_argument("--dimension")
    fact_add.add_argument("--statement")
    fact_add.add_argument("--evidence")
    fact_add.add_argument("--payload")
    fact_add.set_defaults(command="fact.add")

    asset = sub.add_parser("asset", argument_default=argparse.SUPPRESS)
    asset_sub = asset.add_subparsers(dest="asset_command", required=True)
    asset_add = asset_sub.add_parser("add", argument_default=argparse.SUPPRESS)
    _add_common(asset_add)
    asset_add.add_argument("--input-json", dest="input_json")
    asset_add.add_argument("--dry-run", dest="dry_run", action="store_true")
    asset_add.add_argument("--user")
    asset_add.add_argument("--kind")
    asset_add.add_argument("--title")
    asset_add.add_argument("--summary")
    asset_add.add_argument("--from-fact-id", dest="from_fact_id", type=int)
    asset_add.add_argument("--evidence")
    asset_add.add_argument("--payload")
    asset_add.add_argument("--occurred-at", dest="occurred_at")
    asset_add.add_argument("--idempotency-key", dest="idempotency_key")
    asset_add.set_defaults(command="asset.add")
    asset_list = asset_sub.add_parser("list", argument_default=argparse.SUPPRESS)
    _add_common(asset_list)
    asset_list.add_argument("--user")
    asset_list.add_argument("--limit", type=int)
    asset_list.set_defaults(command="asset.list")

    profile = sub.add_parser("profile", argument_default=argparse.SUPPRESS)
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_capture = profile_sub.add_parser("capture", argument_default=argparse.SUPPRESS)
    _add_common(profile_capture)
    _add_write_common(profile_capture)
    profile_capture.add_argument("--dimension")
    profile_capture.add_argument("--statement")
    profile_capture.add_argument("--evidence")
    profile_capture.add_argument("--payload")
    profile_capture.set_defaults(command="profile.capture")
    profile_get = profile_sub.add_parser("get", argument_default=argparse.SUPPRESS)
    _add_common(profile_get)
    profile_get.add_argument("--user")
    profile_get.set_defaults(command="profile.get")

    assets = sub.add_parser("assets", argument_default=argparse.SUPPRESS)
    assets_sub = assets.add_subparsers(dest="assets_command", required=True)
    backfill = assets_sub.add_parser("backfill", argument_default=argparse.SUPPRESS)
    _add_common(backfill)
    backfill.add_argument("--input-json", dest="input_json")
    backfill.add_argument("--dry-run", dest="dry_run", action="store_true")
    backfill.add_argument("--user")
    backfill.add_argument("--limit", type=int)
    backfill.set_defaults(command="assets.backfill")
    return parser


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=["api", "http"])
    parser.add_argument("--base-url", dest="base_url")
    parser.add_argument("--allow-remote-http", dest="allow_remote_http", action="store_true")
    parser.add_argument("--insecure", dest="insecure_tls", action="store_true", default=argparse.SUPPRESS)
    parser.add_argument("--token", "--user-token", dest="user_token")
    parser.add_argument("--name")
    parser.add_argument("--password")
    parser.add_argument("--actor")
    parser.add_argument("--actor-version", dest="actor_version")
    parser.add_argument("--output", choices=["json"])


def _add_write_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input-json", dest="input_json")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("--user")
    parser.add_argument("--occurred-at", dest="occurred_at")
    parser.add_argument("--idempotency-key", dest="idempotency_key")
    parser.add_argument("--user-confirmed-brief", dest="user_confirmed_brief", action="store_true")
    parser.add_argument("--confirmation-text", dest="confirmation_text")


def dispatch(namespace: argparse.Namespace) -> dict[str, Any] | str:
    command = namespace.command
    if command == "help":
        return HELP_TEXT
    if command == "configure":
        effective, sources = _effective_input(
            namespace,
            include_env_defaults=False,
            include_transport_config=True,
        )
        validation = _prevalidate_effective_input(command, effective, sources)
        if validation is not None:
            return validation
        return _configure(effective, sources)
    actor = {
        "name": _value(namespace, "actor", default="cli"),
        "version": _value(namespace, "actor_version", default=None),
    }
    mode = _value(namespace, "mode", default=None)
    if command == "schema" and mode is None:
        return cli_schema()

    effective, sources = _effective_input(namespace)
    validation = _prevalidate_effective_input(command, effective, sources)
    if validation is not None:
        return validation
    client = _api_client(namespace)
    if command == "register":
        return _register_user_response(client, effective, sources)
    if command == "login":
        return _login_user_response(client, effective, sources)
    identity_error = _ensure_user_identity(client, command, effective, sources)
    if identity_error is not None:
        return identity_error
    return _dispatch_http(command, client, effective, sources, actor)


def _dispatch_http(
    command: str,
    client: LifeOSCliHttpClient,
    effective: dict[str, Any],
    sources: dict[str, str],
    actor: dict[str, Any],
) -> dict[str, Any]:
    if command == "schema":
        return client.schema()
    if command == "diagnose":
        return client.diagnose(effective.get("user"))
    if command == "snapshot":
        return client.snapshot(
            str(effective.get("user", "")),
            {
                "facts_limit": effective.get("facts_limit"),
                "assets_limit": effective.get("assets_limit"),
                "dimensions": effective.get("dimensions"),
                "since": effective.get("since"),
                "include_profile": effective.get("include_profile"),
                "include_facts": effective.get("include_facts"),
                "include_assets": effective.get("include_assets"),
                "max_statement_length": effective.get("max_statement_length"),
                "cursor": effective.get("cursor"),
            },
        )
    if command == "plan.save":
        return client.save_plan(
            {
                "user_id": effective.get("user", ""),
                "biz_date": effective.get("biz_date"),
                "source_prompt": effective.get("source_prompt"),
                "session_id": effective.get("session_id"),
                "actions": _plan_actions_payload(effective.get("actions")),
                "actor": actor,
                "effective_input": _public_effective_input(effective),
                "input_sources": _public_input_sources(sources),
            }
        )
    if command == "plan.get":
        return client.get_plan(str(effective.get("user", "")), effective.get("biz_date"))
    if command == "plan.draft.get":
        return client.get_plan_draft(str(effective.get("user", "")), effective.get("biz_date"))
    if command == "plan.draft.update":
        return client.update_plan_draft_action(
            str(effective.get("action_id", "")),
            {
                "user_id": effective.get("user", ""),
                "time": effective.get("time"),
                "action": effective.get("action"),
                "actor": actor,
                "effective_input": _public_effective_input(effective),
                "input_sources": _public_input_sources(sources),
            },
        )
    if command == "plan.confirm":
        return client.confirm_plan(
            {
                "user_id": effective.get("user", ""),
                "biz_date": effective.get("biz_date"),
                "actor": actor,
                "effective_input": _public_effective_input(effective),
                "input_sources": _public_input_sources(sources),
            }
        )
    if command == "plan.history":
        return client.plan_history(str(effective.get("user", "")), effective.get("limit"))
    if command == "action.list":
        return client.list_actions(str(effective.get("user", "")), effective.get("biz_date"))
    if command == "action.update":
        return client.update_action(
            str(effective.get("action_id", "")),
            {
                "user_id": effective.get("user", ""),
                "time": effective.get("time"),
                "action": effective.get("action"),
                "status": effective.get("status"),
                "actor": actor,
                "effective_input": _public_effective_input(effective),
                "input_sources": _public_input_sources(sources),
            },
        )
    if command == "action.done":
        return client.complete_action(
            str(effective.get("action_id", "")),
            {
                "user_id": effective.get("user", ""),
                "text": effective.get("text"),
                "biz_date": effective.get("biz_date"),
                "session_id": effective.get("session_id"),
                "actor": actor,
                "effective_input": _public_effective_input(effective),
                "input_sources": _public_input_sources(sources),
            },
        )
    if command == "score.get":
        return client.get_scores(str(effective.get("user", "")))
    if command in {"fact.add", "profile.capture"}:
        payload = {
            "user_id": effective.get("user", ""),
            "dimension": effective.get("dimension", ""),
            "statement": effective.get("statement", ""),
            "evidence": effective.get("evidence"),
            "payload": _json_object(effective.get("payload")),
            "occurred_at": effective.get("occurred_at"),
            "idempotency_key": effective.get("idempotency_key"),
            "user_confirmed_brief": bool(effective.get("user_confirmed_brief")),
            "confirmation_text": effective.get("confirmation_text"),
            "dry_run": bool(effective.get("dry_run")),
            "actor": actor,
            "effective_input": _public_effective_input(effective),
            "input_sources": _public_input_sources(sources),
            "command": command,
        }
        return client.add_fact(payload)
    if command == "asset.add":
        return client.add_asset(
            {
                "user_id": effective.get("user", ""),
                "kind": effective.get("kind", ""),
                "title": effective.get("title", ""),
                "summary": effective.get("summary"),
                "from_fact_id": effective.get("from_fact_id"),
                "evidence": effective.get("evidence"),
                "payload": _json_object(effective.get("payload")),
                "occurred_at": effective.get("occurred_at"),
                "idempotency_key": effective.get("idempotency_key"),
                "dry_run": bool(effective.get("dry_run")),
                "actor": actor,
                "effective_input": _public_effective_input(effective),
                "input_sources": _public_input_sources(sources),
            }
        )
    if command == "asset.list":
        return client.list_assets(str(effective.get("user", "")), effective.get("limit"))
    if command == "profile.get":
        return client.get_profile(str(effective.get("user", "")))
    if command == "assets.backfill":
        return client.backfill_assets(
            {
                "user_id": effective.get("user", ""),
                "limit": effective.get("limit", 500),
                "dry_run": bool(effective.get("dry_run")),
                "actor": actor,
                "effective_input": _public_effective_input(effective),
                "input_sources": _public_input_sources(sources),
            }
        )
    raise CliConfigError(f"HTTP mode does not support command: {command}")


def _register_user_response(
    client: LifeOSCliHttpClient,
    effective: dict[str, Any],
    sources: dict[str, str],
) -> dict[str, Any]:
    result = _register_user(client, effective=effective, sources=sources)
    if result.get("ok") is False:
        return result
    user_id = str(result.get("user_id") or "")
    user_token = str(result.get("user_token") or "")
    _persist_registered_user(
        user_id=user_id,
        user_token=user_token,
        name=str(effective.get("name") or ""),
    )
    return {
        "ok": True,
        "schemaVersion": SCHEMA_VERSION,
        "command": "register",
        "source": CLI_SOURCE,
        "userId": user_id,
        "tokenStored": bool(user_token),
        "user": _public_user(result),
        "effectiveInput": _public_effective_input(effective | {"user": user_id}),
        "inputSources": _public_input_sources(sources | {"user": "registration"}),
        "warnings": [],
    }


def _login_user_response(
    client: LifeOSCliHttpClient,
    effective: dict[str, Any],
    sources: dict[str, str],
) -> dict[str, Any]:
    result = _login_user(client, effective=effective, sources=sources)
    if result.get("ok") is False:
        return result
    user_id = str(result.get("user_id") or "")
    user_token = str(result.get("user_token") or "")
    _persist_registered_user(
        user_id=user_id,
        user_token=user_token,
        name=str(effective.get("name") or ""),
    )
    return {
        "ok": True,
        "schemaVersion": SCHEMA_VERSION,
        "command": "login",
        "source": CLI_SOURCE,
        "userId": user_id,
        "tokenStored": bool(user_token),
        "user": _public_user(result),
        "effectiveInput": _public_effective_input(effective | {"user": user_id}),
        "inputSources": _public_input_sources(sources | {"user": "login"}),
        "warnings": [],
    }


def _ensure_user_identity(
    client: LifeOSCliHttpClient,
    command: str,
    effective: dict[str, Any],
    sources: dict[str, str],
) -> dict[str, Any] | None:
    if command not in _AUTHENTICATED_COMMANDS:
        return None
    if str(effective.get("user") or "").strip() and str(effective.get("user_token") or "").strip():
        client.set_user_token(str(effective.get("user_token") or ""))
        return None
    if not str(effective.get("user_token") or "").strip() and str(effective.get("name") or "").strip() and str(
        effective.get("password") or ""
    ):
        result = _login_user(client, effective=effective, sources=sources)
        if result.get("ok") is False:
            return result
        user_id = str(result.get("user_id") or "").strip()
        user_token = str(result.get("user_token") or "").strip()
        if not user_id or not user_token:
            return error_payload(
                command="login",
                code="storage_or_http_error",
                message="login response did not include user_id and user_token",
                retryable=True,
            )
        _persist_registered_user(
            user_id=user_id,
            user_token=user_token,
            name=str(effective.get("name") or ""),
        )
        effective["user"] = user_id
        effective["user_token"] = user_token
        client.set_user_token(user_token)
        sources["user"] = "login"
        sources["user_token"] = "login"
        return None
    return error_payload(
        command=command,
        code="auth_or_not_found",
        message="missing user token; run: lifeos login --name \"Your Name\" --password \"Your Password\"",
        retryable=False,
        field_errors=[{"field": "user_token", "reason": "required"}],
    )


def _register_user(
    client: LifeOSCliHttpClient,
    *,
    effective: dict[str, Any],
    sources: dict[str, str],
) -> dict[str, Any]:
    name = str(effective.get("name") or "").strip()
    user_id = str(effective.get("user") or "").strip()
    payload = {
        "user_id": user_id or None,
        "name": name or None,
        "nickname": name or None,
        "password": str(effective.get("password") or ""),
        "source": "lifeos_cli",
    }
    result = client.register_user(payload)
    if result.get("ok") is False:
        return result
    return result


def _login_user(
    client: LifeOSCliHttpClient,
    *,
    effective: dict[str, Any],
    sources: dict[str, str],
) -> dict[str, Any]:
    name = str(effective.get("name") or "").strip()
    payload = {
        "name": name or None,
        "password": str(effective.get("password") or ""),
        "source": "lifeos_cli",
    }
    result = client.login_user(payload)
    if result.get("ok") is False:
        result.setdefault("command", "login")
        result.setdefault("effectiveInput", _public_effective_input(effective))
        result.setdefault("inputSources", _public_input_sources(sources))
    return result


def _api_client(namespace: argparse.Namespace) -> LifeOSCliHttpClient:
    base_url = str(
        _value(
            namespace,
            "base_url",
            default=_config_value("LIFEOS_CLI_BASE_URL", DEFAULT_BASE_URL),
        )
        or ""
    ).strip()
    if not base_url:
        raise CliConfigError(
            "missing base-url; run: lifeos configure --base-url https://your-lifeos-api.example.com --name \"Your Name\""
        )
    return LifeOSCliHttpClient(
        base_url=base_url,
        user_token=_value(namespace, "user_token", default=_config_value("LIFEOS_USER_TOKEN", "")) or None,
        allow_remote_http=bool(_value(namespace, "allow_remote_http", default=False)),
        insecure_tls=bool(
            _value(
                namespace,
                "insecure_tls",
                default=_config_bool(
                    ("LIFEOS_CLI_INSECURE_TLS", "LIFEOS_CLI_INSECURE"),
                    DEFAULT_INSECURE_TLS,
                ),
            )
        ),
    )


def _effective_input(
    namespace: argparse.Namespace,
    *,
    include_env_defaults: bool = True,
    include_transport_config: bool = False,
) -> tuple[dict[str, Any], dict[str, str]]:
    raw = vars(namespace)
    input_json = raw.get("input_json")
    source_data = _load_input_json(input_json) if input_json else {}
    effective = dict(source_data)
    sources = {key: "input_json" for key in source_data}
    ignored = {
        "root_command",
        "fact_command",
        "asset_command",
        "profile_command",
        "assets_command",
        "plan_command",
        "plan_draft_command",
        "action_command",
        "score_command",
        "command",
        "input_json",
        "mode",
        "allow_remote_http",
        "insecure_tls",
        "actor",
        "actor_version",
        "output",
    }
    if not include_transport_config:
        ignored.add("base_url")
    else:
        ignored.discard("insecure_tls")
    for key, value in raw.items():
        if key in ignored or value is None:
            continue
        effective[key] = value
        sources[key] = "cli_arg"
    if include_env_defaults:
        _apply_env_default(effective, sources, key="user", env_names=("LIFEOS_USER_ID",))
        _apply_env_default(effective, sources, key="user_token", env_names=("LIFEOS_USER_TOKEN",))
        _apply_env_default(
            effective,
            sources,
            key="name",
            env_names=("LIFEOS_USER_NAME", "LIFEOS_NAME"),
        )
        _apply_env_default(effective, sources, key="password", env_names=("LIFEOS_PASSWORD",))
    return effective, sources


def _configure(effective: dict[str, Any], sources: dict[str, str]) -> dict[str, Any]:
    path = _user_config_path()
    values = _read_dotenv(path)
    mappings = {
        "base_url": "LIFEOS_CLI_BASE_URL",
        "user": "LIFEOS_USER_ID",
        "user_token": "LIFEOS_USER_TOKEN",
        "name": "LIFEOS_USER_NAME",
    }
    updated: list[str] = []
    for input_key, env_key in mappings.items():
        value = str(effective.get(input_key) or "").strip()
        if not value:
            continue
        values[env_key] = value
        updated.append(env_key)
    if effective.get("insecure_tls") is True:
        values["LIFEOS_CLI_INSECURE_TLS"] = "true"
        updated.append("LIFEOS_CLI_INSECURE_TLS")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_dotenv(values), encoding="utf-8")
    return {
        "ok": True,
        "schemaVersion": SCHEMA_VERSION,
        "command": "configure",
        "source": CLI_SOURCE,
        "configPath": str(path),
        "updated": updated,
        "effectiveInput": _public_effective_input(effective),
        "inputSources": _public_input_sources(sources),
        "warnings": [],
    }


def _persist_registered_user(*, user_id: str, user_token: str = "", name: str = "") -> None:
    if not user_id:
        return
    path = _user_config_path()
    values = _read_dotenv(path)
    values["LIFEOS_USER_ID"] = user_id
    if user_token:
        values["LIFEOS_USER_TOKEN"] = user_token
    if name:
        values["LIFEOS_USER_NAME"] = name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_dotenv(values), encoding="utf-8")


def _apply_env_default(
    effective: dict[str, Any],
    sources: dict[str, str],
    *,
    key: str,
    env_names: tuple[str, ...],
) -> None:
    if str(effective.get(key) or "").strip():
        return
    for env_name in env_names:
        value = _config_value(env_name, "")
        if value:
            effective[key] = value
            sources[key] = "env"
            return


def _load_input_json(value: str) -> dict[str, Any]:
    text = sys.stdin.read() if value == "-" else value
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CliValidationError(f"invalid input-json: {exc}") from exc
    if not isinstance(data, dict):
        raise CliValidationError("input-json must be a JSON object")
    return {_normalize_key(key): item for key, item in data.items()}


def _config_value(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    for env_path in _candidate_env_files():
        parsed = _read_dotenv_value(env_path, name)
        if parsed:
            return parsed
    return default


def _config_bool(names: tuple[str, ...], default: bool = False) -> bool:
    truthy = {"1", "true", "yes", "on"}
    falsy = {"0", "false", "no", "off"}
    for name in names:
        value = _config_value(name, "")
        normalized = value.strip().lower()
        if normalized in truthy:
            return True
        if normalized in falsy:
            return False
    return default


def _candidate_env_files() -> list[Path]:
    cwd = Path.cwd()
    paths = []
    explicit = os.environ.get("LIFEOS_CLI_CONFIG")
    if explicit:
        paths.append(Path(explicit).expanduser())
    paths.append(_user_config_path())
    paths.extend([cwd / ".env", cwd.parent / ".env"])
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _user_config_path() -> Path:
    return Path(os.environ.get("LIFEOS_CLI_CONFIG", "~/.lifeos/cli.env")).expanduser()


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[key] = value
    except OSError:
        return values
    return values


def _format_dotenv(values: dict[str, str]) -> str:
    lines = [
        "# LifeOS CLI config",
        "# Generated by: lifeos configure",
    ]
    for key in sorted(values):
        lines.append(f"{key}={_quote_env_value(values[key])}")
    return "\n".join(lines) + "\n"


def _quote_env_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _read_dotenv_value(path: Path, name: str) -> str | None:
    if not path.exists():
        return None
    prefix = f"{name}="
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or not line.startswith(prefix):
                continue
            value = line[len(prefix) :].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            return value
    except OSError:
        return None
    return None


def _prevalidate_effective_input(
    command: str,
    effective: dict[str, Any],
    sources: dict[str, str],
) -> dict[str, Any] | None:
    required: list[str] = []
    if command in {"fact.add", "profile.capture"}:
        required = ["dimension", "statement"]
    elif command in {
        "asset.add",
        "asset.list",
        "assets.backfill",
        "snapshot",
        "plan.get",
        "plan.draft.get",
        "plan.confirm",
        "plan.history",
        "action.list",
        "score.get",
        "profile.get",
    }:
        required = []
    elif command == "plan.save":
        required = ["actions"]
    elif command in {"plan.draft.update", "action.update", "action.done"}:
        required = ["action_id"]
    if command == "asset.add":
        required.extend(["kind", "title"])
    if command in {"register", "login"} and not str(effective.get("name") or "").strip():
        required.append("name")
    if command in {"register", "login"} and not str(effective.get("password") or "").strip():
        required.append("password")
    if command == "configure" and not any(
        str(effective.get(field) or "").strip()
        for field in ("base_url", "user", "user_token", "name")
    ) and effective.get("insecure_tls") is not True:
        required.append("base_url|user|token|name")

    field_errors = [
        {"field": field, "reason": "required"}
        for field in required
        if not str(effective.get(field) or "").strip()
    ]
    if command in _AUTHENTICATED_COMMANDS:
        has_user_token = str(effective.get("user_token") or "").strip()
        has_password_login = str(effective.get("name") or "").strip() and str(
            effective.get("password") or ""
        ).strip()
        if not str(effective.get("user") or "").strip() and not has_password_login:
            field_errors.append({"field": "user", "reason": "required_without_name"})
            field_errors.append({"field": "name", "reason": "required_without_user"})
        if not has_user_token and not has_password_login:
            field_errors.append({"field": "user_token", "reason": "required_without_password_login"})
    if command == "asset.add" and not effective.get("from_fact_id") and not str(
        effective.get("summary") or ""
    ).strip():
        field_errors.append({"field": "summary", "reason": "required_without_from_fact_id"})
    if command == "plan.save":
        try:
            _plan_actions_payload(effective.get("actions"))
        except CliValidationError as exc:
            field_errors.append({"field": "actions", "reason": "invalid_plan_actions", "message": exc.message})
    if "payload" in effective:
        try:
            _json_object(effective.get("payload"))
        except CliValidationError as exc:
            field_errors.append({"field": "payload", "reason": "invalid_json", "message": exc.message})

    if not field_errors:
        return None
    payload = error_payload(
        command=command,
        code="validation_error",
        message="invalid command input",
        field_errors=field_errors,
    )
    payload["inputSources"] = _public_input_sources(sources)
    payload["effectiveInput"] = _public_effective_input(effective)
    return payload


def _normalize_key(value: str) -> str:
    aliases = {
        "userId": "user",
        "userToken": "user_token",
        "occurredAt": "occurred_at",
        "idempotencyKey": "idempotency_key",
        "userConfirmedBrief": "user_confirmed_brief",
        "confirmationText": "confirmation_text",
        "fromFactId": "from_fact_id",
        "factsLimit": "facts_limit",
        "assetsLimit": "assets_limit",
        "includeProfile": "include_profile",
        "includeFacts": "include_facts",
        "includeAssets": "include_assets",
        "maxStatementLength": "max_statement_length",
        "bizDate": "biz_date",
        "sourcePrompt": "source_prompt",
        "sessionId": "session_id",
        "actionId": "action_id",
    }
    return aliases.get(value, value.replace("-", "_"))


def _plan_actions_payload(value: Any) -> list[dict[str, str]]:
    if value is None or value == "":
        raise CliValidationError("plan save requires at least one --action")
    raw_actions = value if isinstance(value, list) else [value]
    actions: list[dict[str, str]] = []
    for raw in raw_actions:
        if isinstance(raw, dict):
            action_text = str(raw.get("action") or "").strip()
            time_text = str(raw.get("time") or "待定").strip() or "待定"
        else:
            text = str(raw or "").strip()
            if "|" in text:
                time_text, action_text = [part.strip() for part in text.split("|", 1)]
                time_text = time_text or "待定"
            else:
                time_text, action_text = "待定", text
        if not action_text:
            continue
        actions.append({"time": time_text[:32], "action": action_text[:500]})
    if not actions:
        raise CliValidationError("plan save requires at least one non-empty action")
    if len(actions) > 12:
        raise CliValidationError("plan save supports at most 12 actions")
    return actions


def _json_object(value: Any) -> dict[str, Any]:
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError as exc:
        raise CliValidationError(f"payload must be a JSON object: {exc}") from exc
    if not isinstance(parsed, dict):
        raise CliValidationError("payload must be a JSON object")
    return parsed


_SENSITIVE_INPUT_KEYS = {"password", "user_token"}


def _public_effective_input(effective: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in effective.items() if key not in _SENSITIVE_INPUT_KEYS}


def _public_input_sources(sources: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in sources.items() if key not in _SENSITIVE_INPUT_KEYS}


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in user.items() if key != "user_token"}


def _dimensions(value: Any) -> list[str] | None:
    if not value:
        return None
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _value(namespace: argparse.Namespace, key: str, default: Any = None) -> Any:
    return getattr(namespace, key, default)


if __name__ == "__main__":
    raise SystemExit(main())
