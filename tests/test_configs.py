# SPDX-License-Identifier: Apache-2.0
from filo.parse.configs import adapter_base_model, config_base_model


def test_adapter():
    assert adapter_base_model(b'{"base_model_name_or_path": "acme/base-a"}') == "acme/base-a"


def test_config_only_repo_like():
    assert config_base_model(b'{"_name_or_path": "acme/base-a"}') == "acme/base-a"
    assert config_base_model(b'{"_name_or_path": "/local/path"}') is None


def test_bad_json():
    assert adapter_base_model(b"not json") is None
