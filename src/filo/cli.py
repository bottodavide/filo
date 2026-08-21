# SPDX-License-Identifier: Apache-2.0
"""filo command-line interface.

Not implemented yet (scaffolding). See spec §2.9.
Commands: trace, validate, cache, version.
"""

from __future__ import annotations

import sys

from filo import __version__


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "version":
        print(f"filo/{__version__}")
        return 0
    print("filo: not implemented yet (scaffolding). See DEVELOPMENT.md and spec §2.9.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
