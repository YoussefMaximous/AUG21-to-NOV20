#!/usr/bin/env python3
"""Merge dukascopy tick CSVs into one file (header written once)."""

import argparse
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    ap.add_argument("inputs", nargs="+")
    args = ap.parse_args()

    header = None
    total = 0
    with open(args.output, "w", newline="", encoding="ascii") as out:
        for path in args.inputs:
            with open(path, "r", newline="", encoding="ascii") as f:
                first = f.readline()
                if not first:
                    continue
                if header is None:
                    header = first
                    out.write(first)
                elif first != header:
                    print(f"header mismatch in {path}", file=sys.stderr)
                    return 2
                for line in f:
                    if line.strip():
                        out.write(line)
                        total += 1
    print(f"merged {len(args.inputs)} files -> {args.output} ({total:,} data rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
