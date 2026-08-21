# SPDX-License-Identifier: Apache-2.0
"""Content-addressed on-disk cache keyed by (repo_type, repo_id, sha, path); entries never expire.

Not implemented yet (scaffolding). See spec §2.4.
Build order: ir.py and evidence.py first; this module is an adapter to/from them.
"""

from __future__ import annotations
