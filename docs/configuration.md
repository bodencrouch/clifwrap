# Configuration

Runtime policy lives in TOML. Environment variables can override paths and many per-provider settings at execution time.

Default config path:

```text
~/.config/clifwrap/config.toml
```

Override paths:

```bash
CLIFWRAP_CONFIG=/path/to/config.toml
CLIFWRAP_STATE_DIR=/path/to/state
CLIFWRAP_BIN_DIR=/path/to/bin
```

## Providers

Built-in metadata for `searchcli` and `scrapecli` is in `src/clifwrap/providers.toml`. Your config normally only defines accounts and local overrides.

```toml
[[providers.searchcli.accounts]]
name = "primary"
env_files = ["~/.config/secrets.env"]
env = { SEARCHCLI_API_KEY = "env:SEARCHCLI_API_KEY" }

[[providers.searchcli.accounts]]
name = "backup"
env_files = ["~/.config/secrets.env"]
env = { SEARCHCLI_API_KEY = "env:SEARCHCLI_API_KEY_BACKUP" }
```

Account names are labels you choose. They are not derived from provider conventions.

Provider names are treated as data. `clifwrap account add` writes normal TOML keys for simple names and quoted keys when a command name contains dots, so `some.cli` stays one provider instead of nested tables.

Provider tables can set:

| Field | Purpose |
| --- | --- |
| `command` | Command array to run instead of the provider name |
| `retry_exit_codes` | Exit codes that trigger retry on another account |
| `retry_patterns` | Lowercased stderr/stdout snippets that trigger retry |
| `never_retry_patterns` | Snippets that block retry even if another rule matches |
| `retry_on_any_error` | Retry any nonzero exit unless blocked by `never_retry_patterns` |
| `interactive_mode` | Currently `line-repl` for line-by-line wrapped shells |
| `status_command` | Command that returns JSON with `remaining`, `limit`, and optionally `used` |
| `proactive_pick` | Headroom-first starting account before the first upstream call (default `true` when `status_command` or `usage` is set) |
| `passthrough_commands` | Upstream subcommands that skip wrapper auth handling |

### Catalog list merge

Built-in catalog providers (`searchcli`, `scrapecli`, `examplecli`) ship default retry and passthrough lists in `src/clifwrap/providers.toml`. User overrides **append** by default:

```toml
[providers.searchcli]
retry_patterns = ["my custom quota message"]
```

Effective patterns include catalog defaults plus `my custom quota message`.

To replace catalog defaults entirely, use the `*_replace` sibling keys:

```toml
[providers.searchcli]
retry_patterns_replace = ["only this pattern"]
never_retry_patterns_replace = ["parse error"]
retry_exit_codes_replace = [42]
passthrough_commands_replace = ["login"]
```

Append and replace keys apply to the same list fields documented above, including providers that have no catalog entry. See `examplecli` in [provider-catalog.md](provider-catalog.md) for a full catalog template.

## Accounts

Each account is a `[[providers.<name>.accounts]]` entry.

```toml
[[providers.somecli.accounts]]
name = "team-alpha"
enabled = true
env_files = ["~/.config/secrets.env"]
env = { SOMECLI_TOKEN = "env:SOMECLI_TEAM_ALPHA" }
env_command = { SOMECLI_SESSION = ["secret-tool", "lookup", "service", "somecli", "account", "team-alpha"] }
prepare_command = ["somecli", "login", "--token", "${SOMECLI_TOKEN}"]
prepare_on = "once"
```

| Field | Purpose |
| --- | --- |
| `name` | Label you choose |
| `enabled` | Default `true`; disabled accounts are skipped |
| `env_files` | Files with shell-style `KEY=value` lines |
| `env` | Literal values or `env:OTHER_VAR` references |
| `env_command` | Commands whose stdout becomes the env value before each attempt |
| `prepare_command` | Optional command run before attempting this account |
| `prepare_on` | `always`, `once`, or `never` |

`CLIFWRAP_ACCOUNT=<name>` starts one wrapped command from a specific enabled account without editing config.

## Import accounts from a spec file

`clifwrap account import-spec <path>` shows what would change. Add `--apply` to write config.

Imports are idempotent. Existing accounts match on provider + label, then update to the current env ref, env file, and enabled state. Existing `env_command`, `prepare_command`, and `prepare_on` values are kept.

Dry-run statuses:

| Status | Meaning |
| --- | --- |
| `would-add` | Secret source found, account does not exist yet |
| `would-update` | Account exists but spec would change env ref, file, or enabled state |
| `exists` | Already matches the spec |
| `missing` | No env source found for this account |
| `invalid` | Validation configured and the candidate secret failed |

IndexCLImple spec with a template for env var names:

```toml
provider = "somecli"
target_env = "SOMECLI_TOKEN"
env_file = "~/.config/secrets.env"
env_name_template = "CLIFWRAP_{provider_slug}_{account_slug}_{target_env_slug}"

[[accounts]]
label = "team alpha"

[[accounts]]
label = "team beta"
enabled = false
```

## Auth management

Wrapper auth aliases are separate from upstream auth commands. That lets `searchcli logins` or `scrapecli accounts` manage wrapper accounts while bare `searchcli auth` or `scrapecli login` still hit the real CLI.

```toml
[providers.somecli.auth_management]
command = "login"
aliases = ["accounts", "logins"]
```

Environment overrides:

- `CLIFWRAP_PROVIDER_<NAME>_AUTH_COMMAND`
- `CLIFWRAP_PROVIDER_<NAME>_AUTH_ALIASES` — comma-separated
- `CLIFWRAP_PROVIDER_<NAME>_PASSTHROUGH_COMMANDS` — comma-separated upstream subcommands that bypass wrapper auth

## Capacity control

Capacity control runs before the upstream CLI sees the request. That stops fallback accounts from being spent below your reserve unless policy explicitly allows it.

```toml
[providers.somecli.capacity_control]
default_action = "queue"
unknown_capacity_action = "allow"
reserve_threshold = 5
default_cost = 1
command_costs = { search = 2, extract = 5 }
queue_retention_seconds = 86400
queue_max_items = 100
remediation_message = "Provision more credits or enable another account."
remediation_commands = ["clifwrap account add somecli <name> --env-ref SOMECLI_TOKEN=ENVVAR"]
```

| Field | Purpose |
| --- | --- |
| `default_action` | When every known account is below `reserve_threshold + estimated_cost`. Values: `execute`, `queue`, `shed` |
| `unknown_capacity_action` | When no account returns usage data. Values: `allow`, `queue`, `shed` |
| `reserve_threshold` | Capacity floor to preserve |
| `default_cost` | Estimated cost when the subcommand has no explicit entry in `command_costs` |
| `command_costs` | Per-subcommand cost map |
| `queue_retention_seconds` | How long queued items stay replayable |
| `queue_max_items` | Max queued items per provider before new work is shed |
| `snapshot_ttl_seconds` | Usage cache TTL for admission and proactive starting-account decisions |
| `remediation_message` | Message shown in status and queue output |
| `remediation_commands` | Suggested commands for operators |

Environment overrides:

- `CLIFWRAP_PROVIDER_<NAME>_CAPACITY_DEFAULT_ACTION`
- `CLIFWRAP_PROVIDER_<NAME>_CAPACITY_UNKNOWN_ACTION`
- `CLIFWRAP_PROVIDER_<NAME>_CAPACITY_RESERVE_THRESHOLD`
- `CLIFWRAP_PROVIDER_<NAME>_CAPACITY_DEFAULT_COST`
- `CLIFWRAP_PROVIDER_<NAME>_CAPACITY_COMMAND_COSTS` — `key=value,key=value` or TOML inline table
- `CLIFWRAP_PROVIDER_<NAME>_QUEUE_RETENTION_SECONDS`
- `CLIFWRAP_PROVIDER_<NAME>_QUEUE_MAX_ITEMS`
- `CLIFWRAP_PROVIDER_<NAME>_CAPACITY_SNAPSHOT_TTL_SECONDS`
- `CLIFWRAP_PROVIDER_<NAME>_CAPACITY_REMEDIATION_MESSAGE`
- `CLIFWRAP_PROVIDER_<NAME>_CAPACITY_REMEDIATION_COMMANDS` — comma-separated command strings

### Proactive starting account

When `proactive_pick` is enabled (the default for providers with `status_command` or `usage` metadata), clifwrap probes account capacity before the first upstream call and starts on the account with the most headroom. The persisted default is kept when its remaining quota is at or above `reserve_threshold + estimated_cost` (or `1` when capacity control is absent).

```toml
[providers.somecli]
status_command = ["somecli", "usage", "--json"]
proactive_pick = true  # default when status_command or usage is set

[providers.somecli.capacity_control]
reserve_threshold = 5
default_cost = 1
```

Set `proactive_pick = false` to keep legacy default-first ordering without headroom comparison.

When the starting account differs from the default, clifwrap prints a one-line stderr notice naming the account and reason. Reactive failover after a retryable upstream error is unchanged.

`status --json` and `doctor --json` include per-account `starting_eligible` and `starting_ineligible_reason` using the same reserve and cost rules.

Higher `snapshot_ttl_seconds` reduces probe latency but can approve a run from stale quota data. Lower TTL increases probe cost and cold-start latency.

## Usage lookups

HTTP usage lookups feed `clifwrap status` and capacity control.

```toml
[providers.somecli.usage]
url = "https://api.example.test/usage"
auth_env = "SOMECLI_TOKEN"
timeout_seconds = 15
auth_header = "Authorization"
auth_scheme = "Bearer"
content_type = "application/json"
remaining_path = "data.remaining"
limit_path = "data.limit"
used_path = "data.used"
label = "credits"
```

| Field | Purpose |
| --- | --- |
| `url` | HTTP endpoint; `{VAR:default}` env defaults work inside braces |
| `auth_env` | Account env key holding the credential |
| `timeout_seconds` | HTTP timeout (positive integer) |
| `auth_header` | Default `Authorization` |
| `auth_scheme` | Default `Bearer` |
| `content_type` | Optional `Content-Type` header |
| `used_path`, `limit_path`, `remaining_path` | Dotted JSON paths |
| `fallback_used_path`, `fallback_limit_path` | Alternate paths when primary limit data is missing |
| `label`, `fallback_label` | Labels in status output |

Environment override: `CLIFWRAP_PROVIDER_<NAME>_USAGE_TIMEOUT_SECONDS`

## Fallback monitoring

Warns or blocks when too few enabled accounts remain as fallbacks.

```toml
[providers.somecli.fallback_monitor]
threshold = 3
action = "warn"
journald = true
syslog = true
stderr = true
recovery_command = ["notify-send", "somecli fallbacks are low"]
```

`action` is `warn` or `fail`. `fail` stops wrapped commands while the pool is below threshold.

Environment overrides:

- `CLIFWRAP_PROVIDER_<NAME>_FALLBACK_THRESHOLD`
- `CLIFWRAP_PROVIDER_<NAME>_FALLBACK_ACTION`
- `CLIFWRAP_PROVIDER_<NAME>_FALLBACK_JOURNALD`
- `CLIFWRAP_PROVIDER_<NAME>_FALLBACK_SYSLOG`
- `CLIFWRAP_PROVIDER_<NAME>_FALLBACK_STDERR`
- `CLIFWRAP_PROVIDER_<NAME>_FALLBACK_RECOVERY_COMMAND` — comma-separated command parts

Recovery commands receive:

- `CLIFWRAP_PROVIDER`
- `CLIFWRAP_LOW_FALLBACK_MESSAGE`
- `CLIFWRAP_LOW_FALLBACK_ENABLED`
- `CLIFWRAP_LOW_FALLBACK_UNUSED`
- `CLIFWRAP_LOW_FALLBACK_THRESHOLD`
- `CLIFWRAP_LOW_FALLBACK_ACTIVE`
- `CLIFWRAP_LOW_FALLBACK_ENABLED_NAMES`

## Installs

`clifwrap install <provider>` is idempotent. If the target is already a managed shim with a recorded backup, another install returns the same shim.

Restore originals with:

```bash
clifwrap uninstall <provider>
```
