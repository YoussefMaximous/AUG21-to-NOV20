#!/usr/bin/env python3
"""
Dukascopy tick CSV  ->  MetaTrader 4 M1 history (.hst v400) + import CSV.

Input (dukascopy-node -t tick -f csv -v):
    timestamp,askPrice,bidPrice,askVolume,bidVolume
    1793232000110,4055.005,4054.425,0.00012,0.00012
    timestamp = Unix epoch milliseconds, UTC

Outputs (default outdir "mt4_export"):
    XAUUSD1.hst        MT4 v400 M1 history: 148-byte header + 44-byte bars
    XAUUSD_M1.csv      MT4 History Center import CSV: YYYY.MM.DD,HH:MM,O,H,L,C,V
    XAUUSD_ticks.csv   flat tick CSV in server time (for TDS / tick-based tools)
    report.txt         sanity report

MT4 has no free-standing tick database: charts and the tester consume M1 bars
(.hst), and "Every tick" mode synthesizes ticks from them. This produces that
native M1 history from the real Dukascopy ticks.
"""

import argparse
import csv
import os
import struct
import sys
from datetime import datetime, timezone, timedelta

HST_VERSION = 400
HST_HEADER_SIZE = 148
HST_RECORD_SIZE = 44
MIN_MS = 60000


def build_hst_header(symbol: str, period: int, digits: int, last_sync: int) -> bytes:
    copyright_txt = b"Copyright 2001, MetaQuotes Software Corp."
    hdr = struct.pack("<i", HST_VERSION)
    hdr += copyright_txt[:64].ljust(64, b"\x00")
    hdr += symbol.encode("ascii", "replace")[:12].ljust(12, b"\x00")
    hdr += struct.pack("<i", period)
    hdr += struct.pack("<i", digits)
    hdr += struct.pack("<i", 0)              # time sign
    hdr += struct.pack("<i", int(last_sync))
    hdr += struct.pack("<13i", *([0] * 13))
    if len(hdr) != HST_HEADER_SIZE:
        raise RuntimeError(f"header size {len(hdr)} != {HST_HEADER_SIZE}")
    return hdr


def build_hst_bar(ctm: int, o: float, l: float, h: float, c: float, v: float) -> bytes:
    # MT4 order is ctm, open, low, high, close, volume
    return struct.pack("<i5d", int(ctm), o, l, h, c, v)


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert Dukascopy tick CSV to MT4 M1 HST/CSV.")
    ap.add_argument("input")
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--digits", type=int, default=3)
    ap.add_argument("--offset-hours", type=float, default=2.0,
                    help="hours added to UTC = broker server time (IC Markets winter = 2, summer = 3)")
    ap.add_argument("--outdir", default="mt4_export")
    ap.add_argument("--price", choices=["bid", "ask"], default="bid")
    ap.add_argument("--no-ticks-csv", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 2

    os.makedirs(args.outdir, exist_ok=True)
    offset_ms = int(args.offset_hours * 3600 * 1000)

    hst_path = os.path.join(args.outdir, f"{args.symbol}1.hst")
    m1_path = os.path.join(args.outdir, f"{args.symbol}_M1.csv")
    ticks_path = os.path.join(args.outdir, f"{args.symbol}_ticks.csv")
    report_path = os.path.join(args.outdir, "report.txt")

    bars = []
    cur_min = None
    o = l = h = c = 0.0
    bar_n = 0
    ticks = 0
    skipped = 0
    out_of_order = 0
    min_ts = max_ts = None
    price_min = price_max = None
    day_counts = {}

    def flush_bar():
        nonlocal bar_n
        bars.append((cur_min // 1000, o, l, h, c, float(bar_n)))
        bar_n = 0

    tick_fh = None
    tick_w = None
    if not args.no_ticks_csv:
        tick_fh = open(ticks_path, "w", newline="", encoding="ascii")
        tick_w = csv.writer(tick_fh, lineterminator="\n")
        tick_w.writerow(["date", "time", "bid", "ask"])

    with open(args.input, "r", newline="") as fin:
        reader = csv.reader(fin)
        first = next(reader, None)
        if not first:
            print("Empty input", file=sys.stderr)
            return 2
        if first[0].strip().isdigit():
            cols = ["timestamp", "askprice", "bidprice", "askvolume", "bidvolume"]
            fin.seek(0)
            reader = csv.reader(fin)
            next(reader)
        else:
            cols = [x.strip().lower() for x in first]
        i_ts = cols.index("timestamp")
        i_bid = cols.index("bidprice")
        i_ask = cols.index("askprice")
        i_px = i_ask if args.price == "ask" else i_bid

        for row in reader:
            if not row:
                continue
            try:
                ts = int(row[i_ts])
                px = float(row[i_px])
            except (ValueError, IndexError):
                skipped += 1
                continue
            if px <= 0:
                skipped += 1
                continue

            ts += offset_ms
            minute = ts - (ts % MIN_MS)

            if cur_min is not None and minute < cur_min:
                out_of_order += 1
                continue

            ticks += 1
            if min_ts is None:
                min_ts = ts
            max_ts = ts
            if price_min is None or px < price_min:
                price_min = px
            if price_max is None or px > price_max:
                price_max = px

            if cur_min is None or minute > cur_min:
                if cur_min is not None:
                    flush_bar()
                cur_min = minute
                o = l = h = c = px
                bar_n = 1
            else:
                if px < l:
                    l = px
                if px > h:
                    h = px
                c = px
                bar_n += 1

            if tick_w is not None:
                dt = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).replace(tzinfo=None)
                tick_w.writerow([
                    dt.strftime("%Y.%m.%d"),
                    dt.strftime("%H:%M:%S.") + f"{ts % 1000:03d}",
                    f"{px:.{args.digits}f}",
                    f"{float(row[i_ask]):.{args.digits}f}" if i_ask < len(row) else "",
                ])

    if cur_min is not None:
        flush_bar()
    if tick_fh is not None:
        tick_fh.close()

    if not bars:
        print("No valid ticks parsed", file=sys.stderr)
        return 1

    bars.sort(key=lambda b: b[0])
    deduped = []
    for b in bars:
        if deduped and b[0] <= deduped[-1][0]:
            continue
        deduped.append(b)
    bars = deduped

    last_ctm = bars[-1][0]
    with open(hst_path, "wb") as fh:
        fh.write(build_hst_header(args.symbol, 1, args.digits, last_ctm))
        for b in bars:
            fh.write(build_hst_bar(*b))

    with open(m1_path, "w", newline="", encoding="ascii") as fh:
        w = csv.writer(fh, lineterminator="\n")
        for ctm, bo, bl, bh, bc, bv in bars:
            dt = datetime.fromtimestamp(ctm, tz=timezone.utc).replace(tzinfo=None)
            w.writerow([
                dt.strftime("%Y.%m.%d"),
                dt.strftime("%H:%M"),
                f"{bo:.{args.digits}f}",
                f"{bh:.{args.digits}f}",
                f"{bl:.{args.digits}f}",
                f"{bc:.{args.digits}f}",
                int(bv),
            ])

    # day coverage (server time)
    for ctm, *_ in bars:
        d = datetime.fromtimestamp(ctm, tz=timezone.utc).strftime("%Y-%m-%d")
        day_counts[d] = day_counts.get(d, 0) + 1

    exp_size = HST_HEADER_SIZE + HST_RECORD_SIZE * len(bars)
    act_size = os.path.getsize(hst_path)
    first_dt = datetime.fromtimestamp(bars[0][0], tz=timezone.utc)
    last_dt = datetime.fromtimestamp(bars[-1][0], tz=timezone.utc)

    lines = [
        "MT4 M1 export report",
        "====================",
        f"source            : {os.path.abspath(args.input)}",
        f"symbol            : {args.symbol}",
        f"price side        : {args.price}",
        f"server UTC offset : {args.offset_hours:+.1f} h",
        f"ticks parsed      : {ticks:,}",
        f"rows skipped      : {skipped:,}",
        f"out-of-order      : {out_of_order:,}",
        f"M1 bars           : {len(bars):,}",
        f"first bar (server): {first_dt:%Y-%m-%d %H:%M}",
        f"last bar (server) : {last_dt:%Y-%m-%d %H:%M}",
        f"price range       : {price_min:.{args.digits}f} .. {price_max:.{args.digits}f}",
        f"hst size expected : {exp_size:,} bytes",
        f"hst size actual   : {act_size:,} bytes",
        f"hst size OK       : {'YES' if exp_size == act_size else 'NO'}",
        "",
        "bars per day (server time):",
    ]
    for d in sorted(day_counts):
        lines.append(f"  {d}: {day_counts[d]:,}")
    lines.append("")
    lines.append("Files:")
    for p in filter(None, [hst_path, m1_path, None if args.no_ticks_csv else ticks_path]):
        lines.append(f"  {os.path.abspath(p)}  ({os.path.getsize(p)/1048576:.2f} MB)")

    report = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
