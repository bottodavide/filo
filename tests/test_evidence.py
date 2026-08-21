# SPDX-License-Identifier: Apache-2.0
"""Tests for filo.evidence — construction and verification of evidence."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from filo.evidence import (
    SNIPPET_MAX,
    absent_evidence,
    absent_license,
    build_evidence,
    make_snippet,
    sha256_hex,
    utcnow,
    verify_evidence,
)
from filo.ir import EvidenceRef, ExtractionMethod, LicenseConfidence

URL = "https://huggingface.co/owner/model-a"


def test_sha256_hex_matches_hashlib() -> None:
    assert sha256_hex("abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_make_snippet_truncates_and_fingerprints() -> None:
    text = "x" * (SNIPPET_MAX + 50)
    snippet, digest = make_snippet(text)
    assert snippet is not None and len(snippet) == SNIPPET_MAX
    assert digest == sha256_hex(snippet)  # fingerprint is over the truncated text


def test_make_snippet_none() -> None:
    assert make_snippet(None) == (None, None)


def test_utcnow_is_aware_utc() -> None:
    now = utcnow()
    assert now.tzinfo is not None
    assert now.utcoffset() == UTC.utcoffset(now)


def test_build_evidence_populates_provenance() -> None:
    ev = build_evidence(
        URL, ExtractionMethod.CARD_FRONTMATTER, repo_sha="abc123f", text="license: mit"
    )
    assert ev.method is ExtractionMethod.CARD_FRONTMATTER
    assert ev.repo_sha == "abc123f"
    assert ev.snippet == "license: mit"
    assert ev.snippet_sha256 == sha256_hex("license: mit")
    assert ev.retrieved_at.tzinfo is not None


def test_absent_evidence_is_a_documented_search() -> None:
    ev = absent_evidence(URL, ["cardData.license", "frontmatter", "LICENSE file"])
    assert ev.method is ExtractionMethod.ABSENT
    assert ev.snippet is None
    assert ev.searched_locations == ["cardData.license", "frontmatter", "LICENSE file"]


def test_absent_evidence_requires_locations() -> None:
    with pytest.raises(ValueError):
        absent_evidence(URL, [])


def test_absent_license_assertion() -> None:
    la = absent_license(URL, ["cardData.license", "frontmatter"])
    assert la.confidence is LicenseConfidence.ABSENT
    assert la.spdx_id is None
    assert la.evidence.method is ExtractionMethod.ABSENT


def test_verify_evidence_true_for_wellformed() -> None:
    ev = build_evidence(URL, ExtractionMethod.API_TAG, text="mit")
    assert verify_evidence(ev) is True


def test_verify_evidence_false_for_tampered_snippet() -> None:
    ev = build_evidence(URL, ExtractionMethod.API_TAG, text="mit")
    # Bypass model validation to simulate hand-edited / corrupted data.
    tampered = ev.model_copy(update={"snippet": "apache-2.0"})
    assert verify_evidence(tampered) is False


def test_verify_evidence_true_for_absent() -> None:
    ev = absent_evidence(URL, ["frontmatter", "cardData.license"])
    assert verify_evidence(ev) is True


def test_verify_evidence_false_for_absent_without_locations() -> None:
    ev = EvidenceRef.model_construct(
        url=URL,
        repo_sha=None,
        retrieved_at=utcnow(),
        method=ExtractionMethod.ABSENT,
        snippet=None,
        snippet_sha256=None,
        searched_locations=[],  # invalid: absence with no documented search
    )
    assert verify_evidence(ev) is False


def test_verify_evidence_false_for_orphan_sha() -> None:
    ev = EvidenceRef.model_construct(
        url=URL,
        repo_sha=None,
        retrieved_at=utcnow(),
        method=ExtractionMethod.API_TAG,
        snippet=None,
        snippet_sha256="deadbeef",  # sha without a snippet
        searched_locations=[],
    )
    assert verify_evidence(ev) is False


def test_verify_evidence_false_for_naive_datetime() -> None:
    ev = EvidenceRef.model_construct(
        url=URL,
        repo_sha=None,
        retrieved_at=datetime(2026, 8, 21, 12, 0, 0),  # naive on purpose
        method=ExtractionMethod.API_TAG,
        snippet=None,
        snippet_sha256=None,
        searched_locations=[],
    )
    assert verify_evidence(ev) is False
