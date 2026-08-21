# SPDX-License-Identifier: Apache-2.0
"""Offline validation of emitted BOMs against the local official schemas.

The CycloneDX schema $refs an external ``spdx.schema.json`` (for ``license.id``);
we resolve it from the local copy via a referencing registry so validation needs
no network. Signatures (``jsf`` ref) are never emitted, so that ref is never
resolved.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

_SCHEMAS = Path(__file__).resolve().parents[3] / "schemas"


@functools.lru_cache(maxsize=1)
def spdx_ids() -> frozenset[str]:
    """The SPDX license id enum from the local schema (membership check so we
    only emit ``license.id`` for ids the schema knows)."""
    data = json.loads((_SCHEMAS / "spdx.schema.json").read_text())
    return frozenset(data.get("enum", []))


@functools.lru_cache(maxsize=4)
def _validator(spec_version: str) -> Draft7Validator:
    bom = json.loads((_SCHEMAS / f"cyclonedx-{spec_version}.schema.json").read_text())
    spdx = json.loads((_SCHEMAS / "spdx.schema.json").read_text())
    registry = Registry().with_resources(
        [("spdx.schema.json", Resource.from_contents(spdx, DRAFT7))]
    )
    return Draft7Validator(bom, registry=registry)


def validate_bom(doc: dict, spec_version: str = "1.6") -> None:
    """Validate a CycloneDX BOM dict against the local official schema.

    Raises ``jsonschema.ValidationError`` on failure.
    """
    _validator(spec_version).validate(doc)
