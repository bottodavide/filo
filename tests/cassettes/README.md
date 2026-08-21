<!-- SPDX-License-Identifier: Apache-2.0 -->
# tests/cassettes/

Recorded Hugging Face HTTP responses, replayed in tests. **No test makes a real
network call** (DEVELOPMENT.md invariant 6). Add cassettes for the reference chains in
spec §2.11 — the acceptance case is a real chain with a documented missing-license
link; its concrete artifact id is fixed at M1 when the cassettes are recorded.
