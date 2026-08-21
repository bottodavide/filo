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
