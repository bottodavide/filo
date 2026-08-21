# SPDX-License-Identifier: Apache-2.0
from _cassette import CassetteFetcher

from filo.catalog_en import BOUNDARY_SENTENCE, assert_factual
from filo.emit.report import to_report_md
from filo.graph.walker import walk
from filo.hub.client import HFClient
from filo.ir import TraversalParams


def test_report_contains_gaps_and_boundary(broken_chain_cassette):
    chain = walk(
        ["acme/model-a"], HFClient(CassetteFetcher(broken_chain_cassette)), TraversalParams()
    )
    md = to_report_md(chain)
    assert "hf:dataset:acme/dataset-a" in md
    assert "no declared licence: 1" in md
    assert md.rstrip().endswith(BOUNDARY_SENTENCE)
    assert_factual(md)  # invariant 3: does not raise
