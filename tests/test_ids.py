# SPDX-License-Identifier: Apache-2.0
import pytest

from filo.ids import (
    canonical_id,
    dedup_key,
    is_valid_repo_id,
    namespace_name,
    parse_input_id,
    repo_id_of,
)
from filo.ir import ArtifactKind


@pytest.mark.parametrize(
    "raw,kind,repo_id",
    [
        ("acme/model-a", ArtifactKind.MODEL, "acme/model-a"),
        ("model:acme/model-a", ArtifactKind.MODEL, "acme/model-a"),
        ("datasets/acme/data-a", ArtifactKind.DATASET, "acme/data-a"),
        ("dataset:acme/data-a", ArtifactKind.DATASET, "acme/data-a"),
        ("datasets/code_search_net", ArtifactKind.DATASET, "code_search_net"),
        ("bert-base-uncased", ArtifactKind.MODEL, "bert-base-uncased"),
    ],
)
def test_parse_input_id(raw, kind, repo_id):
    assert parse_input_id(raw) == (kind, repo_id)


def test_parse_input_id_rejects_bad():
    with pytest.raises(ValueError):
        parse_input_id("owner/na me")


def test_canonical_and_keys():
    cid = canonical_id(ArtifactKind.MODEL, "Acme/Model-A")
    assert cid == "hf:model:Acme/Model-A"
    assert dedup_key(cid) == "hf:model:acme/model-a"
    assert repo_id_of(cid) == "Acme/Model-A"


def test_canonical_single_name():
    cid = canonical_id(ArtifactKind.DATASET, "code_search_net")
    assert cid == "hf:dataset:code_search_net"
    assert repo_id_of(cid) == "code_search_net"


def test_namespace_name():
    assert namespace_name("acme/model-a") == ("acme", "model-a")
    assert namespace_name("code_search_net") == (None, "code_search_net")


def test_is_valid_repo_id_accepts_normal():
    assert is_valid_repo_id("acme/model-a")
    assert is_valid_repo_id("Acme_Org/Model.v2-b")
    assert is_valid_repo_id("code_search_net")  # single canonical name


@pytest.mark.parametrize(
    "bad",
    [
        "owner/..",
        "owner/.",
        "../owner/name",
        "owner/../../etc/passwd",
        "owner//name",
        "owner/na me",
        "owner/name\r\nEvil: 1",
        "acme/model-a\n",  # lone trailing newline ($ vs \Z regression)
        "acme/model-a\n\n",
        "..",
        ".",
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
