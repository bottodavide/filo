# SPDX-License-Identifier: Apache-2.0
import json

import pytest

from _cassette import CassetteFetcher


def test_cassette_returns_recorded(tmp_path):
    (tmp_path / "index.json").write_text(
        json.dumps({"https://x/api": {"file": "api.json", "status": 200}})
    )
    (tmp_path / "api.json").write_text(json.dumps({"sha": "abc"}))
    f = CassetteFetcher(tmp_path)
    r = f.get("https://x/api")
    assert r.status == 200 and r.json_body == {"sha": "abc"}


def test_cassette_unrecorded_raises(tmp_path):
    (tmp_path / "index.json").write_text("{}")
    with pytest.raises(AssertionError):
        CassetteFetcher(tmp_path).get("https://x/missing")
