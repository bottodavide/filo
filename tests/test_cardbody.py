# SPDX-License-Identifier: Apache-2.0
from filo.ir import ArtifactKind
from filo.parse.cardbody import find_hf_links

BODY = """## Training data
We trained on https://huggingface.co/datasets/acme/data-a and
the base https://huggingface.co/acme/base-a .
## References
See https://huggingface.co/acme/base-a again.
"""


def test_finds_model_and_dataset_dedup():
    hits = find_hf_links(BODY)
    keys = {(h.kind, h.repo_id) for h in hits}
    assert (ArtifactKind.DATASET, "acme/data-a") in keys
    assert (ArtifactKind.MODEL, "acme/base-a") in keys
    assert len(hits) == 2  # base-a deduped across the two sections


def test_captures_heading():
    hits = {h.repo_id: h.heading for h in find_hf_links(BODY)}
    assert hits["acme/data-a"] == "Training data"


def test_single_name_dataset_link():
    # KI-001: a canonical single-name dataset link must be a DATASET, not a
    # model 'datasets/code_search_net'.
    hits = find_hf_links("trained on https://huggingface.co/datasets/code_search_net\n")
    assert len(hits) == 1
    assert hits[0].kind is ArtifactKind.DATASET
    assert hits[0].repo_id == "code_search_net"


def test_bare_single_name_model_link_is_skipped():
    # A bare single-name link (docs/blog/org pages) is too noisy for a model.
    assert find_hf_links("see https://huggingface.co/docs\n") == []


def test_reserved_namespace_links_are_not_artifacts():
    # Prose links to Hugging Face site paths that are NOT repositories must not
    # enter the chain as phantom artifacts (observed on all-MiniLM-L6-v2):
    # site assets (front/), the legacy metrics pages (metrics/), the dataset
    # viewer (datasets/viewer), and two-segment docs/blog links.
    body = """
    thumbnail https://huggingface.co/front/thumbnails/v2/preview.png
    metric https://huggingface.co/metrics/rouge
    viewer https://huggingface.co/datasets/viewer
    guide https://huggingface.co/docs/transformers/index
    blog https://huggingface.co/blog/intro-to-embeddings
    """
    assert find_hf_links(body) == []


def test_reserved_namespace_does_not_shadow_real_repos():
    # The denylist must not swallow legitimate owner/name repos or canonical
    # single-name datasets.
    body = """
    https://huggingface.co/acme/base-a
    https://huggingface.co/datasets/acme/data-a
    https://huggingface.co/datasets/code_search_net
    """
    keys = {(h.kind, h.repo_id) for h in find_hf_links(body)}
    assert (ArtifactKind.MODEL, "acme/base-a") in keys
    assert (ArtifactKind.DATASET, "acme/data-a") in keys
    assert (ArtifactKind.DATASET, "code_search_net") in keys
    assert len(keys) == 3
