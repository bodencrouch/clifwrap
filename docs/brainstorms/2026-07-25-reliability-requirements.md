---
date: 2026-07-25
topic: reliability
---

## Summary

Reduce wasted upstream attempts by picking a starting account with quota headroom before the first wrapped invocation. Extend existing capacity and status probing so failover begins on a viable account instead of always honoring a depleted default.

---

## Problem Frame

clifwrap fails over reactively: it runs on the default account (or `CLIFWRAP_CURRENT_ACCOUNT`), and only switches after a retryable exit code or output pattern match. When the default account is nearly exhausted, every invocation pays at least one doomed upstream call before failover — and may walk multiple accounts the same way on the next run.

Capacity control can queue or shed before execution when snapshots show low headroom, but account selection for execution and failover does not consistently prefer the account with the most remaining quota. Operators with `status_command` configured still see wasted retries because headroom data is not used to choose where to start.

---

## Key Decisions

- **Headroom-first start, not full reliability suite.** This track targets proactive starting-account selection and tighter coupling between capacity snapshots and failover. Circuit breakers, streaming output scanning, 429-vs-quota taxonomy, and failover audit logs are deferred.
- **Lazy probe when default is healthy.** When the default account has headroom above reserve plus estimated cost, keep it — preserve operator intent and avoid probe latency on every invocation.
- **Probe and pick when default is low or unknown.** When default is below threshold or capacity is unknown everywhere, select the enabled account with the best headroom before the first upstream exec.
- **Fail open on missing status data.** If no account returns usable quota data, behavior matches today: start on default and fail over reactively.
- **Reuse scheduling, don't duplicate.** Extend the existing capacity admission path in `src/clifwrap/scheduling.py` rather than a parallel account-picker.

---

## Requirements

**Starting account selection**

- R1. Before the first upstream invocation of a wrapped command, clifwrap evaluates enabled accounts that have usable capacity snapshots.
- R2. When the persisted default account has remaining quota at or above `reserve_threshold + estimated_cost`, that account is the starting account.
- R3. When the default is below threshold or capacity for the default is unknown, clifwrap selects the enabled account with the highest remaining quota (ties broken deterministically, e.g. config order).
- R4. Starting-account selection respects capacity-control policy: an account below reserve is not chosen unless no account meets reserve and policy is `execute` or `unknown_capacity_action` is `allow`.

**Failover interaction**

- R5. Once a starting account is chosen for a request, reactive failover (exit codes, output patterns) continues on that request's account chain without re-probing mid-request.
- R6. A retryable failure on the starting account still advances to the next account in the chain; proactive pick does not disable reactive failover.

**Observability**

- R7. When clifwrap overrides the default for headroom, stderr (human mode) notes which account was chosen and why (default low, better headroom elsewhere).
- R8. `status --json` and `doctor --json` expose per-account headroom and whether each account would be eligible as a starting account under current policy.

**Configuration**

- R9. Operators can disable proactive pick per provider (opt-out) while keeping capacity control; default is enabled when `status_command` or usage probing is configured.
- R10. `snapshot_ttl_seconds` behavior is documented: stale snapshots may approve a run that fails immediately — operators tune TTL vs probe cost.

---

## Key Flows

- F1. Default depleted, backup healthy
  - **Trigger:** Operator runs a wrapped command; default account snapshot shows 2 remaining, reserve is 5, backup shows 40.
  - **Actors:** Operator, clifwrap, upstream CLI
  - **Steps:** Admission reads snapshots → default below reserve → pick backup → run upstream on backup env → succeed without trying default.
  - **Outcome:** Zero wasted attempts on the depleted default.
  - **Covered by:** R2, R3, R5

- F2. Default healthy
  - **Trigger:** Default has ample headroom.
  - **Actors:** Operator, clifwrap
  - **Steps:** Snapshot check → default meets reserve → skip cross-account comparison → run on default.
  - **Outcome:** No added latency from probing all accounts.
  - **Covered by:** R2

- F3. All capacity unknown
  - **Trigger:** `status_command` fails or returns unparseable data for every account.
  - **Actors:** Operator, clifwrap
  - **Steps:** Proactive pick skipped → start on default → reactive failover if retryable error occurs.
  - **Outcome:** Behavior matches pre-track clifwrap; no regression when status unavailable.
  - **Covered by:** R4, R6

---

## Acceptance Examples

- AE1. Skip depleted default
  - **Covers:** R1, R3, R5
  - **Given:** Default snapshot remaining=1, backup remaining=50, reserve=5, estimated cost=1.
  - **When:** Wrapped command runs.
  - **Then:** First upstream invocation uses backup account env; default is not called.

- AE2. Keep healthy default
  - **Covers:** R2
  - **Given:** Default remaining=100, backup remaining=200, reserve=5.
  - **When:** Wrapped command runs.
  - **Then:** First upstream invocation uses default; no account override message unless verbose/debug.

- AE3. Unknown capacity fallback
  - **Covers:** R4, R6
  - **Given:** No account returns valid snapshot; default is `acct-a`.
  - **When:** Wrapped command runs and upstream returns retryable quota error on `acct-a`.
  - **Then:** clifwrap fails over to `acct-b` reactively as today.

- AE4. Status surfaces eligibility
  - **Covers:** R8
  - **Given:** Mixed headroom across accounts.
  - **When:** `clifwrap status searchcli --json`.
  - **Then:** Each account entry includes headroom and a field indicating starting-account eligibility under current policy.

---

## Success Criteria

- A wrapped command with a depleted default and healthy backup completes without calling the depleted account.
- Healthy defaults see no perceptible latency regression (no full-account probe when default is clearly viable).
- Operators can see in `status` why an account would or would not be chosen to start.

---

## Scope Boundaries

**Deferred for later**

- Per-account circuit breaker and cooldown after repeated failures
- Live stdout/stderr pattern scanning during streaming/TUI sessions
- Distinct handling for HTTP 429 rate-limit vs hard quota exhaustion
- Failover event log and switch audit trail (transparency track)
- Background quota watcher daemon for long-running interactive sessions

**Outside this product's identity**

- HTTP proxy that intercepts all traffic (teamclaude-style)
- Automatic purchase or provisioning of new upstream capacity

---

## Dependencies / Assumptions

- Extensibility track validation and merged provider config are available; proactive pick reads merged providers.
- `status_command` or usage URL probing already exists for built-in providers; providers without status data keep reactive-only behavior.
- Capacity control module (`src/clifwrap/scheduling.py`) and snapshot TTL in provider config remain the probe mechanism.
- Agent-native envelope work may land in parallel; this track adds fields to status payloads, compatible with a future envelope wrapper.

---

## Outstanding Questions

**Deferred to planning**

- Exact opt-out config key name (`proactive_pick = false` vs nested under `capacity_control`).
- Whether queue replay uses the same starting-account logic as live wrapped commands.
- Verbose flag vs always-on stderr notice when default is overridden.

---

## Sources / Research

- Prior brainstorm: `docs/brainstorms/2026-07-25-extensibility-requirements.md` (deferred reliability items)
- Repo: `src/clifwrap/runtime.py` (account selection, failover), `src/clifwrap/scheduling.py` (admission, snapshots)
- External: claude-rotate and codex-quota proactive quota-pick patterns; improvement research ranking proactive pick as highest ROI for wasted retries
