#!/usr/bin/env python3
"""Fill cloud templates with model lists and settings from models.dev.

models.dev (https://models.dev) is the open model database opencode uses. For
every cloud template mapped below, the script rewrites `models` and
`[model_settings]` from it: tool-calling, non-deprecated models only, context
window and output limit from `limit`, the `reasoning` flag, and effort levels
mapped onto VibePod's portable set. It never picks a default model and never
touches `base_url`/`auth`; URL and variable mismatches are only reported.

Gateways whose model ids models.dev does not carry (see CATALOGS) are listed
from their own public model endpoint instead, one template per region.

Usage: python scripts/sync_models.py [--source api.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
import urllib.request
from pathlib import Path

SOURCE = "https://models.dev/api.json"
ROOT = Path(__file__).resolve().parent.parent / "providers" / "cloud"

#: template name -> models.dev provider id
PROVIDERS = {
    "openai": "openai",
    "anthropic": "anthropic",
    "openrouter": "openrouter",
    "deepseek": "deepseek",
    "deepseek-anthropic": "deepseek",
    "groq": "groq",
    "mistral": "mistral",
    "together": "togetherai",
    "fireworks": "fireworks-ai",
    "xai": "xai",
    "gemini-openai": "google",
    "huggingface": "huggingface",
    "cerebras": "cerebras",
    "moonshot": "moonshotai",
    "moonshot-anthropic": "moonshotai",
    "zai": "zai",
    "zai-anthropic": "zai",
    "minimax": "minimax",
    "minimax-anthropic": "minimax",
    "dashscope": "alibaba",
    "perplexity": "perplexity",
    "ollama-cloud": "ollama-cloud",
    "scaleway": "scaleway",
    "nebius": "nebius",
}

#: models.dev effort value -> VibePod portable level (others are dropped)
LEVELS = {"none": "off", "minimal": "minimal", "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh"}
LEVEL_ORDER = ("off", "minimal", "low", "medium", "high", "xhigh")


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def settings_for(model: dict) -> dict:
    settings: dict = {}
    limit = model.get("limit") or {}
    if isinstance(limit.get("context"), int) and limit["context"] > 0:
        settings["context_window"] = limit["context"]
    if isinstance(limit.get("output"), int) and limit["output"] > 0:
        settings["max_output_tokens"] = limit["output"]
    reasoning = model.get("reasoning")
    if isinstance(reasoning, bool):
        settings["reasoning"] = reasoning
    levels: set[str] = set()
    for option in model.get("reasoning_options") or []:
        if option.get("type") == "effort":
            levels |= {LEVELS[v] for v in option.get("values", []) if v in LEVELS}
    if levels and reasoning:
        settings["reasoning_levels"] = [level for level in LEVEL_ORDER if level in levels]
    return settings


def render(header: list[str], data: dict, models: dict[str, dict]) -> str:
    lines = list(header)
    lines += [
        "version = 1",
        f"name = {toml_string(data['name'])}",
        f"protocol = {toml_string(data['protocol'])}",
        f"base_url = {toml_string(data['base_url'])}",
        f"auth = {toml_string(data.get('auth', 'none'))}",
    ]
    if data.get("key_env"):
        lines.append(f"key_env = {toml_string(data['key_env'])}")
    if models:
        lines.append("models = [")
        lines += [f"  {toml_string(m)}," for m in models]
        lines.append("]")
    else:
        lines.append("models = []")
    if data.get("default_model") in models:
        lines.append(f"default_model = {toml_string(data['default_model'])}")
    for model, settings in models.items():
        if not settings:
            continue
        lines += ["", f"[model_settings.{toml_string(model)}]"]
        for key, value in settings.items():
            lines.append(f"{key} = {json.dumps(value)}")
    return "\n".join(lines) + "\n"


def sync(db: dict, name: str, provider_id: str) -> str:
    path = ROOT / f"{name}.toml"
    text = path.read_text(encoding="utf-8")
    header = [line for line in text.splitlines() if line.startswith("#")]
    data = tomllib.loads(text)
    provider = db.get(provider_id)
    if provider is None:
        return f"{name}: models.dev has no provider '{provider_id}'"
    notes = []
    api = (provider.get("api") or "").rstrip("/")
    if api and api != data["base_url"].rstrip("/") and not name.endswith("-anthropic"):
        notes.append(f"base_url differs from models.dev api {api}")
    env = provider.get("env") or []
    if env and data.get("key_env") and data["key_env"] not in env:
        notes.append(f"key_env {data['key_env']} not in models.dev env {env}")
    models = {
        model_id: settings_for(model)
        for model_id, model in sorted(provider["models"].items())
        if model.get("tool_call") and model.get("status") != "deprecated"
    }
    path.write_text(render(header, data, models), encoding="utf-8")
    summary = f"{name}: {len(models)} models"
    return summary + ("; " + "; ".join(notes) if notes else "")


#: Resellers not in models.dev: keep their own model ids (filtered to chat and
#: coding models), take settings from the first-party entry with the same id.
RESELLERS: dict[str, str] = {
    "entrim": r".*",
    "llmapi": (
        r"^(gpt-(4\.1|4o|5|6)[\w.-]*|o1|o3(-mini)?|claude-[\w.-]+|gemini-[\w.-]+"
        r"|glm-[\w.-]+|zai-glm-[\w.-]+|deepseek[\w./-]*|kimi-[\w.-]+|qwen[\w.-]*|qwq-plus"
        r"|minimax-m[\w.-]*|grok-4[\w.-]*|mistral-large[\w.-]*|devstral[\w.-]*"
        r"|codestral[\w.-]*|llama-[\w.-]+|gpt-oss-[\w.-]+|mimo-[\w.-]+)$"
    ),
}
#: Ids that match the families above but are not chat models.
NON_CHAT = re.compile(
    r"(image|tts|transcribe|search|embed|ocr|live|-vl|v-turbo|\dv\b|glm-4\.\dv|omni|audio)",
)
#: models.dev providers tried in order for a reseller id (first-party first).
FIRST_PARTY = (
    "openai", "anthropic", "google", "deepseek", "zai", "moonshotai", "alibaba",
    "minimax", "xai", "mistral", "groq", "togetherai", "fireworks-ai", "openrouter",
)


def _index(db: dict) -> dict[str, dict]:
    """Model metadata by normalised id (lowercase, vendor prefix stripped)."""
    index: dict[str, dict] = {}
    for provider_id in (*FIRST_PARTY, *sorted(db)):
        for model_id, model in db.get(provider_id, {}).get("models", {}).items():
            key = model_id.lower().rsplit("/", 1)[-1]
            index.setdefault(key, model)
    return index


def sync_reseller(db: dict, name: str, pattern: str) -> str:
    path = ROOT / f"{name}.toml"
    text = path.read_text(encoding="utf-8")
    header = [line for line in text.splitlines() if line.startswith("#")]
    data = tomllib.loads(text)
    keep = re.compile(pattern)
    index = _index(db)
    existing = data.get("model_settings", {})
    models: dict[str, dict] = {}
    for model_id in data.get("models", []):
        if not keep.match(model_id) or NON_CHAT.search(model_id.lower()):
            continue
        match = index.get(model_id.lower().rsplit("/", 1)[-1])
        # Without upstream metadata, keep whatever was curated by hand.
        models[model_id] = settings_for(match) if match else dict(existing.get(model_id, {}))
    data.pop("default_model", None)
    path.write_text(render(header, data, models), encoding="utf-8")
    matched = sum(1 for v in models.values() if v)
    return f"{name}: {len(models)} models kept, {matched} with settings (reseller)"


#: Gateways with a public model catalog: template name -> (catalog URL, kept
#: geolocations). Regional routers serve the whole catalog, so a regional
#: template lists only models whose inference stays in that region.
CATALOGS: dict[str, tuple[str, frozenset[str]]] = {
    "requesty": ("https://router.requesty.ai/v1/models", frozenset({"global"})),
    "requesty-anthropic": ("https://router.requesty.ai/v1/models", frozenset({"global"})),
    "requesty-eu": ("https://router.eu.requesty.ai/v1/models", frozenset({"eu"})),
    "requesty-eu-anthropic": ("https://router.eu.requesty.ai/v1/models", frozenset({"eu"})),
}


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "vibepod-providers-sync/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def sync_catalog(db: dict, name: str, catalog: list[dict], regions: frozenset[str]) -> str:
    path = ROOT / f"{name}.toml"
    text = path.read_text(encoding="utf-8")
    header = [line for line in text.splitlines() if line.startswith("#")]
    data = tomllib.loads(text)
    index = _index(db)
    models: dict[str, dict] = {}
    for model in sorted(catalog, key=lambda m: m["id"]):
        model_id = model["id"]
        if (
            not model.get("supports_tool_calling")
            or model.get("geolocation") not in regions
            or NON_CHAT.search(model_id.lower())
        ):
            continue
        # "bedrock/claude-opus-5@eu-central-1" -> first-party "claude-opus-5"
        match = index.get(model_id.lower().rsplit("/", 1)[-1].split("@", 1)[0])
        upstream = settings_for(match) if match else {}
        # The gateway's own limits describe the deployment actually served.
        own = settings_for({
            "limit": {"context": model.get("context_window"), "output": model.get("max_output_tokens")},
            "reasoning": model.get("supports_reasoning"),
        })
        settings = {**upstream, **own} | {
            k: upstream[k] for k in ("reasoning", "reasoning_levels") if k in upstream
        }
        if settings.get("max_output_tokens", 0) > settings.get("context_window", float("inf")):
            settings["max_output_tokens"] = settings["context_window"]
        models[model_id] = settings
    data.pop("default_model", None)
    path.write_text(render(header, data, models), encoding="utf-8")
    matched = sum(1 for v in models.values() if "reasoning_levels" in v)
    return f"{name}: {len(models)} models, {matched} with reasoning levels (catalog)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=SOURCE, help="models.dev api.json URL or local path")
    args = parser.parse_args()
    if args.source.startswith(("http://", "https://")):
        db = fetch_json(args.source)
    else:
        db = json.loads(Path(args.source).read_text(encoding="utf-8"))
    for name, provider_id in PROVIDERS.items():
        print(sync(db, name, provider_id))
    for name, pattern in RESELLERS.items():
        print(sync_reseller(db, name, pattern))
    catalogs: dict[str, list[dict]] = {}
    for name, (url, regions) in CATALOGS.items():
        if url not in catalogs:
            catalogs[url] = fetch_json(url)["data"]
        print(sync_catalog(db, name, catalogs[url], regions))
    return 0


if __name__ == "__main__":
    sys.exit(main())
