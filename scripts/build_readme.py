#!/usr/bin/env python3
"""Regenerate the provider tables in README.md between the table markers."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = (
    "| Name | Protocol | Base URL | Key variable | Models | Reference |\n"
    "| --- | --- | --- | --- | --- | --- |"
)


def row(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    data = tomllib.loads(text)
    docs = next((l.split("Docs: ", 1)[1] for l in text.splitlines() if l.startswith("# Docs: ")), "")
    key = f"`{data['key_env']}`" if data.get("auth") == "env" else "none"
    return (
        f"| `{data['name']}` | `{data['protocol']}` | `{data['base_url']}` | {key} "
        f"| {len(data.get('models', []))} | [docs]({docs}) |"
    )


def main() -> int:
    cloud = [row(p) for p in sorted((ROOT / "providers" / "cloud").glob("*.toml"))]
    local = [row(p) for p in sorted((ROOT / "providers" / "local").glob("*.toml"))]
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    for marker, rows in (("cloud", cloud), ("local", local)):
        block = f"<!-- {marker}:start -->\n{HEADER}\n" + "\n".join(rows) + f"\n<!-- {marker}:end -->"
        text, n = re.subn(rf"<!-- {marker}:start -->.*?<!-- {marker}:end -->", block, text, flags=re.S)
        if n != 1:
            print(f"marker {marker} not found in README.md", file=sys.stderr)
            return 1
    readme.write_text(text, encoding="utf-8")
    print(f"{len(cloud)} cloud, {len(local)} local")
    return 0


if __name__ == "__main__":
    sys.exit(main())
