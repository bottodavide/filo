# SPDX-License-Identifier: Apache-2.0
from filo.parse.frontmatter import (
    base_models,
    datasets,
    license_fields,
    split_frontmatter,
)

CARD = """---
license: cc-by-nc-4.0
base_model: acme/base-a
base_model_relation: finetune
datasets:
  - acme/data-a
  - acme/data-b
---
# Title
body text
"""


def test_split():
    fm, body = split_frontmatter(CARD)
    assert fm["license"] == "cc-by-nc-4.0"
    assert body.strip().startswith("# Title")


def test_base_models_str_with_relation():
    fm, _ = split_frontmatter(CARD)
    assert base_models(fm) == [("acme/base-a", "finetune")]


def test_datasets_list():
    fm, _ = split_frontmatter(CARD)
    assert datasets(fm) == ["acme/data-a", "acme/data-b"]


def test_license_fields():
    fm, _ = split_frontmatter(CARD)
    assert license_fields(fm) == ("cc-by-nc-4.0", None, None)


def test_no_frontmatter():
    fm, body = split_frontmatter("just body")
    assert fm == {} and body == "just body"


def test_malformed_base_model_is_filtered():
    fm = {"base_model": ["no-slash", "owner/../../etc", "acme/ok-a"]}
    assert base_models(fm) == [("acme/ok-a", None)]


def test_malformed_datasets_are_filtered():
    fm = {"datasets": ["owner/name\r\nEvil: 1", "acme/data-a", ".hidden/x"]}
    assert datasets(fm) == ["acme/data-a"]
