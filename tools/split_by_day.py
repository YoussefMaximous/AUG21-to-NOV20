#!/usr/bin/env python3
"""Split a Dukascopy tick CSV into one file per UTC day (GitHub-friendly sizes)."""

import argparse
import csv
import os
import sys
from datetime import datetime, timezone

HEADER = ["timestamp", "askPrice", "bidPrice", "askVolume", "bidVolume"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("outdir")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    handles = {}
    counts = {}
    total = 0

    with open(args.input, "r", newline="") as fin:
        reader = csv.reader(fin)
        header = next(reader)
        if header and header[0].strip().isdigit():
            fin.seek(0)
            reader = csv.reader(fin)
        else:
            header = HEADER

        try:
            for row in reader:
                if not row:
                    continue
                ts = int(row[0])
                day = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")
                fh = handles.get(day)
                if fh is None:
                    fh = open(os.path.join(args.outdir, f"{day}.csv"), "w", newline="", encoding="ascii")
                    handles[day] = fh
                    csv.writer(fh, lineterminator="\n").writerow(header)
                    counts[day] = 0
                csv.writer(fh, lineterminator="\n").writerow(row)
                counts[day] += 1
                total += 1
        finally:
            for fh in handles.values():
                fh.close()

    for day in sorted(counts):
        p = os.path.join(args.outdir, f"{day}.csv")
        print(f"{day}  {counts[day]:>9,} ticks  {os.path.getsize(p)/1048576:6.2f} MB")
    print(f"TOTAL   {total:>9,} ticks  {len(counts)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
