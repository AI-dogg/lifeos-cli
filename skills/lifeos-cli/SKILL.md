---
name: lifeos-cli
description: "Use the LifeOS CLI as the user's LifeOS recording and retrieval interface. Trigger when the user wants to record, remember, log, save, sync, inspect, or update personal facts, plans, completed actions, assets, profile state, scores, snapshots, or durable conversation context. Default write path is `lifeos record`."
---

# LifeOS CLI

Use the local `lifeos` command to write to and read from the hosted LifeOS API.
LifeOS follows this chain:

```text
Input -> Facts -> Rules -> Passport -> Manual / Exchange
```

The default recording command is `lifeos record`. Use older precise commands only when the user explicitly needs them.

## Default Write Rule

When the user says "记一下", "记录", "remember this", "log this", "保存上下文", or reports something that should survive the chat, prefer:

```bash
lifeos record --text "..."
```

Add optional context when available:

```bash
lifeos record \
  --text "完成 LifeOS CLI record 主命令，并跑通后端测试" \
  --project LifeOS \
  --tags "CLI,事实层" \
  --evidence "pytest 通过"
```

`record` supports:

- `--text`
- stdin, for example `echo "..." | lifeos record`
- `--input-json`
- `--type`
- `--domain`
- `--occurred-at`
- `--source`
- `--evidence`
- `--project`
- `--person`
- `--tags`
- `--capture-raw`

If the CLI returns `needs_more_detail`, ask one focused follow-up for time, object, result, or evidence. Use `--capture-raw` only when the user explicitly wants to keep the raw fragment despite low detail.

On successful `record`, use `fact`, `ruleProjection`, `assetPrecipitation`, and `projectionRefresh` to understand what was written and which passport/manual/exchange projections refreshed. If `--evidence` was provided, it is preserved in the fact payload and appears in the admin fact ledger as `evidenceSummary`. For raw capture, expect `projectionRefresh.status` to be `candidate`.

## Setup And Identity

Before real operations, run:

```bash
lifeos diagnose
```

If identity is missing, ask the user to register or log in. Do not invent or reveal passwords or tokens.

```bash
lifeos register --name "User Name" --password "password"
lifeos login --name "User Name" --password "password"
```

For a different server:

```bash
lifeos configure --base-url "https://example.com/lifeos" --name "User Name"
```

## Command Selection

- Use `record` for general durable recording: completed work, decisions, learning, reflections, relationship events, project progress, health records, and stable preferences.
- Use `plan save/confirm/get/history` for intended future work on a date.
- Use `action done` only for a completed planned action with a known `action-id`; it writes action evidence as a projected fact and may trigger scoring.
- Use `fact add` only when the user explicitly provides a dimension and wants an advanced fact write.
- Use `profile capture` only for compatibility or explicit profile-signal writes; it writes a profile-signal fact visible in the admin ledger and does not initialize the passport.
- Use `asset add` only for explicit asset backfill or artifact creation; inline backfill writes a backing fact visible in the admin ledger before creating the asset, while normal assets should come from facts.
- Use `snapshot` first for a compact LifeOS passport read-side view; use `profile get`, `score get`, and `asset list` only when you need those specific details.

## Profile Initialization

Before workflows that depend on profile, scoring, daily profile updates, or LifeOS passport interpretation, run:

```bash
lifeos profile get
```

If `life_profile_status` is not `initialized`, collect the 10 initialization answers in natural language, 1-3 questions at a time, then run:

```bash
lifeos profile init --input-json '{
  "mainStoryline": "...",
  "mostWantChange": "...",
  "pastBestPeriod": "...",
  "biggestBlocker": "...",
  "timeSpentDistribution": "...",
  "longTermEnergySources": "...",
  "oneYearIdealState": "...",
  "noConstraintLife": "...",
  "easyToFallIntoPatterns": "...",
  "oneHabitToBuild": "..."
}'
```

## Conversation Sedimentation

Before context compression, handoff, or ending a long useful session, write compact durable signals with `lifeos record`. Do not store the whole transcript.

Good candidates:

- Goals, life-stage changes, decisions, milestones.
- Completed actions and evidence.
- Learnings, reflections, reusable methods, project progress.
- Stable preferences, constraints, relationships, habits, or important context.

Skip jokes, speculation, drafts, temporary todo noise, secrets, and sensitive personal information unless the user confirms.

## Failure Handling

Treat CLI output as JSON and claim success only when `"ok": true`.

- `needs_more_detail`: ask for time, object, result, or evidence; optionally use `--capture-raw` only when the user wants raw preservation.
- `validation_error`: ask only for fields named in `fieldErrors`.
- `auth_or_not_found`: ask the user to log in or provide credentials for login.
- `config_error`: run `lifeos diagnose`; configure base URL or identity.
- `storage_or_http_error`: retry once only if `retryable` is true.

## Operating Rules

- Keep facts objective and based on user-provided information.
- Ask before recording sensitive personal information.
- Do not write secrets, tokens, private keys, or passwords into LifeOS.
- Use explicit dates, preferably `YYYY-MM-DD`, for plans and actions.
- Do not write to LifeOS when the user only asks for advice, a draft, or a hypothetical plan.
- Keep user-facing language friendly: say "记录、计划、行动、目标、成果、复盘、护照", not internal API jargon unless asked.
