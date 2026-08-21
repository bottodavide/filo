# SPDX-License-Identifier: Apache-2.0
"""Extract base-model references from config.json / adapter_config.json.

Values are validated through ``is_valid_repo_id`` (rejects '.'/'..' segments,
traversal and control chars) before being returned for URL construction.
"""
from __future__ import annotations

import json

from filo.ids import is_valid_repo_id


def _load(data: bytes) -> dict | None:
    try:
        obj = json.loads(data)
    except (json.JSONDecodeError, ValueError):
        return None
    return obj if isinstance(obj, dict) else None


def adapter_base_model(data: bytes) -> str | None:
    obj = _load(data)
    if not obj:
        return None
    v = obj.get("base_model_name_or_path")
    return v if isinstance(v, str) and is_valid_repo_id(v) else None


def config_base_model(data: bytes) -> str | None:
    obj = _load(data)
    if not obj:
        return None
    v = obj.get("_name_or_path")
    return v if isinstance(v, str) and is_valid_repo_id(v) else None
