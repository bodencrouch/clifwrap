# Contributing

Thanks for helping. `clifwrap` sits in front of real CLIs and real credentials, so changes here need a light touch.

## Before you open a PR

Run the same checks CI runs:

```bash
python -m pip install -e ".[dev]"
python scripts/verify_release.py --skip-pyinstaller
```

Or use Nox:

```bash
python -m pip install -e ".[dev]"
nox
nox -s release-verify -- --require-actionlint
```

If you have [actionlint](https://github.com/rhysd/actionlint) installed, `verify_release.py` runs it automatically. Pass `--require-actionlint` when you want the script to fail without it.

For a local PyInstaller smoke test:

```bash
python -m pip install -e ".[release]"
python scripts/verify_release.py
```

## Design expectations

- Put provider-specific behavior in `providers.toml` or user config, not in generic Python branches.
- `clifwrap install` must be idempotent — never wrap an existing managed shim twice.
- `clifwrap uninstall` must fail safely when the backup is missing or the target is not a managed shim.
- With no accounts or policies configured, commands pass through unchanged.
- Never log secret values.
- Add regression tests for stdin handling, retry logic, queue behavior, and auth subcommands before changing execution flow.

## Releases

See [docs/release.md](docs/release.md). Manual GitHub releases stay marked prerelease until validation workflows finish and artifacts upload.
