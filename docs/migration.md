# Migration from cli-fallback-wrapper

The project was renamed to `clifwrap`. Package name, CLI command, config paths, state paths, and env var prefix all changed.

## Name map

| Old | New |
| --- | --- |
| `cli-fallback-wrapper` | `clifwrap` |
| Python package `cli_fallback_wrapper` | `clifwrap` |
| CLI command `clifw` | `clifwrap` |
| `~/.config/cli-fallback-wrapper` | `~/.config/clifwrap` |
| `~/.local/state/cli-fallback-wrapper` | `~/.local/state/clifwrap` |
| `CLIFW_*` | `CLIFWRAP_*` |

There is no legacy command alias. That avoids confusion in shell shims and release binaries.

## Steps

```bash
mkdir -p ~/.config/clifwrap ~/.local/state/clifwrap
cp -a ~/.config/cli-fallback-wrapper/config.toml ~/.config/clifwrap/config.toml
cp -a ~/.local/state/cli-fallback-wrapper/. ~/.local/state/clifwrap/
clifwrap install
```

Then rename any exported `CLIFW_*` variables to `CLIFWRAP_*`.
