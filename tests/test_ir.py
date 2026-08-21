# SPDX-License-Identifier: Apache-2.0
"""Tests for filo.ir — the neutral internal representation."""

from __future__ import annotations

from datetime import UTC, datetime, timezone

import pytest
from pydantic import ValidationError

from filo.evidence import absent_license, build_evidence, utcnow
from filo.ir import (
    AccessStatus,
    Artifact,
    ArtifactKind,
    Chain,
    EvidenceRef,
    ExtractionMethod,
    LicenseAssertion,
    LicenseConfidence,
    Relation,
    RelationKind,
    TraversalParams,
)

URL = "https://huggingface.co/owner/model-a"


def _declared_license() -> LicenseAssertion:
    return LicenseAssertion(
        raw_value="mit",
        spdx_id="MIT",
        confidence=LicenseConfidence.DECLARED,
        evidence=build_evidence(URL, ExtractionMethod.API_TAG, text="mit"),
    )


def _artifact(**kw: object) -> Artifact:
    base: dict[str, object] = dict(
        id="hf:model:owner/model-a",
        kind=ArtifactKind.MODEL,
        platform="huggingface",
        name="model-a",
        access=AccessStatus.PUBLIC,
        retrieved_at=utcnow(),
    )
    base.update(kw)
    return Artifact(**base)  # type: ignore[arg-type]


# --- evidence-carrying invariants ------------------------------------------ #
def test_relation_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        Relation(  # type: ignore[call-arg]
            source_id="a", target_id="b", kind=RelationKind.FINETUNED_FROM, confidence="declared"
        )


def test_license_assertion_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        LicenseAssertion(  # type: ignore[call-arg]
            raw_value="mit", confidence=LicenseConfidence.DECLARED
        )


def test_absent_license_cannot_carry_a_value() -> None:
    ev = build_evidence(URL, ExtractionMethod.ABSENT, searched_locations=["frontmatter"])
    with pytest.raises(ValidationError):
        LicenseAssertion(
            raw_value="", spdx_id="MIT", confidence=LicenseConfidence.ABSENT, evidence=ev
        )


def test_absent_license_requires_absent_evidence() -> None:
    ev = build_evidence(URL, ExtractionMethod.API_TAG, text="mit")
    with pytest.raises(ValidationError):
        LicenseAssertion(raw_value="", confidence=LicenseConfidence.ABSENT, evidence=ev)


# --- evidence model itself -------------------------------------------------- #
def test_evidence_absent_needs_searched_locations() -> None:
    with pytest.raises(ValidationError):
        EvidenceRef(url=URL, retrieved_at=utcnow(), method=ExtractionMethod.ABSENT)


def test_evidence_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError):
        EvidenceRef(
            url=URL,
            retrieved_at=datetime(2026, 8, 21, 12, 0, 0),  # naive
            method=ExtractionMethod.API_TAG,
        )


def test_evidence_autofills_snippet_sha() -> None:
    ev = EvidenceRef(
        url=URL, retrieved_at=utcnow(), method=ExtractionMethod.API_TAG, snippet="mit"
    )
    assert ev.snippet_sha256 is not None


def test_evidence_rejects_mismatched_sha() -> None:
    with pytest.raises(ValidationError):
        EvidenceRef(
            url=URL,
            retrieved_at=utcnow(),
            method=ExtractionMethod.API_TAG,
            snippet="mit",
            snippet_sha256="deadbeef",
        )


# --- traversal / truncation ------------------------------------------------- #
def test_truncation_requires_reason() -> None:
    with pytest.raises(ValidationError):
        TraversalParams(truncated=True)


def test_truncation_with_reason_ok() -> None:
    tp = TraversalParams(truncated=True, truncation_reasons=["max depth 6 reached"])
    assert tp.truncated is True


# --- Chain round-trip ------------------------------------------------------- #
def test_chain_roundtrips_json() -> None:
    art = _artifact(licenses=[_declared_license()])
    absent_art = _artifact(
        id="hf:dataset:owner/dataset-a",
        kind=ArtifactKind.DATASET,
        name="dataset-a",
        licenses=[absent_license(URL, ["cardData.license", "frontmatter"])],
    )
    chain = Chain(
        roots=[art.id],
        artifacts={art.id: art, absent_art.id: absent_art},
        relations=[
            Relation(
                source_id=art.id,
                target_id=absent_art.id,
                kind=RelationKind.TRAINED_ON,
                confidence="declared",
                evidence=build_evidence(URL, ExtractionMethod.CARD_FRONTMATTER, text="datasets:"),
            )
        ],
        generated_at=utcnow(),
        generator="filo/0.0.1",
        traversal=TraversalParams(),
    )
    restored = Chain.model_validate_json(chain.model_dump_json())
    assert restored.roots == [art.id]
    # The broken link — the absent-license dataset — survives the round-trip.
    ds = restored.artifacts["hf:dataset:owner/dataset-a"]
    assert ds.licenses[0].confidence is LicenseConfidence.ABSENT
    assert ds.licenses[0].evidence.searched_locations


def test_chain_schema_version_pinned() -> None:
    with pytest.raises(ValidationError):
        Chain(
            schema_version=2,  # type: ignore[arg-type]
            roots=["x"],
            generated_at=utcnow(),
            generator="filo/0.0.1",
            traversal=TraversalParams(),
        )


def test_datetimes_normalised_to_utc() -> None:
    # A non-UTC aware datetime is accepted and normalised.
    from datetime import timedelta

    tz = timezone(timedelta(hours=2))
    ev = EvidenceRef(
        url=URL,
        retrieved_at=datetime(2026, 8, 21, 12, 0, 0, tzinfo=tz),
        method=ExtractionMethod.API_TAG,
    )
    assert ev.retrieved_at.utcoffset() == UTC.utcoffset(ev.retrieved_at)
