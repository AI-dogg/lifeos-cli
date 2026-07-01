---
name: lifeos_cli
description: Use the LifeOS CLI to record and retrieve LifeOS data. Default write path is `lifeos record`; use precise legacy commands only when explicitly needed.
---

# LifeOS CLI

LifeOS records the user's life through:

```text
Input -> Facts -> Rules -> Passport -> Manual / Exchange
```

## Default Recording

For "remember this", "log this", "记一下", completed work, decisions, learning, reflections, relationship events, project progress, or durable context, use:

```bash
lifeos record --text "..."
```

Add context when known:

```bash
lifeos record --text "..." --project LifeOS --person "Name" --tags "CLI,事实层" --evidence "..."
```

`record` supports `--text`, stdin, `--input-json`, `--type`, `--domain`, `--occurred-at`, `--source`, `--evidence`, `--project`, `--person`, `--tags`, and `--capture-raw`.

If `record` returns `needs_more_detail`, ask one focused follow-up. Use `--capture-raw` only when the user explicitly wants to preserve the raw fragment.

When `record` succeeds, inspect `projectionRefresh` with `fact`, `ruleProjection`, and `assetPrecipitation` to know whether passport/manual/exchange projections were refreshed or left as raw candidates. If `--evidence` was provided, it is preserved in the fact payload and appears in the admin fact ledger as `evidenceSummary`.

## Initialization Gate

Before profile/scoring-dependent workflows, run:

```bash
lifeos profile get
```

If uninitialized, collect the 10 initialization answers and run `lifeos profile init --input-json '{...}'`.

## Command Selection

1. Register/login when identity is missing.
2. Use `lifeos record` for general durable recording.
3. Use `lifeos plan save/confirm/get/history` for future dated plans.
4. Use `lifeos action done` for completed planned actions with an `action-id`; it writes a projected action fact.
5. Use `lifeos fact add`, `lifeos profile capture`, and `lifeos asset add` only as advanced/compatibility commands; `profile capture` still writes a profile-signal fact visible in the admin ledger.
6. Read with `lifeos snapshot`, `lifeos profile get`, `lifeos score get`, or `lifeos asset list`.

## Rules

- Do not fabricate answers or facts.
- Keep facts objective and user-provided.
- Ask before recording sensitive personal information.
- Do not expose tokens, passwords, or local config contents.
- Treat CLI output as JSON; claim success only when `"ok": true`.
