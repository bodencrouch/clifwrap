from __future__ import annotations

import json
import os
import shlex
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .config import AccountConfig, ProviderConfig
from .state import get_default_account


@dataclass(frozen=True)
class ValidationFinding:
    provider: str
    field: str
    level: str
    message: str
    remediation: str | None = None


def _load_env_file(path: str) -> dict[str, str]:
    resolved_path = Path(os.path.expandvars(os.path.expanduser(path)))
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(resolved_path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise ValueError(f"{resolved_path}:{line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"{resolved_path}:{line_number}: empty key")
        parts = shlex.split(value, comments=False, posix=True)
        values[key] = parts[0] if parts else ""
    return values


def _env_lookup(name: str, account: AccountConfig) -> str | None:
    source = dict(os.environ)
    for env_file in account.env_files:
        try:
            source.update(_load_env_file(env_file))
        except (OSError, ValueError):
            return None
    return source.get(name)


def _resolve_env_refs(account: AccountConfig) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    for key, value in account.env.items():
        if not value.startswith("env:"):
            continue
        env_name = value[4:]
        if not env_name:
            findings.append(
                ValidationFinding(
                    provider="",
                    field=f"accounts.{account.name}.env.{key}",
                    level="error",
                    message=f"account {account.name!r} env ref for {key!r} is empty",
                    remediation=f"set {env_name} or use clifwrap account add with --env-ref {key}=VAR",
                )
            )
            continue
        if key in account.env_command:
            continue
        if _env_lookup(env_name, account) is None:
            findings.append(
                ValidationFinding(
                    provider="",
                    field=f"accounts.{account.name}.env.{key}",
                    level="error",
                    message=f"account {account.name!r} references unset env:{env_name}",
                    remediation=f"export {env_name} or add env_command for {key!r}",
                )
            )
    return findings


def validate_provider_static(provider: ProviderConfig) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    enabled = [account for account in provider.accounts if account.enabled]
    if not enabled:
        findings.append(
            ValidationFinding(
                provider=provider.name,
                field="accounts",
                level="error",
                message=f"{provider.name}: no enabled accounts configured",
                remediation=f"clifwrap account add {provider.name} <name> --env-ref TOKEN=ENVVAR",
            )
        )
    names: set[str] = set()
    for account in provider.accounts:
        if account.name in names:
            findings.append(
                ValidationFinding(
                    provider=provider.name,
                    field=f"accounts.{account.name}",
                    level="error",
                    message=f"{provider.name}: duplicate account name {account.name!r}",
                    remediation=f"clifwrap account rename {provider.name} {account.name} <new-name>",
                )
            )
        names.add(account.name)
        for finding in _resolve_env_refs(account):
            findings.append(
                ValidationFinding(
                    provider=provider.name,
                    field=finding.field,
                    level=finding.level,
                    message=finding.message,
                    remediation=finding.remediation,
                )
            )
    for index, pattern in enumerate(provider.retry_patterns):
        if not pattern.strip():
            findings.append(
                ValidationFinding(
                    provider=provider.name,
                    field=f"retry_patterns[{index}]",
                    level="error",
                    message=f"{provider.name}: retry_patterns contains an empty entry",
                    remediation="remove empty retry_patterns entries from config.toml",
                )
            )
    usage = provider.usage
    if usage and not usage.url.startswith(("http://", "https://", "{")):
        findings.append(
            ValidationFinding(
                provider=provider.name,
                field="usage.url",
                level="error",
                message=f"{provider.name}: usage.url must be http(s) or a template",
                remediation="fix providers.<name>.usage.url in config.toml",
            )
        )
    return findings


def _safe_error(exc: Exception) -> str:
    """Describe a probe failure without echoing argv or captured output.

    Probe commands are interpolated with resolved account credentials, and
    subprocess exception strings embed the full argv, so stringifying them
    directly would publish secrets into doctor output.
    """
    if isinstance(exc, subprocess.TimeoutExpired):
        return f"timed out after {exc.timeout:g}s"
    if isinstance(exc, subprocess.CalledProcessError):
        return f"exited with status {exc.returncode}"
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return str(exc.reason)
    if isinstance(exc, OSError):
        return exc.strerror or type(exc).__name__
    if isinstance(exc, ValueError):
        return str(exc)
    return type(exc).__name__


def _render_url(template: str, env: dict[str, str]) -> str:
    rendered = template
    for key, value in env.items():
        rendered = rendered.replace(f"${{{key}}}", value)
    while "{" in rendered and "}" in rendered:
        start = rendered.find("{")
        end = rendered.find("}", start)
        if end == -1:
            break
        expression = rendered[start + 1 : end]
        if ":" in expression:
            key, fallback = expression.split(":", 1)
            value = env.get(key, fallback)
        else:
            value = env.get(expression, "")
        rendered = rendered[:start] + value + rendered[end + 1 :]
    return rendered


def _account_env_for_probe(account: AccountConfig) -> dict[str, str]:
    source = dict(os.environ)
    for env_file in account.env_files:
        source.update(_load_env_file(env_file))
    resolved: dict[str, str] = {}
    for key, value in account.env.items():
        if value.startswith("env:"):
            env_name = value[4:]
            resolved_value = source.get(env_name)
            if resolved_value is None:
                raise ValueError(f"missing env:{env_name}")
            resolved[key] = resolved_value
        else:
            resolved[key] = os.path.expandvars(value)
    for key, command in account.env_command.items():
        proc = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        resolved[key] = proc.stdout.strip()
    return resolved


def _usage_probe(provider: ProviderConfig, env: dict[str, str]) -> list[ValidationFinding]:
    usage = provider.usage
    if not usage:
        return []
    findings: list[ValidationFinding] = []
    url = _render_url(usage.url, env)
    if not url.startswith(("http://", "https://")):
        return [
            ValidationFinding(
                provider=provider.name,
                field="usage.url",
                level="warning",
                message=f"{provider.name}: usage URL did not resolve to http(s)",
                remediation="set usage auth env vars or fix usage.url template",
            )
        ]
    token = env.get(usage.auth_env) or os.environ.get(usage.auth_env)
    headers = {usage.auth_header: f"{usage.auth_scheme} {token}".strip()}
    if usage.content_type:
        headers["Content-Type"] = usage.content_type
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=min(usage.timeout_seconds, 5.0)) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return [
            ValidationFinding(
                provider=provider.name,
                field="usage",
                level="warning",
                message=f"{provider.name}: usage probe failed ({_safe_error(exc)})",
                remediation=f"clifwrap doctor --provider {provider.name} --check",
            )
        ]
    if not isinstance(payload, dict):
        return [
            ValidationFinding(
                provider=provider.name,
                field="usage",
                level="warning",
                message=f"{provider.name}: usage probe returned non-object JSON",
                remediation="verify usage URL and auth_env for this provider",
            )
        ]
    return findings


def _status_command_probe(provider: ProviderConfig, env: dict[str, str]) -> list[ValidationFinding]:
    if not provider.status_command:
        return []
    command = []
    for part in provider.status_command:
        rendered = part
        for key, value in env.items():
            rendered = rendered.replace(f"${{{key}}}", value)
        command.append(rendered)
    try:
        proc = subprocess.run(
            command,
            env={**os.environ, **env, "CLIFWRAP_BYPASS": "1"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [
            ValidationFinding(
                provider=provider.name,
                field="status_command",
                level="warning",
                message=f"{provider.name}: status_command probe failed ({_safe_error(exc)})",
                remediation="fix status_command or account env for this provider",
            )
        ]
    if proc.returncode != 0:
        return [
            ValidationFinding(
                provider=provider.name,
                field="status_command",
                level="warning",
                message=f"{provider.name}: status_command exited with status {proc.returncode}",
                remediation="verify status_command and credentials",
            )
        ]
    output = proc.stdout.strip()
    if not output:
        return [
            ValidationFinding(
                provider=provider.name,
                field="status_command",
                level="warning",
                message=f"{provider.name}: status_command returned no output",
                remediation="ensure status_command prints JSON with remaining/limit",
            )
        ]
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return [
            ValidationFinding(
                provider=provider.name,
                field="status_command",
                level="warning",
                message=f"{provider.name}: status_command output is not JSON",
                remediation="configure status_command to emit JSON usage payload",
            )
        ]
    if not isinstance(payload, dict):
        return [
            ValidationFinding(
                provider=provider.name,
                field="status_command",
                level="warning",
                message=f"{provider.name}: status_command JSON is not an object",
                remediation="configure status_command to emit a JSON object",
            )
        ]
    keys = set(payload.keys())
    if not keys.intersection({"remaining", "remainingCredits", "limit", "planCredits", "used", "usage"}):
        return [
            ValidationFinding(
                provider=provider.name,
                field="status_command",
                level="warning",
                message=f"{provider.name}: status_command JSON lacks remaining/limit fields",
                remediation="include remaining and limit fields in status_command output",
            )
        ]
    return []


def probe_provider(provider: ProviderConfig, account: AccountConfig) -> list[ValidationFinding]:
    try:
        env = _account_env_for_probe(account)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        return [
            ValidationFinding(
                provider=provider.name,
                field=f"accounts.{account.name}",
                level="warning",
                message=f"{provider.name}: could not resolve account {account.name!r} env ({_safe_error(exc)})",
                remediation="clifwrap config validate --json",
            )
        ]
    findings: list[ValidationFinding] = []
    if provider.usage:
        findings.extend(_usage_probe(provider, env))
    if provider.status_command:
        findings.extend(_status_command_probe(provider, env))
    return findings


def probe_accounts(provider: ProviderConfig, *, all_accounts: bool = False) -> list[ValidationFinding]:
    enabled = [account for account in provider.accounts if account.enabled]
    if not enabled:
        return []
    if all_accounts:
        targets = enabled
    else:
        default_name = get_default_account(provider.name)
        default = next((account for account in enabled if account.name == default_name), None)
        targets = [default or enabled[0]]
    findings: list[ValidationFinding] = []
    for account in targets:
        findings.extend(probe_provider(provider, account))
    return findings


def findings_to_dict(findings: list[ValidationFinding]) -> list[dict[str, str | None]]:
    return [
        {
            "provider": finding.provider,
            "field": finding.field,
            "level": finding.level,
            "message": finding.message,
            "remediation": finding.remediation,
        }
        for finding in findings
    ]
