# SPDX-License-Identifier: Apache-2.0
"""English user-facing string catalog for ``filo`` (invariant 4: language is
separate from code) and the guard that enforces invariant 3 (state, don't
qualify).

All strings shown to a user live here, not inline in the logic, so a second
language costs a translation and not a rewrite.
"""

from __future__ import annotations

import re

__all__ = ["BOUNDARY_SENTENCE", "FORBIDDEN_OUTPUT_TERMS", "assert_factual"]

# The sentence that marks the boundary between filo (facts) and any downstream
# qualification. Written once, here.
BOUNDARY_SENTENCE = (
    "This report states what the declared chain contains and where it is "
    "incomplete. It does not assess whether the obligations of these licences "
    "are satisfied in your product: that depends on how you distribute it, and "
    "requires review."
)

# Invariant 3: filo constates, it does not qualify. These words signal a legal
# qualification and must never appear in a filo output string.
FORBIDDEN_OUTPUT_TERMS: frozenset[str] = frozenset(
    {
        "violates",
        "violation",
        "non-compliant",
        "noncompliant",
        "illegal",
        "infringing",
        "infringement",
        "unlawful",
        "breach",
    }
)

_WORD_RE = re.compile(r"[a-z][a-z-]*")


def assert_factual(text: str) -> str:
    """Return ``text`` unchanged, or raise ``ValueError`` if it qualifies.

    Guards filo output against invariant-3 violations. Matching is
    case-insensitive on word boundaries so that substrings inside innocent words
    do not trip it.
    """
    words = set(_WORD_RE.findall(text.lower()))
    hit = words & FORBIDDEN_OUTPUT_TERMS
    if hit:
        raise ValueError(
            f"output string qualifies (invariant 3): forbidden term(s) {sorted(hit)}"
        )
    return text
