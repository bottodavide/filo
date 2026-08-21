# SPDX-License-Identifier: Apache-2.0
import json

from _cassette import CassetteFetcher

from filo.cli import _cmd_validate, main, run_trace
from filo.emit.validate import validate_bom


def test_run_trace_writes_all_formats(broken_chain_cassette, tmp_path):
    out = tmp_path / "out"
    run_trace(["acme/model-a"], CassetteFetcher(broken_chain_cassette), out=str(out))
    for name in ("chain.json", "bom.cdx.json", "report.md", "chain.mmd"):
        assert (out / name).exists(), name
    # the written BOM re-validates
    validate_bom(json.loads((out / "bom.cdx.json").read_text()))


def test_run_trace_format_subset(broken_chain_cassette, tmp_path):
    out = tmp_path / "out"
    run_trace(["acme/model-a"], CassetteFetcher(broken_chain_cassette), out=str(out),
              formats={"cdx"})
    assert (out / "bom.cdx.json").exists()
    assert not (out / "chain.json").exists()


def test_validate_subcommand(broken_chain_cassette, tmp_path, capsys):
    out = tmp_path / "out"
    run_trace(["acme/model-a"], CassetteFetcher(broken_chain_cassette), out=str(out),
              formats={"cdx"})
    # valid file -> 0
    class A:
        file = str(out / "bom.cdx.json")
        spec_version = "1.6"
    assert _cmd_validate(A()) == 0

    # broken file -> 2
    bad = tmp_path / "bad.cdx.json"
    bad.write_text('{"bomFormat": "CycloneDX"}')  # missing specVersion
    class B:
        file = str(bad)
        spec_version = "1.6"
    assert _cmd_validate(B()) == 2


def test_trace_rejects_unknown_format(capsys):
    assert main(["trace", "acme/model-a", "--format", "xml", "--out", "/tmp/filo-x"]) == 1
