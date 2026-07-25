# Operations

Day-to-day checks and recovery for `clifwrap` installs.

## Health checks

Run these before and after account or policy changes:

```bash
clifwrap config paths
clifwrap config validate
clifwrap doctor --check
clifwrap doctor --json --check
clifwrap doctor --probe --check
clifwrap status --check
clifwrap status --json --check
```

| Command | What it checks |
| --- | --- |
| `config paths` | Resolved `CLIFWRAP_CONFIG`, `CLIFWRAP_STATE_DIR`, and `CLIFWRAP_BIN_DIR` |
| `config validate` | Parsed config, provider static validation (accounts, env refs, metadata) |
| `doctor --check` | Above plus shim records, backups, default accounts, queue readability |
| `doctor --probe` | Adds live usage/status probes. Off by default because probes resolve credentials and make authenticated calls |
| `status --check` | Low fallback pool, bad queue state, recovery-hook failures, capacity below policy |

## Account inventory

List accounts through wrapper commands, not upstream login state:

```bash
clifwrap account list
clifwrap account list --json
searchcli logins
scrapecli accounts
```

Use labels that describe ownership or purpose. Bind secrets through env files, env refs, or command lookups — not through label names.

The JSON output is safe for automation logs: labels and key names only, no secret values.

## Queue

When capacity is low and policy is `queue`, work is stored under the wrapper state directory:

```bash
clifwrap queue list --json
clifwrap queue run
clifwrap queue drop --expired
```

`queue run` rechecks capacity before replay. If still below reserve, the item stays queued and replay metadata updates — nothing is duplicated.

## Proactive starting account

When `proactive_pick` is enabled (default for providers with usage or `status_command` metadata), wrapped commands start on the account with the most known headroom instead of always trying the persisted default first. This reduces wasted retries when the default is nearly empty.

- Tune `snapshot_ttl_seconds` against probe cost: stale snapshots may start on an account that fails immediately; lower TTL is fresher but slower on cold paths.
- `status --json` exposes `starting_eligible` per account for automation.
- Set `proactive_pick = false` per provider to restore default-first behavior.

## Shim recovery

Install is idempotent:

```bash
clifwrap install searchcli scrapecli
```

Uninstall fails if the target is not a managed shim or the backup is missing:

```bash
clifwrap uninstall searchcli scrapecli
```

If someone replaced an upstream binary by hand, check `CLIFWRAP_BIN_DIR` and the state directory before touching files. Restore the original executable first, then run `clifwrap install` again.

Run `clifwrap doctor --json --check` before and after recovery to confirm target, backup, and shim marker from the wrapper's own records.

## Release verification

Before cutting or publishing a release:

```bash
python -m pip install -e ".[dev,release]"
python scripts/verify_release.py --require-actionlint
```

The verifier checks workflow syntax, GitHub Actions linting, Ruff, pytest, compileall, package archives, wheel install smoke, Pages generation, and a PyInstaller binary smoke test. Generated artifacts are removed unless you pass `--keep-artifacts`.

Pass `--summary-json release-summary.json` when CI or a handoff needs a compact proof record after validation succeeds.
