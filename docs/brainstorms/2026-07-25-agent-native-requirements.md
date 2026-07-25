---
date: 2026-07-25
topic: agent-native
---

## Summary

Give clifwrap a shared agent-native contract so coding agents and CI can drive it without guessing flags or parsing ad-hoc JSON. Unify existing `--json` output under one envelope, document stable exit codes, and add `--dry-run` on mutating clifwrap commands.

---

## Problem Frame

clifwrap already exposes `--json` on several operational commands (`doctor`, `status`, `config validate`, `account list`, queue commands), but each command returns a different top-level shape. Exit codes are meaningful in practice (`--check` fails on issues) yet undocumented as a taxonomy agents can rely on. Mutating commands (`install`, `uninstall`, `account add`, queue replay) have no machine-readable output and no dry-run path, so agents and CI must either scrape human text or execute side effects to learn what would happen.

The extensibility track improves provider validation and authoring; it deliberately deferred a full agent-native surface. This track closes that gap for the commands operators and automation already use daily.

---

## Key Decisions

- **Contract plus dry-run, not full spec compliance.** Ship a unified JSON envelope, documented exit codes, and dry-run on mutating clifwrap commands. Defer machine-readable schema discovery and ai-native-cli-spec coverage across every command.
- **Same contract for agents and CI.** One envelope and exit-code table serves interactive agent sessions and pipeline scripts; no separate "CI mode."
- **Wrap, don't redesign.** Existing per-command payloads move under a `data` field inside the envelope rather than redesigning each command's internal structure.
- **Additive migration for envelope.** When `--json` is used, nest the current payload under `data` and add envelope fields alongside. Human (non-JSON) output stays unchanged. Breaking top-level JSON keys ship only with a documented migration note in the release changelog.
- **Dry-run applies to clifwrap-owned mutations only.** Install, uninstall, account mutations, and queue mutations support dry-run. Wrapped upstream CLIs are out of scope.

---

## Requirements

**JSON envelope**

- R1. Every command that supports `--json` emits a top-level envelope with at least: success indicator, command identity, and a `data` field holding the command's payload.
- R2. On failure, the envelope includes a structured error object with a stable machine-readable code and a human-readable message. Secret values never appear in JSON output.
- R3. Envelope fields are consistent across commands so a single parser can handle doctor, status, validate, account list, and queue output.

**Exit codes**

- R4. clifwrap documents a small stable exit-code taxonomy (success, usage/argument error, config error, operational check failure, internal error) mapped to real command behavior.
- R5. `--check` on doctor and status continues to exit nonzero on check failures; the taxonomy explains which code applies.
- R6. JSON error responses and process exit codes align: an agent reading only stdout can determine outcome; an agent reading only exit code can branch without parsing JSON.

**Dry-run**

- R7. `install`, `uninstall`, `account add`, `account remove`, `queue run`, and `queue drop` accept `--dry-run` and perform no persistent side effects when it is set.
- R8. Dry-run combined with `--json` returns the envelope with a `data` field describing planned changes (targets, accounts, queue items) without applying them.
- R9. Dry-run exits 0 when the operation would succeed; exits with the appropriate taxonomy code when it would fail (missing backup, invalid config, queue item not found).

**Documentation and discoverability**

- R10. `docs/operations.md` and generated CLI reference document the envelope shape, exit-code table, and which commands support `--json` and `--dry-run`.
- R11. `clifwrap doctor --json` includes envelope version or contract version in metadata so agents can detect contract generation.

---

## Key Flows

- F1. CI preflight before deploy
  - **Trigger:** Pipeline runs health checks before releasing or rotating accounts.
  - **Actors:** CI script, clifwrap CLI
  - **Steps:** Run `config validate --json` → parse envelope → run `doctor --json --check` → branch on exit code and `data.issues`.
  - **Outcome:** Pipeline fails fast with a parseable reason, no custom grep rules per subcommand.
  - **Covered by:** R1, R4, R5, R6

- F2. Agent plans shim install without side effects
  - **Trigger:** Coding agent needs to verify install targets before modifying PATH shims.
  - **Actors:** Agent, clifwrap CLI
  - **Steps:** Run `install <app> --dry-run --json` → read planned shim and backup paths from `data` → confirm with user → run without dry-run.
  - **Outcome:** Agent never replaces a binary based on guessed flags.
  - **Covered by:** R7, R8, R9

- F3. Agent replays queue safely
  - **Trigger:** Capacity recovered; automation needs to drain queued work.
  - **Actors:** Agent or cron job
  - **Steps:** `queue list --json` → `queue run --dry-run --json` to preview → `queue run --json` to execute.
  - **Outcome:** No duplicate replay; agent sees item count and outcomes in envelope.
  - **Covered by:** R1, R7, R8

---

## Acceptance Examples

- AE1. Envelope on success
  - **Covers:** R1, R3
  - **Given:** Valid config and `clifwrap config paths --json`.
  - **When:** Command completes successfully.
  - **Then:** stdout is JSON with success indicator true, command identity set, and prior path fields nested under `data`.

- AE2. Envelope on validation failure
  - **Covers:** R2, R6
  - **Given:** Config references a missing env ref.
  - **When:** `clifwrap config validate --json` runs.
  - **Then:** Envelope reports failure, `data` includes findings, exit code matches the config-error category in the documented taxonomy.

- AE3. Dry-run install
  - **Covers:** R7, R8, R9
  - **Given:** `searchcli` is on PATH and not yet shimmed.
  - **When:** `clifwrap install searchcli --dry-run --json` runs.
  - **Then:** Exit 0; `data` describes shim target and backup path; no shim file is written.

- AE4. Check mode exit code
  - **Covers:** R5, R6
  - **Given:** Doctor reports validation warnings and `--check` is set.
  - **When:** `clifwrap doctor --json --check` runs.
  - **Then:** Exit code is the documented operational-check-failure code; envelope success indicator is false or `data` reflects check failure per contract rules.

---

## Success Criteria

- A CI script can drive `validate` and `doctor --check` using only envelope parsing and documented exit codes, without per-command JSON shape knowledge.
- An agent can plan `install` and `queue run` via `--dry-run --json` without causing side effects.
- Operations docs list every `--json` and `--dry-run` command in one place.

---

## Scope Boundaries

**Deferred for later**

- Machine-readable command/schema discovery command (`reference`, `schema`, or equivalent)
- Full ai-native-cli-spec compliance on every subcommand
- `--json` on wrapped upstream CLI passthrough invocations
- Reliability track (proactive quota pick, circuit breakers, failover event log)
- Security track (keychain refs, credential tiering)
- Context-routing track (project profiles, per-account config dirs)

**Outside this product's identity**

- HTTP API or MCP server wrapping clifwrap
- Agent-specific natural-language CLI (clifwrap remains a standard POSIX-style CLI)

---

## Dependencies / Assumptions

- Extensibility track (`config validate`, `doctor` validation section) lands first or in parallel; agent-native work extends those JSON outputs rather than replacing validation behavior.
- Existing `--json` consumers are few (early v0.1); additive nesting under `data` is acceptable with a changelog note.
- Human-readable command output remains the default; JSON is opt-in per command via `--json`.
- Generated `docs/cli-reference.md` continues to be the published command inventory.

---

## Outstanding Questions

**Deferred to planning**

- Exact envelope field names and whether `ok`/`success` follows agent-native-design or an internal convention.
- Whether `account import` dry-run reuses the existing apply-without-apply pattern or gains an explicit `--dry-run` flag aligned with other mutators.
- Contract version bump policy: semver in envelope meta vs clifwrap package version.

---

## Sources / Research

- Prior brainstorm: `docs/brainstorms/2026-07-25-extensibility-requirements.md` (deferred agent-native track)
- Repo: `src/clifwrap/__main__.py` (existing `--json` flags), `docs/operations.md`, `docs/cli-reference.md`
- External: [agent-native-design](https://agents365-ai.github.io/agent-native-design/), [CLI Spec](https://clispec.dev/), codex-quota and gh CLI `--json` patterns from improvement research
