# SPDX-License-Identifier: Apache-2.0
"""Split and parse the YAML frontmatter of a model/dataset card.

Upstream ids read here come from untrusted third-party cards, so
``base_models``/``datasets`` filter every value through ``is_valid_repo_id``:
a malformed reference is dropped, never returned for URL construction.
"""
from __future__ import annotations

import yaml

from filo.ids import is_valid_repo_id


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n", 1)[1].split("\n---", 1)
    if len(parts) != 2:
        return {}, text
    try:
        fm = yaml.safe_load(parts[0]) or {}
    except yaml.YAMLError:
        return {}, text
    if not isinstance(fm, dict):
        return {}, text
    body = parts[1].lstrip("-").lstrip("\n")
    return fm, body


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def base_models(fm: dict) -> list[tuple[str, str | None]]:
    rel = fm.get("base_model_relation")
    rel = rel if isinstance(rel, str) else None
    return [(rid, rel) for rid in _as_list(fm.get("base_model")) if is_valid_repo_id(rid)]


def datasets(fm: dict) -> list[str]:
    return [d for d in _as_list(fm.get("datasets")) if is_valid_repo_id(d)]


def license_fields(fm: dict) -> tuple[str | None, str | None, str | None]:
    def s(key: str) -> str | None:
        v = fm.get(key)
        return v if isinstance(v, str) else None

    return s("license"), s("license_name"), s("license_link")
