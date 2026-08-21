# SPDX-License-Identifier: Apache-2.0
import json

from _cassette import CassetteFetcher

from filo.chain_schema import validate_chain
from filo.cli import main, run_trace, summarize
from filo.ir import LicenseConfidence


def test_run_trace_writes_valid_chain(broken_chain_cassette, tmp_path):
    out = tmp_path / "out"
    chain, code = run_trace(
        ["acme/model-a"], CassetteFetcher(broken_chain_cassette), out=str(out)
    )
    # all artifacts public and not truncated -> exit 0
    assert code == 0
    doc = json.loads((out / "chain.json").read_text())
    validate_chain(doc)  # the written file is schema-valid
    ds = chain.artifacts["hf:dataset:acme/dataset-a"]
    assert ds.licenses[0].confidence is LicenseConfidence.ABSENT


def test_summary_is_factual(broken_chain_cassette):
    chain, _ = run_trace(["acme/model-a"], CassetteFetcher(broken_chain_cassette))
    text = summarize(chain)
    assert "no declared license: 1" in text
    # invariant 3: the summary must not qualify
    from filo.catalog_en import assert_factual

    assert_factual(text)


def test_exit_incomplete_on_truncation(broken_chain_cassette, tmp_path):
    from filo.graph.walker import walk
    from filo.hub.client import HFClient
    from filo.ir import TraversalParams

    chain = walk(
        ["acme/model-a"], HFClient(CassetteFetcher(broken_chain_cassette)),
        TraversalParams(max_depth=0),
    )
    from filo.cli import _exit_code

    assert _exit_code(chain) == 2  # truncated


def test_main_version(capsys):
    assert main(["version"]) == 0
    assert "filo/" in capsys.readouterr().out
