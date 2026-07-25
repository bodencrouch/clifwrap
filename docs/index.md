# clifwrap

`clifwrap` wraps account-backed CLIs — the ones where quota, rate limits, and credentials get in the way. It installs reversible shims, reads account config from TOML, checks capacity before requests when you enable that, and fails over to the next account when policy allows.

## Quick start

```bash
pipx install clifwrap
clifwrap init
clifwrap account add searchcli primary --env-file ~/.config/secrets.env --env-ref SEARCHCLI_API_KEY=SEARCHCLI_API_KEY
clifwrap install searchcli
```

## Documentation

- [Configuration](configuration.md)
- [CLI reference](cli-reference.md)
- [Built-in provider catalog](provider-catalog.md)
- [Migration from cli-fallback-wrapper](migration.md)
- [Operations runbook](operations.md)
- [Release process](release.md)
- [Research notes](RESEARCH.md)

CI publishes pytest reports, JUnit XML, release summaries, and rendered docs to GitHub Pages.
