<!-- SPDX-License-Identifier: Apache-2.0 -->
# filo CycloneDX properties namespace

Everything the CycloneDX standard cannot express natively is emitted under the `filo:`
property namespace, so a third-party reader can interpret the output without guessing.

| Property | Values | Meaning |
|----------|--------|---------|
| `filo:license-confidence`    | `declared` \| `inferred` \| `opaque` \| `absent` | How the license was established. `opaque` = declared `other` with no name/link. `absent` = search performed, nothing found. |
| `filo:evidence-url`          | URL | Exact, stable resource that was read. |
| `filo:evidence-sha`          | commit SHA | Repository commit at read time. |
| `filo:evidence-retrieved-at` | ISO-8601 (UTC) | When it was read. |
| `filo:evidence-method`       | extraction method | `api_tag`, `card_frontmatter`, `card_body_link`, `card_body_text`, `repo_file`, `hf_auto_tag`, `absent`. |
| `filo:searched-locations`    | comma-separated | Where filo looked (populated when method is `absent`). |
| `filo:traversal-depth`       | integer | Distance from the analysis root. |
| `filo:relation-kind`         | relation kind | `finetuned_from`, `adapter_of`, `quantized_from`, `merged_from`, `trained_on`, `evaluated_on`, `derived_from`, `uses_service`. |
| `filo:truncated`             | `true` \| `false` | Whether traversal was cut short (also recorded in `Chain.traversal`). |

> The exact CycloneDX field mapping (component types `machine-learning-model` / `data`,
> `modelCard`, `pedigree.ancestors`, `evidence.licenses`, `evidence.identity`) MUST be
> verified against the official schemas in `schemas/` before the exporter is implemented.
> See spec §2.7 and §10.
