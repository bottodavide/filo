# SPDX-License-Identifier: Apache-2.0
from filo.hub.cache import Cache
from filo.hub.client import HFClient
from filo.hub.fetch import Response
from filo.ir import AccessStatus, ArtifactKind


class FakeFetcher:
    def __init__(self, mapping):
        self.mapping = mapping

    def get(self, url, *, token=None):
        return self.mapping[url]


def test_info_public():
    url = "https://huggingface.co/api/models/acme/model-a"
    f = FakeFetcher(
        {url: Response(200, None, {"sha": "abc", "cardData": {"license": "mit"},
                                   "tags": ["x"], "gated": False})}
    )
    info = HFClient(f).info(ArtifactKind.MODEL, "acme/model-a")
    assert info.access is AccessStatus.PUBLIC and info.sha == "abc"


def test_info_gated_via_flag():
    url = "https://huggingface.co/api/models/acme/gated-a"
    f = FakeFetcher(
        {url: Response(200, None, {"sha": "s", "gated": "manual", "cardData": {}, "tags": []})}
    )
    assert HFClient(f).info(ArtifactKind.MODEL, "acme/gated-a").access is AccessStatus.GATED


def test_info_403_is_gated():
    url = "https://huggingface.co/api/models/acme/priv-a"
    f = FakeFetcher({url: Response(403, "forbidden", None)})
    assert HFClient(f).info(ArtifactKind.MODEL, "acme/priv-a").access is AccessStatus.GATED


def test_info_404_not_found():
    url = "https://huggingface.co/api/models/acme/missing"
    f = FakeFetcher({url: Response(404, "not found", None)})
    assert HFClient(f).info(ArtifactKind.MODEL, "acme/missing").access is AccessStatus.NOT_FOUND


def test_readme_cached(tmp_path):
    raw = "https://huggingface.co/acme/model-a/resolve/abc/README.md"
    f = FakeFetcher({raw: Response(200, "---\nlicense: mit\n---\nbody", None)})
    client = HFClient(f, cache=Cache(tmp_path))
    assert client.readme(ArtifactKind.MODEL, "acme/model-a", "abc").startswith("---")
    # second call served from cache even with an empty fetcher
    client2 = HFClient(FakeFetcher({}), cache=Cache(tmp_path))
    assert client2.readme(ArtifactKind.MODEL, "acme/model-a", "abc") is not None
