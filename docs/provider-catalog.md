# Built-In Provider Catalog

This file is generated from `src/clifwrap/providers.toml`.
Run `python scripts/generate_provider_catalog.py --write` after changing built-in provider metadata.

## `querycli`

| Field | Value |
| --- | --- |
| `retry_patterns` | `rate limit`, `too many requests`, `invalid api key`, `unauthorized`, `401`, `429` |
| `never_retry_patterns` | `network error`, `invalid request`, `422` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `3` |
| `action` | `warn` |
| `journald` | true |
| `syslog` | true |
| `stderr` | true |

### Capacity Control

| Field | Value |
| --- | --- |
| `default_action` | `execute` |
| `unknown_capacity_action` | `allow` |
| `reserve_threshold` | `0` |
| `default_cost` | `1` |
| `queue_retention_seconds` | `86400` |
| `queue_max_items` | `100` |
| `snapshot_ttl_seconds` | `60` |
| `remediation_message` | `Provision another QueryCLI API key or enable another configured account.` |
| `remediation_commands` | `clifwrap account list querycli`, `clifwrap account add querycli <name> --env-ref QUERYCLI_API_KEY=ENVVAR` |

## `indexcli`

| Field | Value |
| --- | --- |
| `passthrough_commands` | `api-key`, `config` |
| `retry_patterns` | `rate limit`, `too many requests`, `no more credits`, `payment required`, `budget exceeded`, `invalid api key`, `unauthorized`, `401`, `402`, `403`, `429` |
| `never_retry_patterns` | `unknown option`, `missing required argument`, `invalid choice`, `must contain` |

### Auth Management

| Field | Value |
| --- | --- |
| `command` | `api-key` |
| `aliases` | `accounts` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `3` |
| `action` | `warn` |
| `journald` | true |
| `syslog` | true |
| `stderr` | true |

### Capacity Control

| Field | Value |
| --- | --- |
| `default_action` | `execute` |
| `unknown_capacity_action` | `allow` |
| `reserve_threshold` | `0` |
| `default_cost` | `1` |
| `queue_retention_seconds` | `86400` |
| `queue_max_items` | `100` |
| `snapshot_ttl_seconds` | `60` |
| `remediation_message` | `Provision another IndexCLI API key or enable another configured account.` |
| `remediation_commands` | `clifwrap account list indexcli`, `clifwrap account add indexcli <name> --env-ref INDEXCLI_API_KEY=ENVVAR` |

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
| `reserve_threshold` | `5` |
| `default_cost` | `1` |
| `queue_retention_seconds` | `86400` |
| `queue_max_items` | `100` |
| `snapshot_ttl_seconds` | `60` |
| `command_costs` | `crawl=10`, `extract=5`, `map=2`, `scrape=1`, `search=2` |
| `remediation_message` | `Provision additional ScrapeCLI credits or enable another configured account before replaying queued work.` |
| `remediation_commands` | `clifwrap account list scrapecli`, `clifwrap account add scrapecli <name> --env-ref SCRAPECLI_API_KEY=ENVVAR` |

## `jina`

| Field | Value |
| --- | --- |
| `retry_patterns` | `rate limit`, `too many requests`, `429`, `invalid or expired api key`, `authentication`, `unauthorized`, `401`, `403`, `quota` |
| `never_retry_patterns` | `unknown command`, `no such option`, `missing argument`, `invalid value` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `3` |
| `action` | `warn` |
| `journald` | true |
| `syslog` | true |
| `stderr` | true |

### Capacity Control

| Field | Value |
| --- | --- |
| `default_action` | `execute` |
| `unknown_capacity_action` | `allow` |
| `reserve_threshold` | `0` |
| `default_cost` | `1` |
| `queue_retention_seconds` | `86400` |
| `queue_max_items` | `100` |
| `snapshot_ttl_seconds` | `60` |
| `remediation_message` | `Provision another EmbedCLI API key or enable another configured account.` |
| `remediation_commands` | `clifwrap account list jina`, `clifwrap account add jina <name> --env-ref EMBEDCLI_API_KEY=ENVVAR` |

## `askcli`

| Field | Value |
| --- | --- |
| `passthrough_commands` | `set-key`, `clear-key`, `view-key`, `history`, `models` |
| `retry_patterns` | `rate limit`, `too many requests`, `429`, `invalid api key`, `401`, `authentication`, `quota`, `insufficient` |
| `never_retry_patterns` | `unknown command`, `unknown option`, `missing required argument` |

### Auth Management

| Field | Value |
| --- | --- |
| `command` | `set-key` |
| `aliases` | `accounts` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `3` |
| `action` | `warn` |
| `journald` | true |
| `syslog` | true |
| `stderr` | true |

### Capacity Control

| Field | Value |
| --- | --- |
| `default_action` | `execute` |
| `unknown_capacity_action` | `allow` |
| `reserve_threshold` | `0` |
| `default_cost` | `1` |
| `queue_retention_seconds` | `86400` |
| `queue_max_items` | `100` |
| `snapshot_ttl_seconds` | `60` |
| `remediation_message` | `Provision another AskCLI API key or enable another configured account.` |
| `remediation_commands` | `clifwrap account list askcli`, `clifwrap account add askcli <name> --env-ref ASKCLI_API_KEY=ENVVAR` |

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
| `reserve_threshold` | `5` |
| `default_cost` | `1` |
| `queue_retention_seconds` | `86400` |
| `queue_max_items` | `100` |
| `snapshot_ttl_seconds` | `60` |
| `command_costs` | `crawl=5`, `extract=1`, `map=1`, `research=15`, `search=1` |
| `remediation_message` | `Provision another SearchCLI key or enable another configured account before replaying queued work.` |
| `remediation_commands` | `clifwrap account list searchcli`, `clifwrap account add searchcli <name> --env-ref SEARCHCLI_API_KEY=ENVVAR` |
