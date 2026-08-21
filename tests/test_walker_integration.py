# SPDX-License-Identifier: Apache-2.0
from _cassette import CassetteFetcher

from filo.chain_schema import validate_chain
from filo.graph.walker import walk
from filo.hub.client import HFClient
from filo.ir import Chain, TraversalParams


def test_chain_serializes_and_validates(broken_chain_cassette):
    chain = walk(
        ["acme/model-a"], HFClient(CassetteFetcher(broken_chain_cassette)), TraversalParams()
    )
    doc = chain.model_dump(mode="json")
    validate_chain(doc)  # schema-valid: the file IS the deliverable
    # round-trips back into the IR
    assert Chain.model_validate(doc).artifacts
