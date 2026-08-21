<!-- SPDX-License-Identifier: Apache-2.0 -->
# schemas/

Local, offline copies of the JSON schemas filo validates against.

| File | Source | Status |
|------|--------|--------|
| `cyclonedx-1.6.schema.json` | git tag `1.6`, `bom-1.6.schema.json` (see `SOURCES.md`) | ✅ fetched 2026-08-21 (standards-verifier, V10) |
| `cyclonedx-1.7.schema.json` | git tag `1.7`, `bom-1.7.schema.json` (see `SOURCES.md`) | ✅ fetched 2026-08-21 (1.7 is a released version) |
| `filo-chain-1.schema.json`  | generated from `filo.ir.Chain` (this repo) | ✅ generated (M1) |
| `spdx.schema.json`          | git tag `1.6` (external ref of the BOM schema, `license.id`) | ✅ fetched (M2) |

Provenance, exact URLs, release status and SHA-256 hashes: see `SOURCES.md` and
`SHA256SUMS`. Field-by-field verification against these schemas: see
`docs/specs/2026-08-21-V10-verifica-fonti-primarie.md`.

**Do not implement the CycloneDX exporter before these schemas are in place and validation
runs in the test suite.** Producing an invalid document is a blocking defect because the file
IS the deliverable (spec §2.7, §10).

`filo-chain-1.schema.json` is the contract consumed by the private `ailc-engine` repo; its
evolution rules live in `MIGRATIONS.md` (added when the first schema change happens).
