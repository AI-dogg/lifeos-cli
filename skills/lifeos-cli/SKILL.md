---
name: lifeos-cli
description: "Use the LifeOS CLI as a personal growth passport for recording and retrieving a user's growth data: stable facts, daily plans, completed actions, profile signals, reusable assets, scores, snapshots, and other accumulated personal context. Trigger when the user wants to record, remember, log, save, sync, inspect, or update personal growth information through the `lifeos` command."
---

# LifeOS CLI Growth Passport

Use the local `lifeos` command to write to and read from the hosted LifeOS API. Treat LifeOS as the user's growth passport: a structured place to accumulate plans, actions, facts, profile signals, assets, and snapshots over time. The CLI defaults to `https://106.55.134.110/lifeos`.

## Agent Flow

Follow this order before running a write command:

1. Decide whether the user wants to write, read, or only discuss.
2. If writing, identify the target: `fact`, `profile`, `plan`, `action`, or `asset`.
3. Check identity after the target is clear. If identity is missing, follow the Identity section.
4. Complete business fields before retrying: date, action list, `action-id`, dimension, kind, title, or summary.
5. Run the CLI and inspect JSON output. Claim success only when `"ok": true`.

If multiple `fieldErrors` appear, handle them in this priority: identity errors first, then missing command fields, then invalid formats. Ask one focused question at a time unless the user explicitly wants a form-style checklist.

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

If a command fails because identity is missing:

- If the user has not registered, ask for a display name and password, then run `lifeos register --name "..." --password "..."`.
- If the user already has an account, ask for the account name and password, then run `lifeos login --name "..." --password "..."`.
- If only `lifeos` is missing, install the CLI first instead of asking for account details.
- Do not print or store passwords outside the CLI command/config flow.

## Decision Guide

- Use `plan` for intended future work on a specific date.
- Use `action` for a confirmed planned task that must be listed, changed, skipped, or completed.
- Use `fact` for stable memory: achievements, habits, important events, preferences, or long-term context.
- Use `profile capture` for identity-shaping growth signals: life stage, long-term goals, key decisions, milestones, and cognitive records.
- Use `asset` for reusable outputs: documents, methods, resources, work products, relationship learnings, or experience summaries.
- Use read commands (`snapshot`, `profile get`, `score get`, `asset list`, `action list`) when the user asks what is known, current, or pending.

If the user says "remember this" and it is both a completed action and a durable achievement, prefer `action done` when there is a matching planned action; otherwise use `fact add` and optionally `asset add` if there is a reusable artifact.

## Vocabulary

Fact dimensions:

- `life_stage`: current stage, role, situation, or life chapter.
- `long_term_goal`: durable goals and direction.
- `key_decision`: important choices and commitments.
- `milestone`: meaningful progress markers or achievements.
- `action_completion`: completed behaviors or task outcomes.
- `sleep`, `exercise`, `diet`: health records.
- `cognitive_record`: insights, reflections, mental models, or learning.
- `work_output`: shipped work or concrete outputs.
- `relationship_interaction`: meaningful relationship events.

Asset kinds:

- `cognitive_asset`: reusable insight or mental model.
- `method_asset`: method, workflow, or practice.
- `work_asset`: concrete work output.
- `relationship_asset`: relationship learning or interaction pattern.
- `experience_asset`: experience, milestone, or story.
- `resource_asset`: external or internal resource worth reusing.

## Command Selection

Use `lifeos fact add` for stable personal facts, growth milestones, and long-term memory:

```bash
lifeos fact add --dimension work_output --statement "Published the first version of my growth passport CLI."
```

If required details are missing:

- Missing `dimension`: infer a likely dimension from Vocabulary only when obvious; otherwise ask the user to choose.
- Missing `statement`: ask the user for the exact fact to remember in one sentence.
- Sensitive or private fact: ask for confirmation before recording.

Use `lifeos profile capture` for profile-shaping signals such as life stage, long-term goals, key decisions, milestones, and cognitive records:

```bash
lifeos profile capture --dimension long_term_goal --statement "Build a durable personal growth passport."
```

If required details are missing:

- Missing `dimension`: ask which profile signal this is: `life_stage`, `long_term_goal`, `key_decision`, `milestone`, or `cognitive_record`.
- Missing `statement`: ask for the profile signal in the user's own words.
- If the content is only a temporary task, use `plan` or `action` instead of `profile capture`.

Use plan commands for things the user intends to do on a date:

```bash
lifeos plan save --date YYYY-MM-DD --action "09:00|Write launch notes" --action "11:00|Test CLI install"
lifeos plan confirm --date YYYY-MM-DD
lifeos plan get --date YYYY-MM-DD
lifeos plan history --limit 30
```

If required details are missing:

- Missing date: ask for the target date; if the user says today/tomorrow, resolve it to `YYYY-MM-DD` before calling the CLI.
- Missing actions for `plan save`: ask for the action list and times. If times are not known, ask whether to use rough slots.
- Missing confirmation intent: save the draft first, then ask whether to run `lifeos plan confirm --date YYYY-MM-DD`.
- User asks to view a plan without a date: ask for a date, or use today's exact date only when that is clearly intended.

Use action commands for planned task execution:

```bash
lifeos action list --date YYYY-MM-DD
lifeos action update --action-id ACTION_ID --status pending
lifeos action done --action-id ACTION_ID --text "Completed and verified."
```

`lifeos action done` has side effects: it records completion evidence, triggers daily check-in behavior, and can trigger scoring when the profile is initialized. Use it only when the user is actually reporting a completed planned action.

If required details are missing:

- Missing `action-id`: run `lifeos action list --date YYYY-MM-DD` first, then choose the matching action if unambiguous; otherwise ask the user to pick.
- Missing date for action lookup: ask for the date, or use today's exact date only when the user is clearly discussing today.
- Missing completion evidence for `action done`: ask what was completed or what proof/result should be recorded.
- Missing status for `action update`: ask whether the status should be `pending`, `done`, or `skipped`.

Use asset commands for outputs, methods, resources, and reusable growth artifacts:

```bash
lifeos asset add --kind work_asset --title "Growth Passport CLI" --summary "A command line client for recording personal growth data."
lifeos asset list
lifeos assets backfill
```

If required details are missing:

- Missing `kind`: infer a likely kind from Vocabulary only when obvious; otherwise ask the user to choose.
- Missing `title`: ask for a short title.
- Missing `summary` and no `from-fact-id`: ask for a concise summary of the artifact or outcome.
- User asks to list assets without a limit: use `lifeos asset list` first; add `--limit` only when the user asks for a bounded list.

Use read commands to inspect state:

```bash
lifeos snapshot
lifeos profile get
lifeos score get
lifeos schema
```

If read commands fail or lack context:

- Missing identity: follow the identity recovery flow above.
- Snapshot too broad: ask which area, date range, or dimension the user wants, then rerun with filters when supported.
- Need command details: run `lifeos help` or `lifeos schema`.

## Failure Handling

When a command returns JSON with `"ok": false`, inspect `code`, `message`, and `fieldErrors`.

- `validation_error`: ask only for the fields named in `fieldErrors`, then rerun the command.
- `auth_or_not_found`: run `lifeos login` if credentials are available; otherwise ask the user to log in or provide account credentials.
- `config_error`: run `lifeos diagnose`; if base URL is missing or wrong, run `lifeos configure --base-url "..."`.
- `storage_or_http_error`: retry once only if `retryable` is true; otherwise report the message and ask whether to continue later.
- `unexpected_error`: report the message briefly and avoid repeating the same command without changing inputs.

If `fieldErrors` includes identity fields together with command fields, collect identity and command details before retrying so the user does not get asked in circles. Example: for missing `user_token` and missing `actions`, ask for login/register first, then ask for the plan actions.

## Operating Rules

- Treat CLI output as JSON; check `"ok": true` before claiming success.
- Use explicit dates, preferably `YYYY-MM-DD`, when recording plans or actions.
- Do not write secrets, raw tokens, private keys, or passwords into LifeOS.
- Ask before recording sensitive personal information.
- Do not write to LifeOS when the user only asks for advice, a draft, or a hypothetical plan.
- Prefer `plan` and `action` for daily execution; do not store daily todos only as facts.
- Prefer `fact`, `profile`, and `asset` for durable memory that should affect future context.
- If a command fails with auth errors, ask the user to run `lifeos login` or provide credentials for login.
- If the user intent is ambiguous, ask one short clarifying question before writing.
- If the CLI returns validation field errors, use the `fieldErrors` payload to ask only for the missing or invalid fields.
