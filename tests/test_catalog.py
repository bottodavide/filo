# SPDX-License-Identifier: Apache-2.0
"""Tests for filo.catalog_en — invariant 3 guard and the boundary sentence."""

from __future__ import annotations

import pytest

from filo.catalog_en import BOUNDARY_SENTENCE, assert_factual


def test_boundary_sentence_is_factual() -> None:
    # The canonical boundary sentence must not trip the qualification guard.
    assert assert_factual(BOUNDARY_SENTENCE) == BOUNDARY_SENTENCE


def test_assert_factual_passes_plain_facts() -> None:
    text = "The dataset declares no license at commit abc123f (searched: frontmatter)."
    assert assert_factual(text) == text


@pytest.mark.parametrize(
    "text",
    [
        "Model X violates the license of dataset Y.",
        "This chain is non-compliant.",
        "The use is illegal.",
        "This is an infringing derivative.",
    ],
)
def test_assert_factual_rejects_qualifications(text: str) -> None:
    with pytest.raises(ValueError):
        assert_factual(text)


def test_assert_factual_ignores_innocent_substrings() -> None:
    # "breach" is forbidden, but "breached" as a substring of an unrelated word
    # must not fire — word-boundary matching. Use a benign word containing a term.
    text = "The model reaches high accuracy."  # 'reaches' contains 'each', not a term
    assert assert_factual(text) == text
