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


@pytest.mark.parametrize(
    "url",
    [
        "https://huggingface.co/api/models/acme/model-a",
        "https://cdn-lfs.huggingface.co/x",
    ],
)
def test_is_hf_url_accepts_hf(url):
    from filo.hub.fetch import is_hf_url

    assert is_hf_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.com/x",
        "https://huggingface.co.evil.com/x",  # suffix trick
        "http://huggingface.co/x",  # not https
        "https://nothuggingface.co/x",
    ],
)
def test_is_hf_url_rejects_other_hosts(url):
    from filo.hub.fetch import is_hf_url

    assert is_hf_url(url) is False


def test_httpx_fetcher_never_raises_on_malformed_url():
    # A control char makes httpx raise InvalidURL at request construction,
    # before any network — the fetcher must swallow it into a Response.
    from filo.hub.fetch import HttpxFetcher

    r = HttpxFetcher().get("https://huggingface.co/api/models/acme/model-a\n")
    assert r.status == 598 and r.json_body is None
