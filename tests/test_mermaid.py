# SPDX-License-Identifier: Apache-2.0
from _cassette import CassetteFetcher

from filo.emit.mermaid import to_mermaid
from filo.graph.walker import walk
from filo.hub.client import HFClient
from filo.ir import TraversalParams


def test_mermaid_nodes_edges_and_marker(broken_chain_cassette):
    chain = walk(
        ["acme/model-a"], HFClient(CassetteFetcher(broken_chain_cassette)), TraversalParams()
    )
    mm = to_mermaid(chain)
    assert mm.startswith("graph TD")
    # a node per artifact, an edge per relation
    assert mm.count('["') == len(chain.artifacts)
    assert mm.count("-->") == len(chain.relations)
    # the absent-license dataset is marked
    assert "no-licence" in mm
    assert "trained_on" in mm
