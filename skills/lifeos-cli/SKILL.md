---
name: lifeos-cli
description: "Use when Codex should call the LifeOS CLI to persist or read LifeOS data: remember facts, save or confirm daily plans, list/update/complete actions, capture profile signals, add/list assets, get scores, diagnose the API, or fetch a user snapshot. Trigger when the user asks to record, remember, log, save, sync, inspect, or update LifeOS state through the `lifeos` command."
---

# LifeOS CLI

Use the local `lifeos` command to write to and read from the hosted LifeOS API. The CLI defaults to `https://106.55.134.110/lifeos`.

## Setup Check

Run this first when the user wants an actual LifeOS operation:

```bash
lifeos diagnose
```

If `lifeos` is missing, install it:

```bash
python3 -m pip install --user --upgrade "git+https://github.com/AI-dogg/lifeos-cli.git"
```

If the command is still not found, add common user bin paths:

```bash
export PATH="$HOME/Library/Python/3.*/bin:$HOME/.local/bin:$PATH"
```

## Identity

The CLI stores configuration in `~/.lifeos/cli.env`. It reads `LIFEOS_USER_ID`, `LIFEOS_USER_TOKEN`, `LIFEOS_USER_NAME`, and `LIFEOS_PASSWORD`.

Register or log in only when the user provides credentials. Do not invent or expose passwords or tokens.

```bash
lifeos register --name "User Name" --password "password"
lifeos login --name "User Name" --password "password"
```

For a different server:

```bash
lifeos configure --base-url "https://example.com/lifeos" --name "User Name"
```

The default server currently uses a temporary self-signed HTTPS certificate, and the CLI allows it by default. Prefer a real domain and certificate for production.

## Command Selection

Use `lifeos fact add` for stable user facts and long-term memory:

```bash
lifeos fact add --dimension work_output --statement "Published the LifeOS CLI."
```

Use `lifeos profile capture` for profile-shaping signals:

```bash
lifeos profile capture --dimension long_term_goal --statement "Build LifeOS into a durable personal operating system."
```

Use plan commands for things the user intends to do on a date:

```bash
lifeos plan save --date YYYY-MM-DD --action "09:00|Write launch notes" --action "11:00|Test CLI install"
lifeos plan confirm --date YYYY-MM-DD
lifeos plan get --date YYYY-MM-DD
lifeos plan history --limit 30
```

Use action commands for planned task execution:

```bash
lifeos action list --date YYYY-MM-DD
lifeos action update --action-id ACTION_ID --status pending
lifeos action done --action-id ACTION_ID --text "Completed and verified."
```

Use asset commands for outputs, methods, resources, and reusable artifacts:

```bash
lifeos asset add --kind work_asset --title "LifeOS CLI" --summary "Open-source command line client for LifeOS."
lifeos asset list
lifeos assets backfill
```

Use read commands to inspect state:

```bash
lifeos snapshot
lifeos profile get
lifeos score get
lifeos schema
```

## Operating Rules

- Treat CLI output as JSON; check `"ok": true` before claiming success.
- Use explicit dates, preferably `YYYY-MM-DD`, when recording plans or actions.
- Do not write secrets, raw tokens, private keys, or passwords into LifeOS.
- Ask before recording sensitive personal information.
- Prefer `plan` and `action` for daily execution; do not store daily todos only as facts.
- Prefer `fact`, `profile`, and `asset` for durable memory that should affect future context.
- If a command fails with auth errors, ask the user to run `lifeos login` or provide credentials for login.
