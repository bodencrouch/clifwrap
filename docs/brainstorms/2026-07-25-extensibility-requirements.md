---
date: 2026-07-25
topic: extensibility
---

## Summary

Make adding and customizing CLI providers in clifwrap safe, predictable, and self-documenting. Ship tiered provider validation, fix catalog override semantics for list fields, and publish a provider authoring guide with a minimal template catalog entry.

---

## Problem Frame

clifwrap already supports declarative providers through `src/clifwrap/providers.toml` and user `config.toml` overrides, but extensibility breaks down in practice. Operators discover misconfiguration only when a wrapped command fails at runtime. List fields such as retry patterns use all-or-nothing merge semantics, so a partial override silently replaces the entire catalog list. Only `searchcli` and `scrapecli` exist as built-in examples, and there is no dedicated guide for authoring a new provider.

The user prioritized extensibility over reliability, security, agent automation, and public-adoption polish for this track. Research against tools like GitHub CLI, teamclaude, AWS credential chains, and the CLI Spec surfaced validation and merge semantics as the highest-leverage gaps without introducing a plugin framework yet.

---

## Key Decisions

- **Validation before runtime, not a plugin system.** Extend existing `config validate` and `doctor` surfaces rather than building pip-based provider discovery or Python hooks in v1 of this track.
- **Warn by default; fail on explicit check.** Offline and air-gapped setups should get warnings for unreachable usage probes. `--check` (and CI-style usage) exits nonzero on validation failures, matching existing `doctor --check` behavior.
- **Template provider, not a third production provider.** Add a minimal catalog entry whose purpose is documentation-by-example, not shipping another real upstream CLI.
- **Append-aware list merge for catalog overrides.** User config must be able to extend catalog list fields without replacing them wholesale unless the user explicitly opts into replace semantics.

---

## Requirements

**Provider validation**

- R1. `clifwrap config validate` reports provider-level issues beyond TOML parsing: missing accounts, unresolvable env refs, invalid merge declarations, and malformed provider metadata.
- R2. `clifwrap doctor` includes a provider validation section that summarizes per-provider health and links each issue to a remediation command.
- R3. A provider probe mode validates live behavior without mutating config: usage URL or `status_command` returns expected JSON fields (`remaining`, `limit`, optionally `used`), and retry rule entries are syntactically valid.
- R4. Validation messages name the provider, the config location, and the next command to fix the issue.
- R5. Without `--check`, unreachable usage endpoints produce warnings. With `--check`, they produce errors and a nonzero exit code.

**Config merge semantics**

- R6. List fields inherited from the catalog (retry patterns, passthrough commands, and similar) support append-by-default when the user supplies entries in `config.toml`.
- R7. Users can opt into full replacement for a list field when they intend to drop catalog defaults entirely.
- R8. Merge rules for list fields are documented in `docs/configuration.md` with before/after examples.

**Authoring and discovery**

- R9. A provider authoring guide explains how to add a catalog provider vs a config-only generic provider, required fields, and common failure modes.
- R10. A minimal template catalog provider demonstrates every optional field with safe defaults and example placeholder URLs.
- R11. Generated `docs/provider-catalog.md` includes the template provider so operators can discover it from published docs.

---

## Key Flows

- F1. Author validates a new provider before first use
  - **Trigger:** Operator adds accounts and overrides for a provider in `config.toml`.
  - **Actors:** Operator, clifwrap CLI
  - **Steps:** Run `config validate` → fix static issues → run `doctor --check` → run provider probe → install shim and test wrapped command.
  - **Outcome:** First real upstream invocation succeeds or fails for upstream reasons, not local misconfiguration.
  - **Covered by:** R1, R2, R3, R4, R5

- F2. Operator extends catalog retry rules without losing defaults
  - **Trigger:** Operator adds one custom retry pattern for a built-in provider.
  - **Actors:** Operator
  - **Steps:** Add pattern in user config → validate → confirm merged provider includes catalog defaults plus the new pattern.
  - **Outcome:** Failover behavior extends rather than resets.
  - **Covered by:** R6, R7, R8

---

## Acceptance Examples

- AE1. Missing env ref
  - **Covers:** R1, R4
  - **Given:** An account references `env:MISSING_VAR` that is unset and has no `env_command`.
  - **When:** The operator runs `clifwrap config validate`.
  - **Then:** Output names the provider and account and suggests setting the variable or adding `env_command`.

- AE2. Offline validation
  - **Covers:** R5
  - **Given:** Usage URL is unreachable and the operator runs `doctor` without `--check`.
  - **When:** Static validation passes but live probe fails.
  - **Then:** Exit code is 0 with a warning; with `--check`, exit code is nonzero.

- AE3. Partial retry pattern override
  - **Covers:** R6, R7
  - **Given:** Catalog defines retry patterns A and B; user adds pattern C without a replace directive.
  - **When:** Config is loaded and merged.
  - **Then:** Effective patterns are A, B, and C. With explicit replace, effective patterns are only what the user specified.

---

## Success Criteria

- A new provider can be configured and validated locally before the first wrapped invocation.
- Operators can extend catalog list defaults without reading merge implementation source.
- `docs/provider-authoring.md` is sufficient for a contributor to propose a catalog entry in a PR without ad-hoc guidance.

---

## Scope Boundaries

**Deferred for later**

- Python plugin or pip-discovered provider packages
- External provider fragments in `~/.config/clifwrap/providers.d/` (may follow if template + validation prove insufficient)
- Proactive quota gating, 429-vs-quota failover distinction, and switch audit JSONL (reliability track)
- keyring-first credential storage (security track)
- Full agent-native CLI surface (`schema` command, `--json` on every data command) (automation track)
- Windows shim install strategy (platform track)

**Outside this product's identity**

- Local HTTP proxy architecture (CliRelay-style) — clifwrap remains a process shim, not a proxy server
- Web management dashboard for accounts

---

## Dependencies / Assumptions

- Existing catalog in `src/clifwrap/providers.toml` and merge logic in `src/clifwrap/config.py` remain the extension mechanism.
- `doctor` and `config validate` already exist and are the right UX anchors; this track extends them rather than introducing parallel commands.
- Template provider uses anonymized placeholder hosts consistent with `scripts/check_anonymity.py` constraints.
- Operators may run validation offline; live probes must not be mandatory for basic config edits.

---

## Outstanding Questions

**Deferred to planning**

- Exact syntax for list replace vs append (dedicated table key, operator prefix, or nested object).
- Whether provider probe runs one account or all enabled accounts by default.
- Whether template catalog provider ships enabled in the built-in catalog or is documented as a copy-paste starting point only.

---

## Sources / Research

- Repo: `src/clifwrap/config.py` (`merged_provider` list merge behavior), `src/clifwrap/__main__.py` (`config validate`, `doctor`), `docs/configuration.md`
- External: [CLI Spec](https://clispec.dev/) (schema, dry-run, scriptable exits), GitHub CLI `auth status` pattern, teamclaude quota-vs-rate-limit distinction, AWS credential precedence chain
- Prior exploration: improvement research covered reliability, security, and agent-native CLI as separate deferred tracks
