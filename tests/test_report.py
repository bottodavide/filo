# SPDX-License-Identifier: Apache-2.0
from _cassette import CassetteFetcher

from filo.catalog_en import BOUNDARY_SENTENCE, assert_factual
from filo.emit.report import to_report_md
from filo.evidence import build_evidence, utcnow
from filo.graph.walker import walk
from filo.hub.client import HFClient
from filo.ir import (
    AccessStatus,
    Artifact,
    ArtifactKind,
    Chain,
    ExtractionMethod,
    LicenseAssertion,
    LicenseConfidence,
    TraversalParams,
)


def test_report_contains_gaps_and_boundary(broken_chain_cassette):
    chain = walk(
        ["acme/model-a"], HFClient(CassetteFetcher(broken_chain_cassette)), TraversalParams()
    )
    md = to_report_md(chain)
    assert "hf:dataset:acme/dataset-a" in md
    assert "no declared licence: 1" in md
    assert md.rstrip().endswith(BOUNDARY_SENTENCE)
    assert_factual(md)  # invariant 3: does not raise


def test_report_escapes_hostile_license():
    # A malicious upstream card sets license: to forge table rows / inject HTML.
    ev = build_evidence(
        "https://huggingface.co/api/models/acme/evil",
        ExtractionMethod.CARD_FRONTMATTER, text="x",
    )
    la = LicenseAssertion(
        raw_value="| forged | row |\n<script>",
        confidence=LicenseConfidence.DECLARED, evidence=ev,
    )
    a = Artifact(
        id="hf:model:acme/evil", kind=ArtifactKind.MODEL, platform="huggingface",
        name="evil", namespace="acme", access=AccessStatus.PUBLIC, licenses=[la],
        retrieved_at=utcnow(),
    )
    chain = Chain(
        roots=[a.id], artifacts={a.id: a}, generated_at=utcnow(),
        generator="filo/0.0.1", traversal=TraversalParams(),
    )
    md = to_report_md(chain)
    # the raw pipes are escaped (\|), so they cannot forge new table cells/rows
    assert "\\| forged \\| row \\|" in md
    assert "<script>" not in md and "&lt;script&gt;" in md  # HTML defanged
    # exactly one data row: the hostile newline did not split the cell into a row
    data_rows = [line for line in md.splitlines() if line.startswith("| `hf:")]
    assert len(data_rows) == 1
