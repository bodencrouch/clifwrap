# Security

`clifwrap` wraps CLIs that may hold API keys, OAuth tokens, or browser-login credentials. Treat config, state files, logs, and release artifacts like you would any local secret store.

## Supported versions

Until `1.0`, only the latest release gets security fixes.

## Automated checks

The repo runs CodeQL on Python for pushes, pull requests, a weekly schedule, and manual runs. Triage findings before calling a release production-ready.

Pull requests also run dependency review and fail when a dependency change introduces a high-severity vulnerability.

Dependabot opens grouped weekly PRs for Python and GitHub Actions dependencies.

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/bodencrouch/clifwrap/security/advisories/new) or GitHub Security Advisories for [github.com/bodencrouch/clifwrap](https://github.com/bodencrouch/clifwrap).

If the repo is unavailable, contact maintainers through the same private channel you use for release coordination. Do not open a public issue with tokens, keys, or exploit steps.

## Secrets in config and logs

- Do not commit API keys, OAuth tokens, browser-login credentials, or generated env files.
- Prefer `env:` references, `env_files`, or command-backed lookups over literal values in config.
- `clifwrap account list --json`, `clifwrap doctor --json`, and release verification are written not to print secret values.
- Upstream CLIs may still print their own diagnostics — review logs before sharing them.

## Local state

By default:

```text
~/.config/clifwrap/config.toml
~/.local/state/clifwrap/
```

The state directory can hold default-account choices, queue metadata, usage cache, recovery-hook errors, and backups of original executables. Lock it down like any other local credential store.
