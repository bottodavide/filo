# filo — development instructions

## What this repository is
Reconstructs the provenance chain of models and datasets on Hugging Face,
collects the declared licenses with their evidence, and emits CycloneDX 1.6/1.7.
IT STATES FACTS. It does not assess compatibility and does not make legal judgements.

## Invariants — never violate
1. No assertion without an EvidenceRef. If the type allows it, the type is wrong.
2. Absence is a state with evidence (LicenseConfidence.ABSENT + searched_locations),
   never None, never an empty string, never confused with a network error.
3. Facts only. No output string may contain "violates", "non-compliant",
   "illegal", "infringing" or the like.
4. Every limit applied to the traversal is declared in Chain.traversal.
   A silent truncation is a blocking defect.
5. No imports from private or internal repositories. This code is public.
6. No network calls in tests. Recorded cassettes only.
7. An `SPDX-License-Identifier: Apache-2.0` header on every source file.
8. User-facing output in English, in catalog files kept separate from the logic.

## Build order
ir.py and evidence.py first. Everything else is an adapter to or from them.
Do not build CycloneDX directly from the API responses.

## Schema changes
Adding optional fields: no schema_version bump.
Removing fields or changing their semantics: bump schema_version and write
the migration note in schemas/MIGRATIONS.md.

## Acceptance test
The acceptance test walks a real chain that contains a documented missing-license
link: the tool must surface the upstream artifact that declares no license, with the
evidence of the locations it searched. If it doesn't, the tool doesn't work. The
concrete fixture chain lives in tests/.

## What not to do
Do not download model weights. Do not add a license knowledge base. Do not add
compatibility logic. Those live elsewhere and must stay there.

## Language
Everything in this public repository is written in English — source, comments,
docs, and this file included.
