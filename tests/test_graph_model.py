# SPDX-License-Identifier: Apache-2.0
from filo.graph.model import collect_uplinks, relation_from_base
from filo.hub.client import RepoInfo
from filo.ir import AccessStatus, ArtifactKind, ExtractionMethod, RelationKind


def _info(card, tags):
    return RepoInfo(
        "acme/model-a", ArtifactKind.MODEL, AccessStatus.PUBLIC,
        sha="abc", card_data=card, tags=tags,
    )


def test_relation_mapping():
    assert relation_from_base("finetune") is RelationKind.FINETUNED_FROM
    assert relation_from_base(None) is RelationKind.DERIVED_FROM


def test_frontmatter_base_and_datasets():
    info = _info(
        {"base_model": "acme/base-a", "base_model_relation": "finetune",
         "datasets": ["acme/data-a"]},
        [],
    )
    links = collect_uplinks(info, readme=None, no_body_scan=True)
    kinds = {(link.repo_id, link.relation) for link in links}
    assert ("acme/base-a", RelationKind.FINETUNED_FROM) in kinds
    assert ("acme/data-a", RelationKind.TRAINED_ON) in kinds


def test_auto_tag_base_model():
    info = _info({}, ["base_model:finetune:acme/base-a"])
    links = collect_uplinks(info, readme=None, no_body_scan=True)
    assert any(link.repo_id == "acme/base-a" and link.confidence == "declared" for link in links)


def test_body_scan_inferred():
    info = _info({}, [])
    readme = "## Training data\nhttps://huggingface.co/datasets/acme/data-b\n"
    links = collect_uplinks(info, readme=readme, no_body_scan=False)
    hit = [link for link in links if link.repo_id == "acme/data-b"][0]
    assert hit.confidence == "inferred" and hit.method is ExtractionMethod.CARD_BODY_LINK


def test_malformed_upstreams_are_dropped():
    # hostile base_model and a traversal-y dataset must not become uplinks
    info = _info(
        {"base_model": "owner/na me", "datasets": ["owner/../../etc/passwd"]},
        ["base_model:finetune:owner/.."],
    )
    assert collect_uplinks(info, readme=None, no_body_scan=True) == []
