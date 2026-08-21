# SPDX-License-Identifier: Apache-2.0
import jsonschema
import pytest

from filo.chain_schema import chain_json_schema, validate_chain
from filo.evidence import utcnow
from filo.ir import Chain, TraversalParams


def _minimal_chain_doc():
    return Chain(
        roots=["hf:model:acme/model-a"],
        generated_at=utcnow(),
        generator="filo/0.0.1",
        traversal=TraversalParams(),
    ).model_dump(mode="json")


def test_schema_has_expected_keys():
    s = chain_json_schema()
    assert "properties" in s and "artifacts" in s["properties"]


def test_valid_chain_passes():
    validate_chain(_minimal_chain_doc())  # no raise


def test_invalid_chain_fails():
    bad = _minimal_chain_doc()
    del bad["generator"]
    with pytest.raises(jsonschema.ValidationError):
        validate_chain(bad)
