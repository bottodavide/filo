# SPDX-License-Identifier: Apache-2.0
from filo.hub.cache import Cache


def test_put_get_roundtrip(tmp_path):
    c = Cache(tmp_path)
    assert c.get("model", "acme/model-a", "abc123", "README.md") is None
    c.put("model", "acme/model-a", "abc123", "README.md", b"hello")
    assert c.get("model", "acme/model-a", "abc123", "README.md") == b"hello"


def test_key_isolation(tmp_path):
    c = Cache(tmp_path)
    c.put("model", "acme/model-a", "abc123", "README.md", b"one")
    # different sha -> different slot
    assert c.get("model", "acme/model-a", "def456", "README.md") is None
