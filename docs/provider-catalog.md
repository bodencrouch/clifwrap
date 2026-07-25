# Built-In Provider Catalog

This file is generated from `src/clifwrap/providers.toml`.
Run `python scripts/generate_provider_catalog.py --write` after changing built-in provider metadata.

## `agent`

| Field | Value |
| --- | --- |
| `interactive_mode` | `tty-exec` |
| `passthrough_commands` | `login`, `logout`, `status`, `whoami`, `about`, `models`, `update`, `mcp`, `plugin`, `worker`, `ls`, `resume`, `create-chat`, `generate-rule`, `rule`, `install-shell-integration`, `uninstall-shell-integration`, `help` |
| `retry_patterns` | `rate limit`, `too many requests`, `429`, `usage limit`, `out of usage`, `spend limit`, `quota`, `not authenticated`, `unauthorized`, `authentication required`, `invalid api key`, `resource_exhausted` |
| `never_retry_patterns` | `unknown option`, `unknown command`, `missing required argument`, `invalid argument` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `2` |
| `action` | `warn` |
| `journald` | false |
| `syslog` | true |
| `stderr` | true |

## `agentcli`

| Field | Value |
| --- | --- |
| `interactive_mode` | `tty-exec` |
| `passthrough_commands` | `login`, `logout`, `status`, `whoami`, `about`, `models`, `update`, `mcp`, `plugin`, `worker`, `ls`, `resume`, `create-chat`, `generate-rule`, `rule`, `install-shell-integration`, `uninstall-shell-integration`, `help` |
| `retry_patterns` | `rate limit`, `too many requests`, `429`, `usage limit`, `out of usage`, `spend limit`, `quota`, `not authenticated`, `unauthorized`, `authentication required`, `invalid api key`, `resource_exhausted` |
| `never_retry_patterns` | `unknown option`, `unknown command`, `missing required argument`, `invalid argument` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `2` |
| `action` | `warn` |
| `journald` | false |
| `syslog` | true |
| `stderr` | true |

## `examplecli`

| Field | Value |
| --- | --- |
| `interactive_mode` | `line-repl` |
| `passthrough_commands` | `login` |
| `retry_exit_codes` | `1` |
| `retry_patterns` | `quota exceeded`, `rate limit` |
| `never_retry_patterns` | `unknown option` |

### Auth Management

| Field | Value |
| --- | --- |
| `command` | `auth` |
| `aliases` | `accounts`, `credentials` |

### Fallback Monitor

| Field | Value |
| --- | --- |
| `threshold` | `2` |
| `action` | `warn` |
| `journald` | false |
| `syslog` | true |
| `stderr` | true |

### Usage

| Field | Value |
| --- | --- |
| `url` | `https://api.examplecli.example/usage` |
| `auth_env` | `EXAMPLECLI_API_KEY` |
| `timeout_seconds` | `10` |
| `remaining_path` | `remaining` |
| `limit_path` | `limit` |
| `label` | `quota` |

### Capacity Control

| Field | Value |
| --- | --- |
| `default_action` | `queue` |
| `unknown_capacity_action` | `allow` |
| `reserve_threshold` | `1` |
| `default_cost` | `1` |
| `command_costs` | `crawl=3`, `search=1` |
| `remediation_message` | `Add another account or raise quota before replaying queued work.` |
| `remediation_commands` | `clifwrap account list examplecli`, `clifwrap config validate` |

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
