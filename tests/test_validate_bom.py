# SPDX-License-Identifier: Apache-2.0
import jsonschema
import pytest

from filo.emit.validate import spdx_ids, validate_bom


def _min_bom():
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "components": [{"type": "library", "name": "x"}],
    }


def test_spdx_ids_loaded():
    ids = spdx_ids()
    assert "MIT" in ids and "Apache-2.0" in ids


def test_valid_min_bom_passes():
    validate_bom(_min_bom())  # no raise


def test_license_id_validates_against_spdx_ref():
    bom = _min_bom()
    bom["components"][0]["licenses"] = [{"license": {"id": "MIT"}}]
    validate_bom(bom)  # resolves external spdx.schema.json offline


def test_bad_license_id_rejected():
    bom = _min_bom()
    bom["components"][0]["licenses"] = [{"license": {"id": "NOT-A-REAL-SPDX-ID"}}]
    with pytest.raises(jsonschema.ValidationError):
        validate_bom(bom)


def test_invalid_bom_fails():
    with pytest.raises(jsonschema.ValidationError):
        validate_bom({"bomFormat": "CycloneDX"})  # missing specVersion


def test_validates_1_7():
    bom = _min_bom()
    bom["specVersion"] = "1.7"
    validate_bom(bom, "1.7")
