<!-- SPDX-License-Identifier: Apache-2.0 -->
# filo

**filo** reconstructs the provenance chain of models and datasets on Hugging Face,
collects the **declared** licenses at each level **with evidence**, and emits an AIBOM in
CycloneDX (1.6 / 1.7) plus a neutral chain representation.

filo **states facts**. It does not assess license compatibility and does not make legal
judgements. What each license *requires* is out of scope on purpose.

> Status: early scaffolding (M0). The chain walker, exporters, CLI and web service are not
> implemented yet. See `DEVELOPMENT.md` for the build order and invariants.

## The four invariants

1. **No assertion without evidence** — every claim carries the source URL, the repo commit
   SHA at read time, a UTC timestamp, the extraction method, and the original snippet.
2. **Absence is a value, not a `null`** — a missing license is recorded as `absent` with the
   evidence of the search performed (which fields/files were checked).
3. **State, don't qualify** — no compatibility or legality verdicts. Output strings are factual.
4. **Language is separate from code** — user-facing strings live in catalog files (English here).

## Acceptance test

```
filo trace DeepMount00/rizzo-pii
```

must surface that `DeepMount00/pii-masking-ita` declares **no license**, with the evidence of
the locations searched. If it doesn't, the tool doesn't work.

## Install (dev)

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev,web]'
pytest
```

## License

Apache-2.0. See `LICENSE` and `NOTICE`. Every source file carries an
`SPDX-License-Identifier: Apache-2.0` header — the same hygiene this tool checks for.
