# SPDX-License-Identifier: Apache-2.0
import pytest

from filo.ids import canonical_id, dedup_key, parse_input_id, repo_id_of
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
