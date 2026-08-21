# SPDX-License-Identifier: Apache-2.0
"""Shared fixtures. The broken_chain cassette is synthetic (owned placeholder
ids) and encodes a model that trains on a dataset declaring no license.
"""
from __future__ import annotations

import json

import pytest

_INDEX = {
    "https://huggingface.co/api/models/acme/model-a": {
        "file": "model_info.json", "status": 200,
    },
    "https://huggingface.co/acme/model-a/resolve/modelsha/README.md": {
        "file": "model_readme.md", "status": 200,
    },
    "https://huggingface.co/api/datasets/acme/dataset-a": {
        "file": "dataset_info.json", "status": 200,
    },
    "https://huggingface.co/datasets/acme/dataset-a/resolve/datasha/README.md": {
        "file": "dataset_readme.md", "status": 200,
    },
}

_MODEL_INFO = {
    "sha": "modelsha",
    "cardData": {"license": "mit", "datasets": ["acme/dataset-a"]},
    "tags": [],
    "gated": False,
}
_DATASET_INFO = {"sha": "datasha", "cardData": {}, "tags": [], "gated": False}
_MODEL_README = "---\nlicense: mit\ndatasets:\n  - acme/dataset-a\n---\n# Model A\n"
_DATASET_README = "# Dataset A\nNo license is stated on this card.\n"


@pytest.fixture
def broken_chain_cassette(tmp_path):
    (tmp_path / "index.json").write_text(json.dumps(_INDEX))
    (tmp_path / "model_info.json").write_text(json.dumps(_MODEL_INFO))
    (tmp_path / "dataset_info.json").write_text(json.dumps(_DATASET_INFO))
    (tmp_path / "model_readme.md").write_text(_MODEL_README)
    (tmp_path / "dataset_readme.md").write_text(_DATASET_README)
    return tmp_path


# A model card carrying hostile upstream references alongside one valid dataset.
_MALFORMED_MODEL_INFO = {
    "sha": "modelsha",
    "cardData": {
        "license": "mit",
        "base_model": "owner/../evil",  # multi-segment traversal -> invalid
        "datasets": ["owner/../../etc/passwd", "acme/dataset-a"],
    },
    "tags": ["base_model:finetune:owner/.."],
    "gated": False,
}


@pytest.fixture
def malformed_upstream_cassette(tmp_path):
    (tmp_path / "index.json").write_text(json.dumps(_INDEX))
    (tmp_path / "model_info.json").write_text(json.dumps(_MALFORMED_MODEL_INFO))
    (tmp_path / "dataset_info.json").write_text(json.dumps(_DATASET_INFO))
    (tmp_path / "model_readme.md").write_text("# Model A\nno links here\n")
    (tmp_path / "dataset_readme.md").write_text(_DATASET_README)
    return tmp_path
