from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.1.0"
CLI_VERSION = "0.1.1"
BACKEND_CONTRACT_VERSION = "0.1.0"
CLI_SOURCE = "lifeos_cli"

EXIT_CODES = {
    "success": 0,
    "validation_error": 2,
    "needs_more_detail": 3,
    "auth_or_not_found": 4,
    "config_error": 5,
    "storage_or_http_error": 10,
    "unexpected_error": 20,
}

EVENT_DIMENSIONS = frozenset(
    {
        "action_completion",
        "sleep",
        "exercise",
        "diet",
        "raw_capture",
        "daily_action",
        "reflection",
        "learning",
        "relationship_event",
        "project_progress",
    }
)
FACT_DIMENSIONS = frozenset(
    {
        "life_stage",
        "long_term_goal",
        "key_decision",
        "milestone",
        "action_completion",
        "sleep",
        "exercise",
        "diet",
        "cognitive_record",
        "work_output",
        "relationship_interaction",
        "raw_capture",
        "daily_action",
        "decision",
        "reflection",
        "learning",
        "relationship_event",
        "project_progress",
    }
)
PROFILE_SIGNAL_DIMENSIONS = frozenset(
    {
        "life_stage",
        "long_term_goal",
        "key_decision",
        "milestone",
        "cognitive_record",
        "decision",
        "reflection",
        "learning",
        "project_progress",
    }
)
AUTO_ASSET_DIMENSIONS = frozenset(
    {"cognitive_record", "work_output", "learning", "reflection", "project_progress"}
)
OPTIONAL_ASSET_DIMENSIONS = frozenset(
    {"relationship_interaction", "milestone", "action_completion"}
)
ASSET_KIND_BACKING_DIMENSIONS = {
    "cognitive_asset": "cognitive_record",
    "method_asset": "action_completion",
    "work_asset": "work_output",
    "relationship_asset": "relationship_interaction",
    "experience_asset": "milestone",
    "resource_asset": "cognitive_record",
}
ASSET_KINDS = frozenset(ASSET_KIND_BACKING_DIMENSIONS)
ANSWER_FIELDS = (
    "main_storyline",
    "most_want_change",
    "past_best_period",
    "biggest_blocker",
    "time_spent_distribution",
    "long_term_energy_sources",
    "one_year_ideal_state",
    "no_constraint_life",
    "easy_to_fall_into_patterns",
    "one_habit_to_build",
)


def cli_schema() -> dict[str, Any]:
    return {
        "ok": True,
        "schemaVersion": SCHEMA_VERSION,
        "cliVersion": CLI_VERSION,
        "backendContractVersion": BACKEND_CONTRACT_VERSION,
        "command": "schema",
        "source": CLI_SOURCE,
        "capabilities": {
            "inputJson": True,
            "dryRun": True,
            "httpMode": True,
            "profileCapture": True,
            "assetBackfill": True,
            "userConfirmedBrief": True,
            "confirmationText": True,
            "occurredAt": True,
            "idempotencyKey": True,
            "fromFactId": True,
            "snapshotFilters": True,
            "register": True,
            "login": True,
            "envIdentity": True,
            "userTokenAuth": True,
            "passwordTokenRecovery": True,
            "autoRegisterByName": False,
            "planLayer": True,
            "actionLayer": True,
            "scoreRead": True,
            "profileRead": True,
            "profileInit": True,
            "assetList": True,
            "insecureTls": True,
            "recordCommand": True,
            "rawCapture": True,
            "ruleProjection": True,
            "projectionRefresh": True,
            "factEvidencePayload": True,
            "adminLedgerEvidenceSummary": True,
        },
        "compatibility": {
            "minor": "may add optional fields without changing existing semantics",
            "patch": "must not change existing field semantics",
            "major": "required for field removal, rename, or meaning change",
        },
        "commands": {
            "fact.add": {
                "dimensions": sorted(FACT_DIMENSIONS),
                "eventDimensions": sorted(EVENT_DIMENSIONS),
            },
            "record": {
                "writes": ["facts"],
                "dimensions": sorted(FACT_DIMENSIONS),
                "input": ["text", "stdin", "inputJson"],
                "optionalFields": [
                    "type",
                    "domain",
                    "occurredAt",
                    "source",
                    "evidence",
                    "project",
                    "person",
                    "tags",
                    "captureRaw",
                ],
                "ruleProjection": ["bahao", "powers", "asset", "passport", "manual", "exchange"],
                "factPayload": ["captureIntent", "evidence", "ruleProjection", "projectionRefresh"],
                "adminLedger": ["sourceGroups", "projectionSummary", "evidenceSummary"],
                "returns": [
                    "fact",
                    "ruleProjection",
                    "assetPrecipitation",
                    "projectionRefresh",
                    "passportProjection",
                    "manualProjection",
                    "exchangeProjection",
                ],
            },
            "asset.add": {
                "kinds": sorted(ASSET_KINDS),
                "backingDimensions": ASSET_KIND_BACKING_DIMENSIONS,
            },
            "asset.list": {"filters": ["limit"]},
            "plan.save": {
                "writes": ["daily_plan_drafts", "daily_plan_draft_actions"],
                "actionFormat": "time|action",
                "maxActions": 12,
            },
            "plan.get": {"reads": ["daily_plan_actions"]},
            "plan.draft.get": {"reads": ["daily_plan_drafts"]},
            "plan.draft.update": {"writes": ["daily_plan_draft_actions"]},
            "plan.confirm": {
                "writes": ["daily_plan_actions"],
                "note": "confirms the latest draft for the date and replaces confirmed actions for that date",
            },
            "plan.history": {"reads": ["daily_plan_actions"]},
            "action.list": {"reads": ["daily_plan_actions"]},
            "action.update": {"writes": ["daily_plan_actions"]},
            "action.done": {
                "writes": ["daily_plan_actions", "bahao_checkins", "fact_events"],
                "scoring": "triggers seven-power AI scoring when life profile is initialized",
                "factPayload": ["captureIntent", "ruleProjection", "projectionRefresh"],
            },
            "score.get": {"reads": ["power_scores", "power_score_events"]},
            "profile.capture": {
                "dimensions": sorted(PROFILE_SIGNAL_DIMENSIONS),
                "writes": ["facts"],
                "doesNotWrite": ["life_profiles"],
                "profileWritePolicy": "fact_first",
            },
            "profile.get": {"reads": ["life_profiles"]},
            "profile.init": {
                "writes": ["life_profiles"],
                "requires": list(ANSWER_FIELDS),
                "note": "initializes the LifeOS passport; profile.capture only writes objective profile facts",
            },
            "snapshot": {},
            "assets.backfill": {},
            "diagnose": {},
            "register": {
                "env": ["LIFEOS_USER_ID", "LIFEOS_USER_TOKEN", "LIFEOS_USER_NAME", "LIFEOS_NAME"],
                "autoGeneratesUserId": True,
                "requiresPassword": True,
                "returnsUserToken": True,
            },
            "login": {
                "env": ["LIFEOS_USER_TOKEN", "LIFEOS_PASSWORD"],
                "requires": ["name", "password"],
                "returnsUserToken": True,
            },
        },
        "exitCodes": EXIT_CODES,
    }
