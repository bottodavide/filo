# SPDX-License-Identifier: Apache-2.0
from _cassette import CassetteFetcher

from filo.emit.mermaid import to_mermaid
from filo.evidence import absent_license, utcnow
from filo.graph.walker import walk
from filo.hub.client import HFClient
from filo.ir import AccessStatus, Artifact, ArtifactKind, Chain, TraversalParams


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


def _artifact(repo_id: str):
    ns, _, name = repo_id.partition("/")
    la = absent_license(f"https://huggingface.co/api/models/{repo_id}", ["frontmatter"])
    return Artifact(
        id=f"hf:model:{repo_id}", kind=ArtifactKind.MODEL, platform="huggingface",
        name=name, namespace=ns, access=AccessStatus.PUBLIC, licenses=[la],
        retrieved_at=utcnow(),
    )


def test_node_ids_do_not_collide_on_punctuation():
    # 'acme/a.b' and 'acme/a-b' would collapse under a naive [^A-Za-z0-9]->_ id.
    a1, a2 = _artifact("acme/a.b"), _artifact("acme/a-b")
    chain = Chain(
        roots=[a1.id], artifacts={a1.id: a1, a2.id: a2}, generated_at=utcnow(),
        generator="filo/0.0.1", traversal=TraversalParams(),
    )
    mm = to_mermaid(chain)
    assert "n0[" in mm and "n1[" in mm  # two distinct nodes
    assert mm.count('["') == 2
