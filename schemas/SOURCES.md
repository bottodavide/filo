<!-- SPDX-License-Identifier: Apache-2.0 -->
# schemas/SOURCES.md

Provenance of the official JSON schema copies stored in this directory.
Fetched by the `standards-verifier` agent for task **V10** (verification of the
primary sources referenced in spec §10) on **2026-08-21**.

| File | Upstream URL | Upstream ref | Release status | Fetched (UTC) | SHA-256 |
|------|--------------|--------------|----------------|---------------|---------|
| `cyclonedx-1.6.schema.json` | https://raw.githubusercontent.com/CycloneDX/specification/1.6/schema/bom-1.6.schema.json | git tag `1.6` | Released 2024-04-09 (latest patch `1.6.2`, 2026-06-02) | 2026-08-21 | see `SHA256SUMS` below |
| `cyclonedx-1.7.schema.json` | https://raw.githubusercontent.com/CycloneDX/specification/1.7/schema/bom-1.7.schema.json | git tag `1.7` | Released 2025-10-21 (latest patch `1.7.1`, 2026-06-02) | 2026-08-21 | see `SHA256SUMS` below |

Both schemas declare `"$schema": "http://json-schema.org/draft-07/schema#"` and
`"$id": "http://cyclonedx.org/schema/bom-1.<v>.schema.json"`.

CycloneDX **1.7 IS an officially released version** (git tag `1.7`, 2025-10-21;
patch `1.7.1`, 2026-06-02). The `1.7` schema file downloaded here comes from the
released tag, not from `master`.

## How to reproduce

```sh
curl -sS -o cyclonedx-1.6.schema.json \
  https://raw.githubusercontent.com/CycloneDX/specification/1.6/schema/bom-1.6.schema.json
curl -sS -o cyclonedx-1.7.schema.json \
  https://raw.githubusercontent.com/CycloneDX/specification/1.7/schema/bom-1.7.schema.json
sha256sum cyclonedx-1.6.schema.json cyclonedx-1.7.schema.json
```

Release status verified via the GitHub API:
`https://api.github.com/repos/CycloneDX/specification/releases` and `/tags`.

The `filo-chain-1.schema.json` in this directory is NOT an external schema: it is
generated from `filo.ir.Chain` (this repo) and is the contract consumed by the
private `ailc-engine` repo.
