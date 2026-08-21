# SPDX-License-Identifier: Apache-2.0
from _cassette import CassetteFetcher

from filo.emit.cyclonedx import component_of, dependencies_of, to_cyclonedx
from filo.emit.validate import validate_bom
from filo.evidence import absent_license, build_evidence, utcnow
from filo.graph.walker import walk
from filo.hub.client import HFClient
from filo.ir import (
    AccessStatus,
    Artifact,
    ArtifactKind,
    ExtractionMethod,
    LicenseAssertion,
    LicenseConfidence,
    TraversalParams,
)


def _model():
    ev = build_evidence(
        "https://huggingface.co/api/models/acme/model-a",
        ExtractionMethod.CARD_FRONTMATTER, repo_sha="abc", text="license: mit",
    )
    lic = LicenseAssertion(
        raw_value="mit", spdx_id="MIT", confidence=LicenseConfidence.DECLARED, evidence=ev
    )
    return Artifact(
        id="hf:model:acme/model-a", kind=ArtifactKind.MODEL, platform="huggingface",
        name="model-a", namespace="acme", access=AccessStatus.PUBLIC, revision="abc",
        licenses=[lic], retrieved_at=utcnow(), depth=0,
    )


def _absent_dataset():
    la = absent_license("https://huggingface.co/api/datasets/acme/data-a", ["frontmatter"])
    return Artifact(
        id="hf:dataset:acme/data-a", kind=ArtifactKind.DATASET, platform="huggingface",
        name="data-a", namespace="acme", access=AccessStatus.PUBLIC,
        licenses=[la], retrieved_at=utcnow(), depth=1,
    )


def test_model_component():
    c = component_of(_model())
    assert c["type"] == "machine-learning-model" and c["name"] == "acme/model-a"
    assert c["licenses"] == [{"license": {"id": "MIT"}}]
    assert c["evidence"]["identity"][0]["field"] == "name"
    props = {p["name"]: p["value"] for p in c["properties"]}
    assert props["filo:license-confidence"] == "declared"
    assert props["filo:evidence-sha"] == "abc"


def test_absent_dataset_component():
    c = component_of(_absent_dataset())
    assert c["type"] == "data"
    assert c["data"][0]["type"] == "dataset"
    assert "licenses" not in c  # absence is not a blank license
    props = {p["name"]: p["value"] for p in c["properties"]}
    assert props["filo:license-confidence"] == "absent"
    assert "frontmatter" in props["filo:searched-locations"]


def test_dependencies_and_ancestors(broken_chain_cassette):
    chain = walk(
        ["acme/model-a"], HFClient(CassetteFetcher(broken_chain_cassette)), TraversalParams()
    )
    deps = dependencies_of(chain)
    assert {
        "ref": "hf:model:acme/model-a", "dependsOn": ["hf:dataset:acme/dataset-a"]
    } in deps
    model = component_of(chain.artifacts["hf:model:acme/model-a"], chain)
    ancestor_refs = [a["bom-ref"] for a in model["pedigree"]["ancestors"]]
    assert "hf:dataset:acme/dataset-a" in ancestor_refs


def test_full_bom_is_schema_valid(broken_chain_cassette):
    chain = walk(
        ["acme/model-a"], HFClient(CassetteFetcher(broken_chain_cassette)), TraversalParams()
    )
    for v in ("1.6", "1.7"):
        bom = to_cyclonedx(chain, v)
        validate_bom(bom, v)  # blocking: the file IS the deliverable
    bom = to_cyclonedx(chain, "1.6")
    ds = [c for c in bom["components"] if c["bom-ref"] == "hf:dataset:acme/dataset-a"][0]
    assert "licenses" not in ds
    assert any(
        p["name"] == "filo:license-confidence" and p["value"] == "absent" for p in ds["properties"]
    )
