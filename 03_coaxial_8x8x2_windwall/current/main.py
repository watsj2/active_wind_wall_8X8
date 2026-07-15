#!/usr/bin/env python3
"""Entry point for the Coaxial 8x8x2 Windwall system."""

from __future__ import annotations

import argparse
import sys

from coaxial_windwall.gui.app import run_app


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coaxial 8x8x2 Windwall")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Open the GUI briefly and exit with status 0 if it starts.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use simulated output instead of the configured real transport.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    return run_app(
        smoke_test_ms=800 if args.smoke_test else 0,
        use_mock=True if args.mock else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
