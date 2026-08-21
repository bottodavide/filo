# SPDX-License-Identifier: Apache-2.0
from filo.parse.licenses import PROPRIETARY_FAMILY, is_opaque, to_spdx


def test_known_spdx():
    assert to_spdx("apache-2.0") == "Apache-2.0"
    assert to_spdx("cc-by-nc-4.0") == "CC-BY-NC-4.0"


def test_unknown_is_none():
    assert to_spdx("llama3.1") is None
    assert to_spdx("totally-made-up") is None


def test_other_bare_is_opaque():
    assert is_opaque("other", None, None) is True
    assert is_opaque("other", "Acme License", None) is False
    assert is_opaque("other", None, "https://x/license") is False
    assert is_opaque("mit", None, None) is False


def test_proprietary_family():
    assert PROPRIETARY_FAMILY["llama3.1"] == "llama"
