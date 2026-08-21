# SPDX-License-Identifier: Apache-2.0
"""Generate and validate against the filo-chain schema (the contract consumed
by ailc-engine).
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from filo.ir import Chain


def chain_json_schema() -> dict:
    return Chain.model_json_schema()


def write_schema(path: Path) -> None:
    Path(path).write_text(
        json.dumps(chain_json_schema(), indent=2, sort_keys=True) + "\n"
    )


def validate_chain(doc: dict) -> None:
    jsonschema.validate(doc, chain_json_schema())
