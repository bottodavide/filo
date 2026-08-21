# SPDX-License-Identifier: Apache-2.0
"""filo command-line interface.

`filo trace <id>` walks the provenance chain of a Hugging Face artifact and
writes chain.json, a validated CycloneDX BOM, a report and a diagram. The
chain-building logic lives in `run_trace`, which takes an injected fetcher so it
can be tested without the network; `main` wires the real HttpxFetcher.
`filo validate <file>` checks an existing BOM against the local schemas.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import jsonschema

from filo import __version__
from filo.emit.cyclonedx import to_cyclonedx
from filo.emit.mermaid import to_mermaid
from filo.emit.report import to_report_md
from filo.emit.validate import validate_bom
from filo.graph.walker import walk
from filo.hub.cache import Cache
from filo.hub.client import HFClient
from filo.hub.fetch import Fetcher, HttpxFetcher
from filo.ir import AccessStatus, Chain, LicenseConfidence, TraversalParams

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_INCOMPLETE = 2  # chain walked but truncated or with inaccessible artifacts

ALL_FORMATS = ("json", "cdx", "md", "mmd")


def run_trace(
    ids: list[str],
    fetcher: Fetcher,
    *,
    cache: Cache | None = None,
    depth: int = 6,
    no_body_scan: bool = False,
    token: str | None = None,
    out: str | None = None,
    formats: set[str] | None = None,
    spec_version: str = "1.6",
) -> tuple[Chain, int]:
    formats = formats or set(ALL_FORMATS)
    client = HFClient(fetcher, cache=cache, token=token)
    chain = walk(ids, client, TraversalParams(max_depth=depth, no_body_scan=no_body_scan))
    if out is not None:
        out_dir = Path(out)
        out_dir.mkdir(parents=True, exist_ok=True)
        if "json" in formats:
            (out_dir / "chain.json").write_text(chain.model_dump_json(indent=2))
        if "cdx" in formats:
            bom = to_cyclonedx(chain, spec_version)
            validate_bom(bom, spec_version)  # blocking: the file IS the deliverable
            (out_dir / "bom.cdx.json").write_text(json.dumps(bom, indent=2) + "\n")
        if "md" in formats:
            (out_dir / "report.md").write_text(to_report_md(chain))
        if "mmd" in formats:
            (out_dir / "chain.mmd").write_text(to_mermaid(chain))
    return chain, _exit_code(chain)


def _exit_code(chain: Chain) -> int:
    inaccessible = any(a.access is not AccessStatus.PUBLIC for a in chain.artifacts.values())
    if chain.traversal.truncated or inaccessible:
        return EXIT_INCOMPLETE
    return EXIT_OK


def summarize(chain: Chain) -> str:
    def count(pred) -> int:
        return sum(1 for a in chain.artifacts.values() if pred(a))

    def has_conf(a, c) -> bool:
        return any(lic.confidence is c for lic in a.licenses)

    return "\n".join(
        [
            f"artifacts: {len(chain.artifacts)}",
            f"relations: {len(chain.relations)}",
            f"no declared license: {count(lambda a: has_conf(a, LicenseConfidence.ABSENT))}",
            f"opaque license: {count(lambda a: has_conf(a, LicenseConfidence.OPAQUE))}",
            f"gated: {count(lambda a: a.access is AccessStatus.GATED)}",
            f"not found: {count(lambda a: a.access is AccessStatus.NOT_FOUND)}",
            f"errors: {count(lambda a: a.access is AccessStatus.ERROR)}",
            f"truncated: {'yes' if chain.traversal.truncated else 'no'}",
        ]
    )


def _cmd_trace(args: argparse.Namespace) -> int:
    token = os.environ.get(args.token) if args.token else None
    cache = Cache(Path(args.cache)) if args.cache else None
    formats = {f.strip() for f in args.format.split(",") if f.strip()}
    unknown = formats - set(ALL_FORMATS)
    if unknown:
        print(f"filo: unknown format(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return EXIT_USAGE
    try:
        chain, code = run_trace(
            args.ids, HttpxFetcher(), cache=cache, depth=args.depth,
            no_body_scan=args.no_body_scan, token=token, out=args.out,
            formats=formats, spec_version=args.spec_version,
        )
    except ValueError as exc:
        print(f"filo: {exc}", file=sys.stderr)
        return EXIT_USAGE
    print(summarize(chain))
    print(f"\nwrote to {args.out}/ ({', '.join(sorted(formats))})")
    return code


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        doc = json.loads(Path(args.file).read_text())
        validate_bom(doc, args.spec_version)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"filo: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except jsonschema.ValidationError as exc:
        print(f"filo: invalid CycloneDX {args.spec_version}: {exc.message}", file=sys.stderr)
        return EXIT_INCOMPLETE
    print(f"valid CycloneDX {args.spec_version}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(prog="filo")
    sub = parser.add_subparsers(dest="command")

    p_trace = sub.add_parser("trace", help="walk one or more provenance chains")
    p_trace.add_argument("ids", nargs="+", help="artifact ids, e.g. owner/name")
    p_trace.add_argument("--depth", type=int, default=6, help="max traversal depth")
    p_trace.add_argument("--out", default="./out", help="output directory")
    p_trace.add_argument("--format", default=",".join(ALL_FORMATS), help="json,cdx,md,mmd")
    p_trace.add_argument("--spec-version", default="1.6", choices=("1.6", "1.7"))
    p_trace.add_argument("--cache", default=None, help="cache directory")
    p_trace.add_argument("--token", default=None, help="env var holding a read-only HF token")
    p_trace.add_argument("--no-body-scan", action="store_true", help="structured sources only")

    p_val = sub.add_parser("validate", help="validate a CycloneDX BOM file")
    p_val.add_argument("file", help="path to a .cdx.json file")
    p_val.add_argument("--spec-version", default="1.6", choices=("1.6", "1.7"))

    sub.add_parser("version", help="print version")

    args = parser.parse_args(argv)
    if args.command == "version":
        print(f"filo/{__version__}")
        return EXIT_OK
    if args.command == "trace":
        return _cmd_trace(args)
    if args.command == "validate":
        return _cmd_validate(args)
    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
