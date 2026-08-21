# SPDX-License-Identifier: Apache-2.0
from _cassette import CassetteFetcher

from filo.graph.walker import walk
from filo.hub.client import HFClient
from filo.ids import canonical_id
from filo.ir import ArtifactKind, LicenseConfidence, TraversalParams


def test_walk_surfaces_absent_license(broken_chain_cassette):
    client = HFClient(CassetteFetcher(broken_chain_cassette))
    chain = walk(["acme/model-a"], client, TraversalParams(max_depth=6))
    ds_id = canonical_id(ArtifactKind.DATASET, "acme", "dataset-a")
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
