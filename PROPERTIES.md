<!-- SPDX-License-Identifier: Apache-2.0 -->
# filo CycloneDX properties namespace

Everything the CycloneDX standard cannot express natively is emitted under the `filo:`
property namespace, so a third-party reader can interpret the output without guessing.
Properties are the CycloneDX `{name, value}` string pairs; duplicate names are allowed.

## On each component (`components[].properties`)

| Property | Values | Meaning |
|----------|--------|---------|
| `filo:license-confidence`    | `declared` \| `inferred` \| `opaque` \| `absent` | How the license was established. `opaque` = declared `other` with no name/link. `absent` = search performed, nothing found. Emitted only when the artifact carries a license assertion. |
| `filo:evidence-method`       | `api_tag`, `card_frontmatter`, `card_body_link`, `card_body_text`, `repo_file`, `hf_auto_tag`, `absent` | How the license was read. |
| `filo:evidence-url`          | URL | Exact, stable resource that was read. |
| `filo:evidence-sha`          | commit SHA | Repository commit at read time (when known). |
| `filo:evidence-retrieved-at` | ISO-8601 (UTC) | When it was read. |
| `filo:spdx-id`               | SPDX id | Normalised SPDX id, when recognised. |
| `filo:searched-locations`    | comma-separated | Where filo looked — emitted when the license is `absent`. |
| `filo:access`                | `public` \| `gated` \| `private` \| `not_found` \| `error` | Access status of the artifact. |
| `filo:traversal-depth`       | integer | Distance from the analysis root. |
| `filo:relation`              | `<kind>:<confidence>:<target-bom-ref>` | One per outgoing derivation edge, e.g. `trained_on:declared:hf:dataset:owner/name`. Mirrors `pedigree.ancestors` / `dependencies`. |

Derivation is also expressed structurally: upstream artifacts appear in the downstream
component's `pedigree.ancestors`, and the whole graph in the top-level `dependencies`.
Datasets additionally carry `component.data` (`componentData.type = "dataset"`). License
evidence is duplicated in `component.evidence.licenses`, and `component.evidence.identity`
is emitted as an **array** (the single-object form is deprecated since CycloneDX 1.6).

## On the BOM metadata (`metadata.properties`)

| Property | Values | Meaning |
|----------|--------|---------|
| `filo:generator`         | e.g. `filo/0.0.1` | The generator and version. |
| `filo:truncated`         | `true` \| `false` | Whether traversal was cut short (also in `chain.json` `traversal`). |
| `filo:truncation-reason` | string | One per applied limit (max depth / max artifacts / …). Emitted once per reason. |

> A silent truncation is a blocking defect: every applied limit is declared here and in
> `chain.json`. See spec §2.7 and the field mapping verified in
> `../docs/specs/2026-08-21-V10-verifica-fonti-primarie.md`.
