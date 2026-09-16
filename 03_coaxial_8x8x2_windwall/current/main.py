#!/usr/bin/env python3
"""Entry point for the Coaxial 8x8x2 Windwall system."""

from __future__ import annotations

import argparse
import sys

from coaxial_windwall.gui.app import run_app


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coaxial 8x8x2 Windwall")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    parse_args(sys.argv[1:] if argv is None else argv)
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
