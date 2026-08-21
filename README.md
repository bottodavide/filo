<!-- SPDX-License-Identifier: Apache-2.0 -->
# filo

**filo** reconstructs the provenance chain of models and datasets on Hugging Face,
collects the **declared** licenses at each level **with evidence**, and emits an AIBOM in
CycloneDX (1.6 / 1.7) plus a neutral chain representation.

filo **states facts**. It does not assess license compatibility and does not make legal
judgements. What each license *requires* is out of scope on purpose.

> **Status:** M0–M2 complete. `filo trace owner/name` walks the chain and writes a
> `chain.json`, a schema-validated **CycloneDX 1.6/1.7 AIBOM** (`bom.cdx.json`), a `report.md`
> and a Mermaid diagram — all evidence-backed. `filo validate <bom>` checks a BOM against the
> official schemas offline. Not implemented yet: the public web demo. See `DEVELOPMENT.md` for the
> build order and invariants.

## The four invariants

1. **No assertion without evidence** — every claim carries the source URL, the repo commit
   SHA at read time, a UTC timestamp, the extraction method, and the original snippet.
2. **Absence is a value, not a `null`** — a missing license is recorded as `absent` with the
   evidence of the search performed (which fields/files were checked).
3. **State, don't qualify** — no compatibility or legality verdicts. Output strings are factual.
4. **Language is separate from code** — user-facing strings live in catalog files (English here).

## Install

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'      # add ,web once the web demo lands
```

## Usage

```bash
# Walk a chain and write chain.json + bom.cdx.json + report.md + chain.mmd into ./out
filo trace sentence-transformers/all-MiniLM-L6-v2 --depth 2

# Options
filo trace <id> [<id> ...] \
    --depth N               # max traversal depth (default 6)
    --spec-version 1.6|1.7  # CycloneDX version (default 1.6)
    --format json,cdx,md,mmd  # which outputs to write (default all)
    --out DIR               # output directory (default ./out)
    --no-body-scan          # structured sources only (skip card-body links)
    --cache DIR             # persistent content-addressed cache
    --token ENV_VAR         # name of an env var holding a read-only HF token

# Validate a CycloneDX BOM offline against the official schemas
filo validate ./out/bom.cdx.json --spec-version 1.6

filo version
```

Ids accept `owner/name`, a canonical single name (`bert-base-uncased`), `model:owner/name`,
or `datasets/owner/name`.

**Exit codes:** `0` chain fully walked; `1` usage error; `2` chain walked but **truncated or
with inaccessible artifacts** (gated / not-found / error) — useful as a signal in CI.

Every emitted CycloneDX BOM is validated against the official schema before it is written; an
invalid document is a blocking defect, because the file *is* the deliverable. What CycloneDX
cannot express natively is carried under the `filo:` property namespace — see `PROPERTIES.md`.

## Acceptance test

filo is validated against a real provenance chain that contains a documented
**missing-license link**: the tool must surface the upstream artifact that declares
**no license**, together with the evidence of the locations it searched. If it doesn't,
the tool doesn't work. The concrete fixture chain lives in `tests/`.

## Development

```bash
pytest                       # no test makes a network call (recorded cassettes only)
ruff check src tests
mypy                         # --strict on ir.py + evidence.py
```

Build order and invariants are in `DEVELOPMENT.md`. Schemas (CycloneDX 1.6/1.7 + SPDX) are
vendored under `schemas/` with provenance in `schemas/SOURCES.md`.

## License

Apache-2.0. See `LICENSE` and `NOTICE`. Every source file carries an
`SPDX-License-Identifier: Apache-2.0` header — the same hygiene this tool checks for.
