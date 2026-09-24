#!/usr/bin/env python3
"""Validate every provider template without depending on the VibePod CLI.

Checks the exchange-file contract documented at
https://github.com/VibePod/vibepod-cli/blob/main/docs/providers.md#sharing-providers:
schema version, filename == name (lowercase slug), protocol, credential-free
authentication, sane endpoint URL, model list and settings shapes.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

PROTOCOLS = {"openai-chat", "openai-responses", "anthropic"}
AUTH = {"none", "env", "key"}
LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh")
TOP_KEYS = {"version", "name", "protocol", "base_url", "auth", "key_env", "models", "default_model", "model_settings"}
SETTING_KEYS = {"context_window", "max_output_tokens", "reasoning", "reasoning_levels", "reasoning_default"}
SECRET_KEYS = {"api_key", "key", "token", "secret", "credential_file"}


def check(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        return [f"not valid TOML: {exc}"]
    unknown = set(data) - TOP_KEYS
    if unknown & SECRET_KEYS:
        errors.append(f"credential-like keys are forbidden: {sorted(unknown & SECRET_KEYS)}")
    elif unknown:
        errors.append(f"unknown keys: {sorted(unknown)}")
    if data.get("version") != 1:
        errors.append("version must be 1")
    name = data.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", name):
        errors.append("name must be a lowercase slug")
    elif name != path.stem:
        errors.append(f"name {name!r} must match the filename {path.stem!r}")
    protocol = data.get("protocol")
    if protocol not in PROTOCOLS:
        errors.append(f"protocol must be one of {sorted(PROTOCOLS)}")
    url = data.get("base_url")
    parts = urlsplit(url) if isinstance(url, str) else None
    if parts is None or parts.scheme not in ("http", "https") or not parts.hostname:
        errors.append("base_url must be an http(s) URL")
    else:
        if parts.username or parts.password or parts.query or parts.fragment:
            errors.append("base_url must not carry credentials, query, or fragment")
        if protocol == "anthropic" and parts.path.rstrip("/").endswith("/v1"):
            errors.append("Anthropic endpoints must not end with /v1 (clients append it)")
    auth = data.get("auth", "none")
    if auth not in AUTH:
        errors.append(f"auth must be one of {sorted(AUTH)}")
    key_env = data.get("key_env", "")
    if auth == "env" and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(key_env)):
        errors.append("auth = env requires a key_env variable name")
    if auth != "env" and key_env:
        errors.append("key_env only applies to auth = env")
    models = data.get("models", [])
    if not isinstance(models, list) or not all(isinstance(m, str) and m.strip() and m.isprintable() for m in models):
        errors.append("models must be a list of non-empty strings")
        models = []
    if len(set(models)) != len(models):
        errors.append("models must be unique")
    default = data.get("default_model", "")
    if default and default not in models:
        errors.append("default_model must be one of models")
    settings = data.get("model_settings", {})
    if not isinstance(settings, dict):
        errors.append("model_settings must be a table")
        settings = {}
    for model, entry in settings.items():
        if model not in models:
            errors.append(f"model_settings.{model!r}: not in models")
        if not isinstance(entry, dict):
            errors.append(f"model_settings.{model!r}: must be a table")
            continue
        if set(entry) - SETTING_KEYS:
            errors.append(f"model_settings.{model!r}: unknown keys {sorted(set(entry) - SETTING_KEYS)}")
        for field in ("context_window", "max_output_tokens"):
            value = entry.get(field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value <= 0):
                errors.append(f"model_settings.{model!r}.{field}: positive integer required")
        levels = entry.get("reasoning_levels", [])
        if not isinstance(levels, list) or any(level not in LEVELS for level in levels) or len(set(levels)) != len(levels):
            errors.append(f"model_settings.{model!r}.reasoning_levels: distinct values from {LEVELS}")
            levels = []
        if entry.get("reasoning") is False and (levels or entry.get("reasoning_default")):
            errors.append(f"model_settings.{model!r}: non-reasoning model with reasoning levels")
        chosen = entry.get("reasoning_default", "")
        if chosen and chosen not in (levels or LEVELS):
            errors.append(f"model_settings.{model!r}.reasoning_default: must be one of the accepted levels")
    if path.parent.name not in ("cloud", "local"):
        errors.append("file must live in providers/cloud/ or providers/local/")
    elif path.parent.name == "cloud" and auth == "none":
        errors.append("cloud templates reference a key (auth = env)")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "providers"
    files = sorted(root.glob("*/*.toml"))
    stray = sorted(p for p in root.glob("*.toml"))
    for path in stray:
        print(f"FAIL {path.relative_to(root.parent)}\n     - place files under providers/cloud/ or providers/local/")
    if not files:
        print("no provider files found", file=sys.stderr)
        return 1
    failed = 0
    for path in files:
        errors = check(path)
        status = "ok" if not errors else "FAIL"
        print(f"{status:4} {path.relative_to(root.parent)}")
        for error in errors:
            print(f"     - {error}")
        failed += bool(errors)
    print(f"{len(files) - failed}/{len(files)} valid")
    return 1 if failed or stray else 0


if __name__ == "__main__":
    sys.exit(main())
