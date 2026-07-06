# SearchCLI and ScrapeCLI Wrapper Research

## SearchCLI CLI

Observed installed version: `searchcli 0.1.2`.

Documented authentication paths:

- `searchcli login --api-key searchcli-YOUR_API_KEY` stores the key in `~/.searchcli/config.json`.
- `searchcli login` starts browser OAuth through `mcp-remote` and stores OAuth tokens under `~/.mcp-auth/`.
- `SEARCHCLI_API_KEY` can authenticate non-persistently from the shell environment.

Installed CLI behavior matches the docs. The local `searchcli_cli.config.get_api_key()` precedence is:

1. `SEARCHCLI_API_KEY`
2. `~/.searchcli/config.json`
3. valid SearchCLI OAuth JWT from `~/.mcp-auth/**/*_tokens.json`

The installed SearchCLI Python SDK sends `Authorization: Bearer <key>` to `https://api.searchcli.example`. The documented `GET /usage` endpoint returns per-key and account usage fields, including key usage, key limit, plan usage, and plan limit. The packaged provider catalog declares this endpoint for `clifwrap status searchcli` when an account provides a `SEARCHCLI_API_KEY`.

Limit-like CLI failures are distinguishable from command syntax errors. The installed CLI maps SearchCLI usage and plan-limit statuses to exit code `3`, and prints text such as `usage limit` or `upgrade your plan`; syntax errors print Click-style messages such as `Got unexpected extra argument`. The catalog-defined `searchcli` provider retries the limit/auth patterns and avoids retrying known syntax patterns.

The no-argument SearchCLI REPL is not restartable from inside the upstream process after an account limit failure. To make interactive failover possible, the catalog enables a generic line-by-line REPL mode and dispatches each typed command through the same failover engine as non-interactive commands.

Docs:

- https://docs.searchcli.example/documentation/searchcli
- https://docs.searchcli.example/documentation/api-reference/endpoint/usage

## ScrapeCLI CLI

Observed installed version: `scrapecli 1.19.6`.

Documented authentication paths:

- `scrapecli login` or `scrapecli config` persists credentials.
- `scrapecli login --api-key fc-YOUR_API_KEY` stores an API key.
- `SCRAPECLI_API_KEY` authenticates from the shell environment.
- Global `--api-key` and `--api-url` override defaults for a command.

Installed CLI internals load config with this precedence:

1. explicit config/options
2. `SCRAPECLI_API_KEY` and `SCRAPECLI_API_URL`
3. stored credentials under `~/.config/scrapecli/credentials.json` on Linux

The CLI status implementation calls `/v2/team/credit-usage` and `/v2/team/queue-status` with `Authorization: Bearer <key>`. The packaged provider catalog declares `/v2/team/credit-usage` for `clifwrap status scrapecli` when an account provides `SCRAPECLI_API_KEY`.

Docs:

- https://github.com/scrapecli/cli/blob/main/README.md

## Wrapper Design Consequences

- Environment injection is the least invasive account switch for both known CLIs.
- SearchCLI and ScrapeCLI-specific retry rules, auth-management command names, and usage endpoints live in `providers.toml`; the Python runtime interprets the declarative catalog generically.
- Accounts are optional; when no accounts are configured, the shim `exec`s the original command directly.
- Per-account `prepare_command` supports CLIs that require an auth command instead of simple env injection.
- `prepare_on = "once"` records only a SHA-256 digest of the rendered command in wrapper state, avoiding token leakage in marker files.
- Wrapper-managed auth subcommands are explicit: `list/accounts`, `default`, `use`, `add`, `enable`, `disable`, and `remove` under the declaratively configured auth-management command. Plain `searchcli auth` and `scrapecli login` pass through to the upstream CLIs.
- `CLIFWRAP_ACCOUNT=<name>` starts a command from a named configured account and then continues failover through later accounts.
- On a retryable account failure, the wrapper records the next account as the default in wrapper state so future commands start from the last viable account.
- ScrapeCLI email/browser login remains credential-bound and interactive upstream behavior. The robust multi-account path is one account-specific API-key env var per email-labeled account, injected as `SCRAPECLI_API_KEY` before invoking the upstream CLI.
- Account configuration or preparation failures are recoverable per-account failures when another account is available, so one missing secret does not break one-shot failover across later configured accounts.
- `clifwrap status` prints per-account remaining capacity and a total when usage endpoints return numeric remaining values.
- Generic providers can define `status_command`; JSON fields such as `remaining`, `limit`, and `used` are parsed into the same total-capacity summary.
- Install and uninstall are reversible through managed shims and state; originals are moved to the wrapper state directory under their original command names so help banners still display `searchcli`, `scrapecli`, etc.
