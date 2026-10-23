"""CodeSniff command line.

    codesniff scan PATH [--format table|json|sarif] [--fail-on clear|borderline|never] [--output FILE]

PATH: a .java file, a folder, a .zip archive or https://github.com/<owner>/<repo>.
Exit codes: 0 = no method at or above the --fail-on zone; 1 = at least one; 2 = usage or input error.
Default --fail-on clear: only methods above the annotated band fail the gate; borderline methods are warnings.
"""
import argparse
import sys

from . import __version__
from .analyze import analyze_path, sort_rows
from .report import to_csv, to_json, to_sarif, to_table
from .zones import ZONE_ORDER


def build_parser():
    p = argparse.ArgumentParser(prog="codesniff", description="Borderline code-smell candidates with context, not verdicts.")
    p.add_argument("--version", action="version", version=f"CodeSniff {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("scan", help="scan a Java file, folder, zip or GitHub repository")
    s.add_argument("path")
    s.add_argument("--format", choices=["table", "json", "sarif", "csv"], default="table")
    s.add_argument("--fail-on", choices=["clear", "borderline", "never"], default="clear")
    s.add_argument("--output", "-o", help="write the report to this file instead of stdout")
    s.add_argument("--max-files", type=int, default=None)
    return p


def gate(rows, fail_on):
    if fail_on == "never":
        return 0
    return int(any(ZONE_ORDER[r["status"]] >= ZONE_ORDER[fail_on] for r in rows))


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        rows, skipped, source = analyze_path(args.path, max_files=args.max_files)
    except (FileNotFoundError, ValueError) as exc:
        print(f"codesniff: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # e.g. git clone failure
        print(f"codesniff: could not scan {args.path}: {exc}", file=sys.stderr)
        return 2
    rows = sort_rows(rows)
    text = {"table": to_table, "sarif": to_sarif, "csv": to_csv}.get(args.format)
    out = text(rows) if text else to_json(rows, source, skipped)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
    else:
        print(out)
    for f, why in skipped:
        print(f"codesniff: skipped {f}: {why}", file=sys.stderr)
    return gate(rows, args.fail_on)


if __name__ == "__main__":
    sys.exit(main())
