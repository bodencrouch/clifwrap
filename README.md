# clifwrap

[![CI](https://github.com/bodencrouch/clifwrap/actions/workflows/ci.yml/badge.svg)](https://github.com/bodencrouch/clifwrap/actions/workflows/ci.yml)

`clifwrap` puts a thin shim in front of CLIs like `searchcli` and `scrapecli`. When one account hits a quota wall, rate limit, or auth error, the wrapper retries the same command on your next configured account.

Nothing changes unless you ask for it:

- No config file → the CLI runs as before.
- No shim installed → your original binary is untouched.
- `clifwrap uninstall` puts the original back.
- Provider-specific rules live in `providers.toml`, not scattered through the Python code.

## Why use it

Tools like SearchCLI and ScrapeCLI accept credentials from several places — env vars, config files, OAuth tokens. If you run more than one account, switching by hand is tedious and easy to get wrong.

`clifwrap` maps named accounts to env vars (or secret lookups), picks a starting account, and walks the list when a retryable failure comes back. For interactive CLIs, it can run a line-by-line shell and route each command through the same failover logic.

## Install

```bash
pipx install .
mkdir -p ~/.config/clifwrap
clifwrap sample-config > ~/.config/clifwrap/config.toml
clifwrap install searchcli scrapecli
```

This finds `searchcli` and `scrapecli` on your PATH, saves the originals under `~/.local/state/clifwrap/`, and replaces them with managed shims.

If your config already lists providers, `clifwrap install` with no arguments wraps all of them. Same idea for `clifwrap uninstall` — no arguments restores every shim the wrapper knows about.

Running install twice is safe. If a shim is already in place and the backup is recorded, install is a no-op.

### Build config step by step

```bash
clifwrap init
clifwrap account add searchcli primary --env-file ~/.config/secrets.env --env-ref SEARCHCLI_API_KEY=SEARCHCLI_PRIMARY
clifwrap account add searchcli backup --env-file ~/.config/secrets.env --env-ref SEARCHCLI_API_KEY=SEARCHCLI_BACKUP
clifwrap account add somecli dynamic --env-command SOMECLI_TOKEN='secret-tool lookup service somecli account dynamic'
clifwrap account list searchcli
clifwrap account list searchcli --json
clifwrap doctor --check
clifwrap install
```

### Remove it

```bash
clifwrap uninstall searchcli scrapecli
pipx uninstall clifwrap
```

Uninstall refuses to run if the backup is missing or the target is no longer a managed shim. That way you do not accidentally overwrite a binary the wrapper did not install.

## Config

Default path: `~/.config/clifwrap/config.toml`. Override with `CLIFWRAP_CONFIG=/path/to/config.toml`.

### SearchCLI example

```toml
[[providers.searchcli.accounts]]
name = "acct-a"
env_files = ["~/.config/secrets.env"]
env = { SEARCHCLI_API_KEY = "env:SEARCHCLI_TEAM_A_KEY" }

[[providers.searchcli.accounts]]
name = "acct-b"
env_files = ["~/.config/secrets.env"]
env = { SEARCHCLI_API_KEY = "env:SEARCHCLI_TEAM_B_KEY" }
```

### ScrapeCLI example

```toml
[[providers.scrapecli.accounts]]
name = "team-a"
env_files = ["~/.config/secrets.env"]
env = { SCRAPECLI_API_KEY = "env:SCRAPECLI_TEAM_A_KEY" }

[[providers.scrapecli.accounts]]
name = "team-b"
env_files = ["~/.config/secrets.env"]
env = { SCRAPECLI_API_KEY = "env:SCRAPECLI_TEAM_B_KEY" }
```

Retry rules, auth command names, and usage endpoints for SearchCLI and ScrapeCLI ship in `src/clifwrap/providers.toml`. Your config usually only needs account entries.

See [docs/configuration.md](docs/configuration.md) for the full reference.

### Capacity control

You can block or defer requests before they hit the upstream CLI when quota is low:

```toml
[providers.somecli]
status_command = ["somecli", "usage", "--json"]

[providers.somecli.capacity_control]
default_action = "queue"
unknown_capacity_action = "allow"
reserve_threshold = 5
default_cost = 1
queue_retention_seconds = 86400
queue_max_items = 100
snapshot_ttl_seconds = 60
command_costs = { search = 2, extract = 5 }
remediation_message = "Provision more credits or enable another account."
remediation_commands = ["clifwrap account add somecli <name> --env-ref SOMECLI_TOKEN=ENVVAR"]
```

- `default_action` — what to do when every account is below `reserve_threshold + estimated_cost`. Values: `execute`, `queue`, `shed`.
- `unknown_capacity_action` — what to do when usage data is unavailable everywhere. Values: `allow`, `queue`, `shed`.

Command costs are estimates, not billing truth. SearchCLI and ScrapeCLI defaults live in `providers.toml` so you can override them without touching code.

When capacity control picks an account, retries for that request stay on that account. A retryable upstream error will not burn through your reserve accounts.

With `proactive_pick` enabled (default when usage or `status_command` is configured), clifwrap also picks the best starting account before the first upstream call so a depleted default does not burn a retry. See [docs/configuration.md](docs/configuration.md#proactive-starting-account).

### Account management from the wrapped CLI

Upstream auth still works as usual:

```bash
searchcli auth
scrapecli login
```

Wrapper account commands sit under explicit subcommands:

```bash
searchcli auth list
searchcli logins
searchcli logins use acct-b
searchcli credentials default
searchcli auth use acct-b
searchcli auth add acct-c --env-file ~/.config/secrets.env --env-ref SEARCHCLI_API_KEY=SEARCHCLI_TEAM_C_KEY
searchcli auth add acct-d --env-command SEARCHCLI_API_KEY='secret-tool lookup service searchcli account acct-d'
searchcli auth disable acct-c
searchcli auth enable acct-c
searchcli auth remove acct-c

scrapecli login accounts
scrapecli accounts
scrapecli login use team-b
scrapecli login add team-c --env-file ~/.config/secrets.env --env-ref SCRAPECLI_API_KEY=SCRAPECLI_TEAM_C_KEY
scrapecli login add team-d --env-command SCRAPECLI_API_KEY='secret-tool lookup service scrapecli account team-d'
scrapecli login disable team-c
scrapecli login remove team-c
```

For SearchCLI, wrapper aliases include `accounts`, `logins`, and `credentials`. For ScrapeCLI, they live under `login` plus any aliases you configure. A bare alias like `searchcli logins` lists accounts; bare `searchcli auth` or `scrapecli login` still goes to the real CLI.

`clifwrap account list --json` returns labels, enabled/default flags, env key names, file paths, and prepare-command metadata. It never prints secret values.

ScrapeCLI's browser login stores one active credential. For multi-account failover, give each account its own credential source. The wrapper sets `SCRAPECLI_API_KEY` before calling upstream. Sources can be env refs, files, command lookups, or keys captured by a helper script.

To import several ScrapeCLI accounts from a spec file:

```bash
clifwrap account import-spec scripts/scrapecli_requested_accounts.toml --apply
```

The spec can include a `[validation]` block (usage URL, auth header, response path). Import validates each key before adding it and skips accounts with missing or bad keys. Re-running with `--apply` updates existing entries instead of duplicating them. Use `env_name_template` to derive env var names from account labels.

To capture keys through ScrapeCLI's interactive login:

```bash
python scripts/scrapecli_login_sequence.py
```

The script reads account labels from the spec, runs `scrapecli login` for each missing account, stores keys in your env file, then runs `clifwrap account import-spec ... --apply`. It does not print secrets. Pass `--method manual` to skip browser login, or `--replace-existing` to refresh keys you already have.

When failover succeeds, the wrapper saves the working account as the new default. `CLIFWRAP_ACCOUNT=<name>` overrides that for one command.

### Prepare commands

Some CLIs need a login step before env injection works:

```toml
[[providers.somecli.accounts]]
name = "persisted-login"
env = { SOMECLI_TOKEN = "env:SOMECLI_TOKEN_A" }
env_command = { SOMECLI_REFRESHED_TOKEN = ["secret-tool", "lookup", "service", "somecli"] }
prepare_on = "once"
prepare_command = ["somecli", "login", "--token", "${SOMECLI_TOKEN}"]
```

`env_command` runs before each attempt; stdout becomes the env value. `prepare_command` runs right before that account is tried. Set `prepare_on` to `once` (idempotent), `always`, or `never`.

Pick a starting account for one run:

```bash
CLIFWRAP_ACCOUNT=secondary searchcli search "autoclaw cli"
```

## Status

```bash
clifwrap status                  # all configured providers
clifwrap status scrapecli        # one provider
clifwrap status --json           # JSON for all
clifwrap status --json scrapecli
clifwrap status --check          # exit 1 on low fallback or recovery-hook errors
clifwrap status --json --check scrapecli
```

For SearchCLI, status calls `GET /usage` when the account has `SEARCHCLI_API_KEY`. For ScrapeCLI, it calls `GET /v2/team/credit-usage` when `SCRAPECLI_API_KEY` is set.

When usage data includes remaining counts, status also prints total capacity across all available accounts.

For other providers, set a `status_command` that prints JSON with `remaining`, `limit`, and optionally `used`:

```toml
[providers.somecli]
status_command = ["somecli", "usage", "--json"]
```

HTTP lookup timeouts: set `timeout_seconds` under `[providers.<name>.usage]`, or override at runtime with `CLIFWRAP_PROVIDER_<NAME>_USAGE_TIMEOUT_SECONDS`.

With capacity control enabled, status also reports queue backlog, expired items, and any remediation message from config.

`status --check` exits nonzero on queue backlog, queue errors, or low capacity — in addition to low-fallback and recovery-hook signals.

## Doctor

Local checks for config, shims, and queue state:

```bash
clifwrap doctor
clifwrap doctor --json --check
```

Run this before editing state by hand. `--check` exits nonzero on config parse errors, bad install state, missing backups, broken default-account pointers, or malformed queue data.

Config-only checks:

```bash
clifwrap config paths
clifwrap config paths --json
clifwrap config validate
clifwrap config validate --json
```

`config paths` shows resolved config, state, and shim-bin paths after env overrides. `config validate` parses `config.toml` the same way wrapped commands do.

## Queue

When a command is queued, the wrapper stores provider, argv, enqueue time, replay count, reason, and policy snapshot, then exits with code `73`.

```bash
clifwrap queue list
clifwrap queue list scrapecli --json
clifwrap queue run
clifwrap queue run searchcli --id <queue-id>
clifwrap queue drop scrapecli --expired
```

`queue run` rechecks capacity before replay. If still blocked, the item stays queued and replay metadata updates — no duplicate entry. Success removes the item.

Runtime overrides for capacity policy:

```bash
CLIFWRAP_PROVIDER_SCRAPECLI_CAPACITY_DEFAULT_ACTION=queue \
CLIFWRAP_PROVIDER_SCRAPECLI_CAPACITY_UNKNOWN_ACTION=allow \
CLIFWRAP_PROVIDER_SCRAPECLI_CAPACITY_RESERVE_THRESHOLD=50 \
CLIFWRAP_PROVIDER_SCRAPECLI_CAPACITY_DEFAULT_COST=5 \
CLIFWRAP_PROVIDER_SCRAPECLI_CAPACITY_COMMAND_COSTS="crawl=25,scrape=5,search=5" \
CLIFWRAP_PROVIDER_SCRAPECLI_QUEUE_RETENTION_SECONDS=3600 \
CLIFWRAP_PROVIDER_SCRAPECLI_QUEUE_MAX_ITEMS=250 \
scrapecli crawl https://example.com
```

## Low-fallback warnings

For `searchcli` and `scrapecli`, the wrapper warns when fewer than three unused enabled accounts remain. Custom providers can opt in:

```toml
[providers.somecli.fallback_monitor]
threshold = 3
action = "warn"
journald = true
syslog = true
stderr = true
recovery_command = ["notify-send", "somecli fallbacks are low"]
```

"Unused fallbacks" means enabled accounts minus the one currently active. Warnings go to journald (via `systemd-cat` when available), syslog, and stderr as configured.

Set `action = "fail"` to stop wrapped commands while the pool is below threshold (exit `75`). Default is `warn`.

The optional `recovery_command` runs once per distinct low-pool state in the background. It receives `CLIFWRAP_PROVIDER`, `CLIFWRAP_LOW_FALLBACK_MESSAGE`, `CLIFWRAP_LOW_FALLBACK_ENABLED`, `CLIFWRAP_LOW_FALLBACK_UNUSED`, `CLIFWRAP_LOW_FALLBACK_THRESHOLD`, `CLIFWRAP_LOW_FALLBACK_ACTIVE`, and `CLIFWRAP_LOW_FALLBACK_ENABLED_NAMES`. If the hook fails to start, `clifwrap status` reports that until a later launch succeeds.

Runtime overrides:

```bash
CLIFWRAP_PROVIDER_SCRAPECLI_FALLBACK_THRESHOLD=2 \
CLIFWRAP_PROVIDER_SCRAPECLI_FALLBACK_ACTION=warn \
CLIFWRAP_PROVIDER_SCRAPECLI_FALLBACK_JOURNALD=true \
CLIFWRAP_PROVIDER_SCRAPECLI_FALLBACK_SYSLOG=true \
CLIFWRAP_PROVIDER_SCRAPECLI_FALLBACK_STDERR=true \
CLIFWRAP_PROVIDER_SCRAPECLI_FALLBACK_RECOVERY_COMMAND="notify-send,scrapecli fallbacks are low" \
scrapecli search "example"
```

## Notes

- Failed attempts are buffered; you see the final successful output plus short failover notices on stderr.
- If no account matches or no retry rule fires, you get the original exit code and output.
- The wrapper does not touch upstream config unless you use a `prepare_command` that does. Wrapper state lives under `~/.local/state/clifwrap/`.

## Docs

- [Configuration](docs/configuration.md)
- [Provider authoring](docs/provider-authoring.md)
- [CLI reference](docs/cli-reference.md)
- [Built-in provider catalog](docs/provider-catalog.md)
- [Migration from cli-fallback-wrapper](docs/migration.md)
- [Operations runbook](docs/operations.md)
- [Release process](docs/release.md)
- [Research notes](docs/RESEARCH.md)
- [Security policy](SECURITY.md)

## Releases

Repo: [github.com/bodencrouch/clifwrap](https://github.com/bodencrouch/clifwrap). Docs and test reports: [bodencrouch.github.io/clifwrap](https://bodencrouch.github.io/clifwrap/).

Releases are cut by release-please. New GitHub releases start as prerelease while CI runs tests, builds PyInstaller binaries, uploads artifacts, and writes `SHA256SUMS` and `RELEASE-MANIFEST.json`. The release is marked stable only after those jobs pass.
