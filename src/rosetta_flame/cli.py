"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
#from dataclasses import asdict
#from pathlib import Path

from rosetta_flame import __version__
from rosetta_flame.core.text_analysis import analyze_text
from rosetta_flame.db import open_database
from rosetta_flame.db.seed import SeedError, SeedReport, import_topics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rosetta-flame",
        description="Rosetta Flame: learn and improve your English.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--db", metavar="PATH", help="database file to use (default: the configured one)"
    )
    commands = parser.add_subparsers(dest="command")
    
    # Seed command
    seed = commands.add_parser("seed", help="load seed data into the database")
    seed_targets = seed.add_subparsers(dest="target", required=True)
    seed_topics = seed_targets.add_parser(
        "topics", help="create or update the Topics from the packaged topic seed"
    )
    seed_topics.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the seed and show what would change, without writing",
    )
    
    # Analyze command
    analyze = commands.add_parser(
        "analyze", help="analyze a text and suggest Weak Spots and related Topics"
    )
    analyze.add_argument("file", nargs="?", help="text file to analyze, or - to read stdin")
    analyze.add_argument("-t", "--text", help="text to analyze, instead of a file")
    analyze.add_argument(
        "-f",
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    return parser


def _print_report(report: SeedReport) -> None:
    verb = "would be" if report.dry_run else "were"
    print(
        f"Topics: {len(report.created)} created, {len(report.updated)} updated, "
        f"{len(report.unchanged)} unchanged"
        + (" (dry run, nothing written)." if report.dry_run else ".")
    )
    if report.updated:
        print(f"Updated {verb}: {', '.join(report.updated)}")
    if report.not_in_seed:
        print(
            f"Kept {len(report.not_in_seed)} Topic(s) that are no longer in the seed: "
            + ", ".join(report.not_in_seed)
        )


def _seed_topics(args: argparse.Namespace) -> int:
    conn = open_database(args.db)
    try:
        report = import_topics(conn, dry_run=args.dry_run)
    except SeedError as error:
        print(error, file=sys.stderr)
        return 1
    finally:
        conn.close()
    _print_report(report)
    return 0


def _analyze_text(args: argparse.Namespace) -> int:
    if args.text:
        text = args.text
    elif args.file:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
    else:
        print("No text provided for analysis.", file=sys.stderr)
        return 1

    report = analyze_text(text)
    if args.format == "json":
        import json
        print(json.dumps(report))
    else:
        print(report)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "seed" and args.target == "topics":
        return _seed_topics(args)
    if args.command == "analyze":
        return _analyze_text(args)
    print("Rosetta Flame is ready.")
    return 0
