"""Command-line entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from rosetta_flame import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rosetta-flame",
        description="Rosetta Flame: learn and improve your English.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    print("Rosetta Flame is ready.")
    return 0
