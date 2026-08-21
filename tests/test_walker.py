# SPDX-License-Identifier: Apache-2.0
from _cassette import CassetteFetcher

from filo.graph.walker import walk
from filo.hub.client import HFClient
from filo.ids import canonical_id
from filo.ir import ArtifactKind, LicenseConfidence, TraversalParams


def test_walk_surfaces_absent_license(broken_chain_cassette):
    client = HFClient(CassetteFetcher(broken_chain_cassette))
    chain = walk(["acme/model-a"], client, TraversalParams(max_depth=6))
    ds_id = canonical_id(ArtifactKind.DATASET, "acme/dataset-a")
    ds = chain.artifacts[ds_id]
    assert ds.licenses[0].confidence is LicenseConfidence.ABSENT
    assert ds.licenses[0].evidence.searched_locations  # documented search
    # the trained_on relation is present
    assert any(r.target_id == ds_id for r in chain.relations)


def test_walk_declares_truncation(broken_chain_cassette):
    client = HFClient(CassetteFetcher(broken_chain_cassette))
    chain = walk(["acme/model-a"], client, TraversalParams(max_depth=0))
    assert chain.traversal.truncated is True
    assert chain.traversal.truncation_reasons


def test_walk_survives_malformed_upstreams(malformed_upstream_cassette):
    # Hostile base_model / dataset / tag values must not crash the walk, and
    # must not produce an artifact for a malformed reference.
    client = HFClient(CassetteFetcher(malformed_upstream_cassette))
    chain = walk(["acme/model-a"], client, TraversalParams())
    ids = set(chain.artifacts)
    assert "hf:dataset:acme/dataset-a" in ids  # the one valid upstream survives
    assert not any("etc" in i or ".." in i for i in ids)


def test_walker_warns_on_invalid_uplink(broken_chain_cassette, monkeypatch):
    # Defense in depth: even if a parser regression yielded an invalid repo_id,
    # the walker fails closed with a documented warning instead of raising.
    import filo.graph.walker as walker_mod
    from filo.graph.model import UpLink
    from filo.ir import ArtifactKind, ExtractionMethod, RelationKind

    def fake_uplinks(info, readme, *, no_body_scan):
        return [
            UpLink("owner/../../evil", ArtifactKind.MODEL, RelationKind.DERIVED_FROM,
                   "declared", ExtractionMethod.CARD_FRONTMATTER)
        ]

    monkeypatch.setattr(walker_mod, "collect_uplinks", fake_uplinks)
    chain = walk(["acme/model-a"], HFClient(CassetteFetcher(broken_chain_cassette)),
                 TraversalParams(max_depth=2))
    assert any(w.code == "malformed_upstream_reference" for w in chain.warnings)
    assert not chain.relations  # nothing invalid was queued
