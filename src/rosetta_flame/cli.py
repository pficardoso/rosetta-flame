"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from rosetta_flame import __version__
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "seed" and args.target == "topics":
        return _seed_topics(args)
    print("Rosetta Flame is ready.")
    return 0
