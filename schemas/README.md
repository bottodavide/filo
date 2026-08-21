<!-- SPDX-License-Identifier: Apache-2.0 -->
# schemas/

Local, offline copies of the JSON schemas filo validates against.

| File | Source | Status |
|------|--------|--------|
| `cyclonedx-1.6.schema.json` | https://raw.githubusercontent.com/CycloneDX/specification/master/schema/bom-1.6.schema.json | ⬜ to fetch (standards-verifier, before the exporter) |
| `cyclonedx-1.7.schema.json` | official CycloneDX specification repo | ⬜ to fetch |
| `filo-chain-1.schema.json`  | generated from `filo.ir.Chain` (this repo) | ⬜ to generate |

**Do not implement the CycloneDX exporter before these schemas are in place and validation
runs in the test suite.** Producing an invalid document is a blocking defect because the file
IS the deliverable (spec §2.7, §10).

`filo-chain-1.schema.json` is the contract consumed by the private `ailc-engine` repo; its
evolution rules live in `MIGRATIONS.md` (added when the first schema change happens).
