# SPDX-License-Identifier: Apache-2.0
"""Explicit raw->SPDX table. Maps only when the match is certain; everything
else keeps spdx_id=None and the raw value. 'other' and proprietary model
families get dedicated handling. This module recognises and names — it does not
say what a license requires (that lives in ailc-engine).
"""
from __future__ import annotations

_SPDX: dict[str, str] = {
    "mit": "MIT",
    "apache-2.0": "Apache-2.0",
    "bsd-2-clause": "BSD-2-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "gpl-2.0": "GPL-2.0-only",
    "gpl-3.0": "GPL-3.0-only",
    "lgpl-3.0": "LGPL-3.0-only",
    "agpl-3.0": "AGPL-3.0-only",
    "mpl-2.0": "MPL-2.0",
    "cc0-1.0": "CC0-1.0",
    "cc-by-4.0": "CC-BY-4.0",
    "cc-by-sa-4.0": "CC-BY-SA-4.0",
    "cc-by-nc-4.0": "CC-BY-NC-4.0",
    "cc-by-nd-4.0": "CC-BY-ND-4.0",
    "cc-by-nc-sa-4.0": "CC-BY-NC-SA-4.0",
    "cc-by-nc-nd-4.0": "CC-BY-NC-ND-4.0",
    "odc-by": "ODC-By-1.0",
    "odbl": "ODbL-1.0",
    "pddl": "PDDL-1.0",
}

PROPRIETARY_FAMILY: dict[str, str] = {
    "llama2": "llama",
    "llama3": "llama",
    "llama3.1": "llama",
    "llama3.2": "llama",
    "llama3.3": "llama",
    "gemma": "gemma",
    "qwen": "qwen",
    "openrail": "rail",
    "openrail++": "rail",
    "bigscience-openrail-m": "rail",
    "creativeml-openrail-m": "rail",
}


def to_spdx(raw: str) -> str | None:
    return _SPDX.get(raw.strip().lower())


def is_opaque(raw: str, license_name: str | None, license_link: str | None) -> bool:
    return raw.strip().lower() == "other" and not license_name and not license_link
