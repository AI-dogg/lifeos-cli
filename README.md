# LifeOS CLI

Open-source command line client for LifeOS.

The CLI runs locally and calls a remote LifeOS API. It stores local configuration in
`~/.lifeos/cli.env` by default.

## Install

Install from GitHub:

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

## Configure

Point the CLI at your LifeOS API:

```bash
lifeos configure \
  --base-url "https://106.55.134.110/lifeos" \
  --name "Your Name" \
  --insecure
```

`--insecure` allows a temporary self-signed HTTPS certificate. Remove it after
you attach a real domain and certificate.

Register or log in:

```bash
lifeos register --password "your-password"
lifeos login --password "your-password"
```

## Use

```bash
lifeos diagnose
lifeos snapshot
lifeos fact add --dimension work_output --statement "Published the LifeOS CLI."
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
LIFEOS_CLI_BASE_URL=https://your-lifeos-api.example.com
LIFEOS_CLI_INSECURE_TLS=false
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
