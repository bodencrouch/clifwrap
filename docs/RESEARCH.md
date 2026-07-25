# SearchCLI and ScrapeCLI research

Notes from testing the upstream CLIs before building wrapper support.

## SearchCLI CLI

Tested version: `searchcli 0.1.2`.

### Auth paths (documented)

- `searchcli login --api-key searchcli-YOUR_API_KEY` → `~/.searchcli/config.json`
- `searchcli login` → browser OAuth via `mcp-remote` → tokens under `~/.mcp-auth/`
- `SEARCHCLI_API_KEY` in the shell (not persisted)

### What the installed CLI actually does

Local `searchcli_cli.config.get_api_key()` precedence:

1. `SEARCHCLI_API_KEY`
2. `~/.searchcli/config.json`
3. Valid SearchCLI OAuth JWT from `~/.mcp-auth/**/*_tokens.json`

The Python SDK sends `Authorization: Bearer <key>` to `https://api.searchcli.example`. `GET /usage` returns per-key and account usage (key usage/limit, plan usage/limit). The packaged catalog uses this endpoint for `clifwrap status searchcli` when an account provides `SEARCHCLI_API_KEY`.

Limit failures are distinct from syntax errors. The CLI maps usage/plan-limit statuses to exit code `3` with messages like `usage limit` or `upgrade your plan`. Syntax errors use Click-style text like `Got unexpected extra argument`. The catalog retries limit/auth patterns and skips known syntax patterns.

The no-argument SearchCLI REPL cannot restart after an account limit failure inside the upstream process. The catalog enables `line-repl` mode so each typed line goes through the same failover engine as non-interactive commands.

Docs:

- https://docs.searchcli.example/documentation/searchcli
- https://docs.searchcli.example/documentation/api-reference/endpoint/usage

## ScrapeCLI CLI

Tested version: `scrapecli 1.19.6`.

### Auth paths (documented)

- `scrapecli login` or `scrapecli config` persists credentials
- `scrapecli login --api-key fc-YOUR_API_KEY` stores an API key
- `SCRAPECLI_API_KEY` in the shell
- Global `--api-key` and `--api-url` override defaults per command

### What the installed CLI actually does

Config load precedence:

1. Explicit config/options
2. `SCRAPECLI_API_KEY` and `SCRAPECLI_API_URL`
3. Stored credentials at `~/.config/scrapecli/credentials.json` (Linux)

Status calls `/v2/team/credit-usage` and `/v2/team/queue-status` with `Authorization: Bearer <key>`. The catalog uses `/v2/team/credit-usage` for `clifwrap status scrapecli` when an account provides `SCRAPECLI_API_KEY`.

Docs:

- https://github.com/scrapecli/cli/blob/main/README.md

## What we built from this

- Env injection is the least invasive way to switch accounts for both CLIs.
- Retry rules, auth command names, and usage endpoints live in `providers.toml`; Python interprets the catalog generically.
- With no accounts configured, the shim `exec`s the original command.
- `prepare_command` handles CLIs that need a login step instead of plain env injection.
- `prepare_on = "once"` stores only a SHA-256 digest of the rendered command in state — no tokens in marker files.
- Wrapper auth subcommands (`list`, `default`, `use`, `add`, `enable`, `disable`, `remove`) sit under the configured auth command. Plain `searchcli auth` and `scrapecli login` pass through.
- `CLIFWRAP_ACCOUNT=<name>` starts from a named account, then continues failover through later accounts.
- On retryable failure, the wrapper saves the next working account as default for future commands.
- ScrapeCLI browser login is interactive and stores one active credential. Multi-account failover needs one API-key source per account, injected as `SCRAPECLI_API_KEY` before calling upstream.
- Account config or prepare failures on one account do not block failover to later accounts.
- `clifwrap status` prints per-account remaining capacity and a total when usage endpoints return numbers.
- Generic providers can define `status_command`; JSON fields `remaining`, `limit`, and `used` feed the same total-capacity summary.
- Install/uninstall is reversible: originals move to the wrapper state directory under their command names so help banners still say `searchcli`, `scrapecli`, etc.
