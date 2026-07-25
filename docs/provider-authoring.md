# Provider authoring

This guide explains how to extend clifwrap with new CLI providers without reading implementation source.

## Two paths

**Config-only provider** — Add accounts and optional overrides under `[providers.<name>]` in `~/.config/clifwrap/config.toml`. You must define retry rules, usage lookup, and capacity metadata yourself if you need failover or quota gating.

**Catalog provider** — Add a `[providers.<name>]` table to `src/clifwrap/providers.toml` in the repository (or ship a private fork). Catalog entries document retry behavior, usage URLs, auth aliases, and capacity defaults. Users normally only add `[[providers.<name>.accounts]]` entries locally.

Use `examplecli` in [provider-catalog.md](provider-catalog.md) as the reference template. It is documentation-only — do not install a shim for it.

## Required pieces

| Concern | Config-only | Catalog |
| --- | --- | --- |
| Accounts | Required in user config | Required in user config |
| Retry rules | Recommended in user config | Defaults in catalog; append or replace |
| Usage or `status_command` | Required for `status` / capacity | Recommended in catalog |
| Auth metadata | Optional | Recommended when upstream has auth subcommands |

## Validation workflow

Before installing a shim, validate configuration locally:

```bash
clifwrap config validate
clifwrap config validate --json
clifwrap doctor
clifwrap doctor --check
clifwrap doctor --probe --provider somecli
clifwrap doctor --provider somecli --all-accounts
```

`config validate` catches static issues: missing accounts, unset `env:` references, duplicate account names, and malformed metadata.

`doctor --probe` adds live probes when usage URLs or `status_command` are configured (`--all-accounts` implies it). Probes are opt-in because they resolve account credentials, run `env_command` lookups, and make authenticated requests. Probes warn by default; `--check` exits nonzero on warnings or errors (useful in CI).

Probe findings never echo command output or argv — a failing `status_command` is reported by exit status only, so tokens printed on stderr stay out of `doctor --json`.

## Common failure modes

- **Runtime failure on first wrap** — Usually a missing `env:VAR` or wrong retry patterns. Run `clifwrap config validate` first.
- **Catalog override dropped defaults** — Setting a non-empty list without `*_replace` previously replaced the whole catalog list. Append is now the default; use `retry_patterns_replace` when you intend to drop catalog defaults.
- **Usage probe warnings offline** — Expected when the usage endpoint is unreachable. Warnings do not fail `doctor` unless `--check` is set.

## Contributing a catalog provider

1. Copy the `examplecli` block in `src/clifwrap/providers.toml`.
2. Use anonymized `*.example` hosts (see `scripts/check_anonymity.py`).
3. Regenerate docs: `python scripts/generate_provider_catalog.py --write`.
4. Add integration tests in `tests/test_wrapper.py` using a generic `somecli` fixture where possible.
5. Do not add provider name literals to generic modules (`config.py`, `runtime.py`, etc.).

## Interactive agent CLI notes

Some coding-agent CLIs are full-screen TUIs. Do not use `interactive_mode = "line-repl"` for those — that mode is for line-oriented shells like SearchCLI. Catalog entries `agent` / `agentcli` use `tty-exec`:

- Interactive sessions: select account → `exec` the real binary (TTY preserved).
- `-p` / `--print` headless runs: buffered run with retry/failover across accounts.

Passthrough covers management commands (`login`, `logout`, `status`, `mcp`, …) so browser login and MCP setup stay upstream.

## Related docs

- [configuration.md](configuration.md) — field reference and merge semantics
- [provider-catalog.md](provider-catalog.md) — generated catalog reference
- [operations.md](operations.md) — day-two operations
