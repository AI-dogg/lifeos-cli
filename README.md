# LifeOS CLI

Open-source command line client for LifeOS.

The CLI runs locally and calls the LifeOS API at
`https://106.55.134.110/lifeos` by default. It stores local configuration in
`~/.lifeos/cli.env` when you change settings or log in.

## Install CLI + Skill

### 1. Install the CLI

```bash
python3 -m pip install --user --upgrade \
  "git+https://github.com/AI-dogg/lifeos-cli.git"
```

Or use `pipx`:

```bash
brew install pipx
pipx install "git+https://github.com/AI-dogg/lifeos-cli.git"
```

If your shell cannot find `lifeos`, add your user bin directory to `PATH`:

```bash
export PATH="$HOME/Library/Python/3.*/bin:$HOME/.local/bin:$PATH"
```

### 2. Install the AI skill

The skill tells an AI agent when and how to use `lifeos` as a personal growth
passport for facts, plans, actions, assets, profile signals, snapshots, and
diagnostics.

Copy the skill into your agent runtime's skills directory:

```bash
git clone https://github.com/AI-dogg/lifeos-cli.git
cp -R lifeos-cli/skills/lifeos-cli /path/to/your/skills/
```

For example, if your runtime reads skills from `~/.codex/skills`:

```bash
mkdir -p ~/.codex/skills
cp -R lifeos-cli/skills/lifeos-cli ~/.codex/skills/
```

### 3. Register and verify

After installation, the CLI already points at the current LifeOS server:

```bash
lifeos register --name "Your Name" --password "your-password"
lifeos diagnose
```

The default server currently uses a temporary self-signed HTTPS certificate, so
the CLI allows that certificate by default. Turn this off after you attach a real
domain and certificate.

## Configure

Override the default server or account name:

```bash
lifeos configure \
  --base-url "https://your-lifeos-api.example.com" \
  --name "Your Name"
```

## Use

```bash
lifeos diagnose
lifeos snapshot
lifeos fact add --dimension work_output --statement "Published my growth passport CLI."
lifeos plan save --date 2026-06-18 --action "09:00|Write plan"
lifeos plan confirm --date 2026-06-18
lifeos action list --date 2026-06-18
```

Run `lifeos help` for the full command list.

## Configuration

The CLI reads values from command arguments, environment variables, and
`~/.lifeos/cli.env`.

Common values:

```bash
LIFEOS_CLI_BASE_URL=https://106.55.134.110/lifeos
LIFEOS_CLI_INSECURE_TLS=true
LIFEOS_USER_ID=...
LIFEOS_USER_TOKEN=...
LIFEOS_USER_NAME=...
```

Use a custom config path:

```bash
export LIFEOS_CLI_CONFIG="$HOME/.config/lifeos/cli.env"
```

## Development

```bash
python3 -m pip install -e .
lifeos schema
```

## License

MIT
