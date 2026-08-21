# SPDX-License-Identifier: Apache-2.0
"""Neutral internal representation (IR) of a provenance chain.

This is the core of ``filo``: everything else is an adapter to or from these
types. It is written before the HTTP client and before the exporters on purpose
(see ``DEVELOPMENT.md``).

The IR encodes the system invariants in the *types* themselves:

1. No assertion without evidence — :class:`LicenseAssertion` and :class:`Relation`
   both require an :class:`EvidenceRef`. There is no way to construct one without.
2. Absence is a value — :class:`LicenseConfidence.ABSENT` plus
   ``EvidenceRef.searched_locations`` express "we looked and found nothing",
   never ``None`` and never a network error.
4. Every applied traversal limit is declared — :class:`TraversalParams` records
   truncation explicitly; a silent truncation is a blocking defect.

(Invariant 3 — state, don't qualify — is enforced on the *output* strings, see
``catalog_en.assert_factual``.)
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from filo.evidence import sha256_hex

__all__ = [
    "ExtractionMethod",
    "EvidenceRef",
    "LicenseConfidence",
    "LicenseAssertion",
    "ArtifactKind",
    "AccessStatus",
    "Artifact",
    "RelationKind",
    "Relation",
    "TraversalParams",
    "Warning",
    "Chain",
    "SNIPPET_MAX",
]

SNIPPET_MAX = 500


def _ensure_aware(value: datetime | None) -> datetime | None:
    """Reject naive datetimes; normalise to UTC. Invariant: timestamps are UTC-aware."""
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (UTC)")
    return value.astimezone(UTC)


# --------------------------------------------------------------------------- #
# Evidence
# --------------------------------------------------------------------------- #
class ExtractionMethod(StrEnum):
    API_TAG = "api_tag"  # license field of the HF API
    CARD_FRONTMATTER = "card_frontmatter"  # YAML at the top of the README
    CARD_BODY_LINK = "card_body_link"  # link in the card body
    CARD_BODY_TEXT = "card_body_text"  # textual mention in the card body
    REPO_FILE = "repo_file"  # LICENSE, config.json, adapter_config.json
    HF_AUTO_TAG = "hf_auto_tag"  # platform-generated tag
    ABSENT = "absent"  # search performed, nothing found


class EvidenceRef(BaseModel):
    """Provenance of a single assertion. Required wherever an assertion is made."""

    url: HttpUrl
    repo_sha: str | None = None
    retrieved_at: datetime
    method: ExtractionMethod
    snippet: str | None = Field(default=None, max_length=SNIPPET_MAX)
    snippet_sha256: str | None = None
    searched_locations: list[str] = Field(default_factory=list)

    _aware = field_validator("retrieved_at")(_ensure_aware)

    @model_validator(mode="after")
    def _check_consistency(self) -> EvidenceRef:
        # Snippet and its fingerprint must agree; auto-fill the fingerprint when omitted.
        if self.snippet is not None:
            digest = sha256_hex(self.snippet)
            if self.snippet_sha256 is None:
                object.__setattr__(self, "snippet_sha256", digest)
            elif self.snippet_sha256 != digest:
                raise ValueError("snippet_sha256 does not match snippet")
        elif self.snippet_sha256 is not None:
            raise ValueError("snippet_sha256 set without a snippet")

        # Invariant 2: absence is a documented search.
        if self.method is ExtractionMethod.ABSENT:
            if self.snippet is not None:
                raise ValueError("ABSENT evidence must not carry a snippet")
            if not self.searched_locations:
                raise ValueError("ABSENT evidence must list searched_locations")
        return self


# --------------------------------------------------------------------------- #
# Licenses
# --------------------------------------------------------------------------- #
class LicenseConfidence(StrEnum):
    DECLARED = "declared"  # API tag or frontmatter license field
    INFERRED = "inferred"  # deduced from the card body or a LICENSE file
    OPAQUE = "opaque"  # declared "other" with no name nor link
    ABSENT = "absent"  # no information found


class LicenseAssertion(BaseModel):
    raw_value: str = ""  # what was literally there: "cc-by-nc-4.0", "other", "llama3.1"
    spdx_id: str | None = None  # normalised when recognisable, else None
    license_name: str | None = None
    license_link: HttpUrl | None = None
    confidence: LicenseConfidence
    evidence: EvidenceRef

    @model_validator(mode="after")
    def _check_absence(self) -> LicenseAssertion:
        if self.confidence is LicenseConfidence.ABSENT:
            if self.evidence.method is not ExtractionMethod.ABSENT:
                raise ValueError("ABSENT license must carry ABSENT evidence")
            if self.spdx_id or self.license_name or self.license_link:
                raise ValueError("ABSENT license cannot carry a value")
        return self


# --------------------------------------------------------------------------- #
# Artifacts and relations
# --------------------------------------------------------------------------- #
class ArtifactKind(StrEnum):
    MODEL = "model"
    DATASET = "dataset"
    CODE = "code"
    SERVICE = "service"


class AccessStatus(StrEnum):
    PUBLIC = "public"
    GATED = "gated"
    PRIVATE = "private"
    NOT_FOUND = "not_found"
    ERROR = "error"


class Artifact(BaseModel):
    id: str  # "hf:model:DeepMount00/rizzo-pii" — stable key
    kind: ArtifactKind
    platform: str  # "huggingface", "github", "openai", ...
    namespace: str | None = None
    name: str
    revision: str | None = None  # commit SHA
    url: HttpUrl | None = None
    access: AccessStatus
    access_note: str | None = None
    licenses: list[LicenseAssertion] = Field(default_factory=list)
    downloads: int | None = None
    last_modified: datetime | None = None
    retrieved_at: datetime
    depth: int = 0
    raw_tags: list[str] = Field(default_factory=list)

    _aware_retrieved = field_validator("retrieved_at")(_ensure_aware)
    _aware_modified = field_validator("last_modified")(_ensure_aware)


class RelationKind(StrEnum):
    FINETUNED_FROM = "finetuned_from"
    ADAPTER_OF = "adapter_of"
    QUANTIZED_FROM = "quantized_from"
    MERGED_FROM = "merged_from"
    TRAINED_ON = "trained_on"
    EVALUATED_ON = "evaluated_on"
    DERIVED_FROM = "derived_from"  # generic, when the kind cannot be determined
    USES_SERVICE = "uses_service"


class Relation(BaseModel):
    source_id: str  # the downstream artifact
    target_id: str  # the upstream artifact
    kind: RelationKind
    confidence: Literal["declared", "inferred"]
    evidence: EvidenceRef


# --------------------------------------------------------------------------- #
# Chain
# --------------------------------------------------------------------------- #
class TraversalParams(BaseModel):
    """Every limit applied to the traversal is declared here (invariant 4)."""

    max_depth: int = 6
    max_artifacts: int | None = None
    no_body_scan: bool = False
    truncated: bool = False
    truncation_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _truncation_has_reason(self) -> TraversalParams:
        if self.truncated and not self.truncation_reasons:
            raise ValueError("a truncated traversal must state its reasons")
        return self


class Warning(BaseModel):
    code: str
    message: str
    artifact_id: str | None = None


class Chain(BaseModel):
    schema_version: Literal[1] = 1
    roots: list[str]  # the ids the analysis started from
    artifacts: dict[str, Artifact] = Field(default_factory=dict)
    relations: list[Relation] = Field(default_factory=list)
    generated_at: datetime
    generator: str  # "filo/0.3.1"
    traversal: TraversalParams
    warnings: list[Warning] = Field(default_factory=list)

    _aware = field_validator("generated_at")(_ensure_aware)
