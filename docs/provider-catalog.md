# Built-In Provider Catalog

This file is generated from `src/clifwrap/providers.toml`.
Run `python scripts/generate_provider_catalog.py --write` after changing built-in provider metadata.

## `scrapecli`

| Field | Value |
| --- | --- |
| `passthrough_commands` | `login`, `logout` |
| `retry_patterns` | `rate limit`, `too many requests`, `quota`, `remaining credits`, `insufficient credits`, `api key is required`, `not authenticated`, `unauthorized`, `forbidden` |
| `never_retry_patterns` | `unknown option`, `missing required argument`, `invalid status` |

### Auth Management

| Field | Value |
| --- | --- |
| `command` | `login` |
| `aliases` | `accounts` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `3` |
| `action` | `warn` |
| `journald` | true |
| `syslog` | true |
| `stderr` | true |

### Usage

| Field | Value |
| --- | --- |
| `url` | `{SCRAPECLI_API_URL:https://api.scrapecli.example}/v2/team/credit-usage` |
| `auth_env` | `SCRAPECLI_API_KEY` |
| `timeout_seconds` | `15` |
| `auth_header` | `Authorization` |
| `auth_scheme` | `Bearer` |
| `content_type` | `application/json` |
| `remaining_path` | `data.remainingCredits` |
| `limit_path` | `data.planCredits` |
| `label` | `credits` |

### Capacity Control

| Field | Value |
| --- | --- |
| `default_action` | `queue` |
| `unknown_capacity_action` | `allow` |
| `reserve_threshold` | `25` |
| `default_cost` | `5` |
| `queue_retention_seconds` | `86400` |
| `queue_max_items` | `100` |
| `snapshot_ttl_seconds` | `60` |
| `command_costs` | `crawl=25`, `extract=10`, `map=10`, `scrape=5`, `search=5` |
| `remediation_message` | `Provision additional ScrapeCLI credits or enable another configured account before replaying queued work.` |
| `remediation_commands` | `clifwrap account list scrapecli`, `clifwrap account add scrapecli <name> --env-ref SCRAPECLI_API_KEY=ENVVAR` |

## `searchcli`

| Field | Value |
| --- | --- |
| `interactive_mode` | `line-repl` |
| `retry_exit_codes` | `3` |
| `retry_patterns` | `usage limit`, `upgrade your plan`, `rate limit`, `too many requests`, `429`, `432`, `not authenticated`, `no searchcli api key found`, `authentication timed out` |
| `never_retry_patterns` | `got unexpected extra argument`, `missing argument`, `no such command`, `invalid value`, `parse error` |

### Auth Management

| Field | Value |
| --- | --- |
| `command` | `auth` |
| `aliases` | `accounts`, `logins`, `credentials` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `3` |
| `action` | `warn` |
| `journald` | true |
| `syslog` | true |
| `stderr` | true |

### Usage

| Field | Value |
| --- | --- |
| `url` | `https://api.searchcli.example/usage` |
| `auth_env` | `SEARCHCLI_API_KEY` |
| `timeout_seconds` | `15` |
| `auth_header` | `Authorization` |
| `auth_scheme` | `Bearer` |
| `used_path` | `key.usage` |
| `limit_path` | `key.limit` |
| `fallback_used_path` | `account.plan_usage` |
| `fallback_limit_path` | `account.plan_limit` |
| `label` | `key` |
| `fallback_label` | `plan` |

### Capacity Control

| Field | Value |
| --- | --- |
| `default_action` | `queue` |
| `unknown_capacity_action` | `allow` |
| `reserve_threshold` | `25` |
| `default_cost` | `25` |
| `queue_retention_seconds` | `86400` |
| `queue_max_items` | `100` |
| `snapshot_ttl_seconds` | `60` |
| `command_costs` | `crawl=100`, `extract=50`, `map=100`, `search=25` |
| `remediation_message` | `Provision another SearchCLI key or enable another configured account before replaying queued work.` |
| `remediation_commands` | `clifwrap account list searchcli`, `clifwrap account add searchcli <name> --env-ref SEARCHCLI_API_KEY=ENVVAR` |
