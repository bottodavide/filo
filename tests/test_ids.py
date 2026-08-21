# SPDX-License-Identifier: Apache-2.0
import pytest

from filo.ids import (
    canonical_id,
    dedup_key,
    is_valid_repo_id,
    parse_input_id,
    repo_id_of,
)
from filo.ir import ArtifactKind


@pytest.mark.parametrize(
    "raw,kind,ns,name",
    [
        ("acme/model-a", ArtifactKind.MODEL, "acme", "model-a"),
        ("model:acme/model-a", ArtifactKind.MODEL, "acme", "model-a"),
        ("datasets/acme/data-a", ArtifactKind.DATASET, "acme", "data-a"),
        ("dataset:acme/data-a", ArtifactKind.DATASET, "acme", "data-a"),
    ],
)
def test_parse_input_id(raw, kind, ns, name):
    assert parse_input_id(raw) == (kind, ns, name)


def test_parse_input_id_rejects_bad():
    with pytest.raises(ValueError):
        parse_input_id("no-slash")


def test_canonical_and_keys():
    cid = canonical_id(ArtifactKind.MODEL, "Acme", "Model-A")
    assert cid == "hf:model:Acme/Model-A"
    assert dedup_key(cid) == "hf:model:acme/model-a"
    assert repo_id_of(cid) == "Acme/Model-A"


def test_is_valid_repo_id_accepts_normal():
    assert is_valid_repo_id("acme/model-a")
    assert is_valid_repo_id("Acme_Org/Model.v2-b")


@pytest.mark.parametrize(
    "bad",
    [
        "no-slash",
        "owner/..",
        "owner/.",
        "../owner/name",
        "owner/../../etc/passwd",
        "owner//name",
        "owner/na me",
        "owner/name\r\nEvil: 1",
        "acme/model-a\n",  # lone trailing newline ($ vs \Z regression)
        "acme/model-a\n\n",
        "http://evil.com/x",
        "@evil.com/x",
        ".hidden/name",
        "",
    ],
)
def test_is_valid_repo_id_rejects_hostile(bad):
    assert is_valid_repo_id(bad) is False


@pytest.mark.parametrize("bad", ["owner/..", "owner/name\r\nX", "owner/../../x"])
def test_parse_input_id_rejects_hostile(bad):
    with pytest.raises(ValueError):
        parse_input_id(bad)
