# XAUUSD & XAGUSD tick data — 2026-08-21 → 2026-11-20 (3 months)

Real tick history for **spot gold (XAUUSD)** and **spot silver (XAGUSD)**, plus
native **MetaTrader 4** history built from them. Ready to download as ZIP, open,
and use.

---

## 1. What's inside

| | XAUUSD (gold) | XAGUSD (silver) |
|---|---|---|
| Ticks | **23,532,983** | **15,507,761** |
| CSV size | 1,075.5 MB | 589.6 MB |
| Daily files | 79 | 79 |
| Price range | 3502.690 – 4696.635 | 40.751 – 71.155 |
| M1 bars | 90,808 | 90,586 |
| MT4 decimals | 2 (IC) / 3 (Dukascopy) | 3 |
| HST size | 3,995,700 B | 3,985,932 B |

Both instruments cover **2026-08-21 00:00:00 UTC → 2026-11-20 23:59:59.999 UTC**
(3 months; 21 Nov is a Saturday, so the last ticks are Friday 20 Nov).

---

## 2. Where the ticks come from

| | |
|---|---|
| Source | **Dukascopy Bank SA** public tick datafeed (`datafeed.dukascopy.com`) |
| Pulled with | [dukascopy-node](https://github.com/Leo4815162342/dukascopy-node) |
| Timeframe | raw ticks (`-t tick`) |
| Instruments | `xauusd` (gold), `xagusd` (silver) |

Exact commands (each metal pulled in 3 monthly chunks — the feed drops long runs):

```bash
npx dukascopy-node -i xauusd -from 2026-08-21 -to 2026-09-21 -t tick -f csv -v
npx dukascopy-node -i xauusd -from 2026-09-21 -to 2026-10-21 -t tick -f csv -v
npx dukascopy-node -i xauusd -from 2026-10-21 -to 2026-11-21 -t tick -f csv -v

npx dukascopy-node -i xagusd -from 2026-08-21 -to 2026-09-21 -t tick -f csv -v
npx dukascopy-node -i xagusd -from 2026-09-21 -to 2026-10-21 -t tick -f csv -v
npx dukascopy-node -i xagusd -from 2026-10-21 -to 2026-11-21 -t tick -f csv -v
```

`-to` is exclusive, so `2026-11-21` means "through the end of 20 Nov".

> **Naming note:** Dukascopy has no `XASUUSD` symbol. Gold is `xauusd`, silver is
> `xagusd`.

---

## 3. Tick files — `data/`

```
data/xauusd/2026-08-21.csv ... 2026-11-20.csv   (79 files)
data/xagusd/2026-08-21.csv ... 2026-11-20.csv   (79 files)
```

One CSV per UTC day, identical schema for both metals:

```
timestamp,askPrice,bidPrice,askVolume,bidVolume
1787270400066,68.232,68.185,0.006,0.009
```

| Column | Meaning |
|---|---|
| `timestamp` | Unix epoch **milliseconds, UTC** |
| `askPrice` | ask quote |
| `bidPrice` | bid quote |
| `askVolume` / `bidVolume` | Dukascopy volume, in millions of units |

No Saturday files. Sunday files are small because the market only opens in the
evening. Example: gold 2026-11-01 has 15,983 ticks; silver has similar
Sunday-evening opens.

---

## 4. MT4 files — `mt4/`

**MT4 has no free-standing tick database.** Charts and the Strategy Tester read
**M1 bars** (`.hst`), and "Every tick" mode *synthesises* ticks from those M1
bars. So the ticks were aggregated into MT4's native v400 `.hst` container —
this is exactly what IC Markets MT4 loads.

| Folder | Symbol | Decimals | Use it when |
|---|---|---|---|
| `mt4/xauusd-2-decimals-icmarkets/` | XAUUSD | 2 | **IC Markets gold** (default) |
| `mt4/xauusd-3-decimals-dukascopy/` | XAUUSD | 3 | brokers quoting gold to 3 dp |
| `mt4/xagusd-3-decimals/` | XAGUSD | 3 | **IC Markets silver** and most brokers |

Each folder contains:

| File | What it is |
|---|---|
| `XAUUSD1.hst` / `XAGUSD1.hst` | MT4 v400 M1 history, 148-byte header + 44-byte bars |
| `XAUUSD_M1.csv` / `XAGUSD_M1.csv` | same bars as `YYYY.MM.DD,HH:MM,O,H,L,C,V` |
| `report.txt` | counts, price range, size check, bars per day |

### Decimals — the gold-specific gotcha

- **Gold:** Dukascopy quotes **3 dp** (`4054.425`), IC Markets quotes **2 dp**
  (`4054.43`). Use the 2-decimal build on IC.
- **Silver:** both Dukascopy and IC Markets quote **3 dp** (`68.232`), so there
  is only one silver build.
- MT4 prices are doubles; the HST header records precision and the chart axis
  follows it. Gold rounding to 2 dp moves a price by at most **0.005**,
  irrelevant at ~4,000.
- The flag is `--digits` (MT4's field name; here it means **decimal places**).
- The 2-decimal gold HST changes the header precision and the CSV text; stored
  doubles keep full tick precision (difference ≤ 0.005).

### Time zone and DST — applies to both metals

MT4 stores server time, not UTC. IC Markets runs **GMT+3 in summer** and
**GMT+2 in winter**. This range crosses the EU switch:

| Period (UTC) | IC server time |
|---|---|
| 2026-08-21 → 2026-10-25 01:00 | **GMT+3** |
| 2026-10-25 01:00 → 2026-11-20 | **GMT+2** |

The converter's `--server-tz icmarkets` applies that automatically (EU rule:
last Sunday of March/October, 01:00 UTC). The switch happens while the market is
closed, so no bars are duplicated or lost. First bar is **03:00 server on
21 Aug**; last is **23:59 server on 20 Nov**.

### Install into MT4 (2 minutes per symbol)

1. **Close MT4.**
2. MT4 → **File → Open Data Folder**.
3. Open `history\` and find your server folder, e.g. `history\ICMarkets-Live01\`.
4. Copy the `.hst` files you need there:
   - `XAUUSD1.hst` from `mt4/xauusd-2-decimals-icmarkets/`
   - `XAGUSD1.hst` from `mt4/xagusd-3-decimals/`
5. Start MT4 → **Tools → History Center (F2)** → select each symbol →
   **Refresh**.
6. Open M1 charts. Bars start at 03:00 on 21 Aug.

Alternative without copying files: F2 → symbol → **Import** → its `_M1.csv`.

Then in the Strategy Tester: symbol, period M1, model **Every tick**.

---

## 5. Bar counts — why they differ

| | Gold | Silver |
|---|---|---|
| Full session | 1,380 bars/day | ~1,374 bars/day |
| Reason | 23 h trading | silver has a short daily maintenance break |

- Gold: 1,380 bars on every normal day; 3 partial days (21 Aug dataset start =
  1,260; 7 Sep US Labor Day = 1,229; 1 Oct one empty minute = 1,379).
- Silver: most days 1,370–1,380 because of the daily break; 21 Aug starts at
  1,260; 7 Sep Labor Day is 1,223. That is a real session, not missing data.

---

## 6. Verification

Both HSTs were read back after writing:

| | XAUUSD | XAGUSD |
|---|---|---|
| version / period | 400 / 1 | 400 / 1 |
| bars | 90,808 | 90,586 |
| file size | 3,995,700 B | 3,985,932 B |
| size formula | 148 + 44 × 90,808 | 148 + 44 × 90,586 |
| OHLC invariants | OK | OK |

Per-file SHA-256 checksums are in [`MANIFEST.md`](MANIFEST.md).

---

## 7. Caveats worth knowing

- **Symbol must already exist** in Market Watch as `XAUUSD` / `XAGUSD`. If your
  account uses a suffix (e.g. `XAUUSD.a`), rename the `.hst`, or re-run the
  converter with `--symbol`.
- MT4 may **merge or re-download** server history for the same dates after you
  connect. Imported bars usually survive, but keep a copy of the `.hst` files.
- **Spread is not stored** in v400 HST. The tester applies the current/fixed
  spread from its settings, not the historical Dukascopy spread. Both bid and
  ask are in the raw tick CSVs.
- **Volume = tick count** per M1 bar, the standard MT4 meaning.
- "Every tick" is **M1-interpolated**, not exchange-grade tick replay. True
  tick-by-tick MT4 tests need an `.fxt` built by a third-party tool (e.g. Tick
  Data Suite). MT4 cannot import raw ticks.
- Sunday bars exist only after the 22:00 UTC open — normal.

---

## 8. Tools

| Script | Purpose |
|---|---|
| `tools/convert_to_mt4.py` | tick CSV → `.hst` v400 + MT4 import CSV |
| `tools/split_by_day.py` | combined tick CSV → one file per UTC day |
| `tools/merge_csvs.py` | merge chunked downloads into one CSV |

Python 3.9+, no third-party packages.

```bash
python tools/convert_to_mt4.py data.csv \
  --symbol XAGUSD --digits 3 --server-tz icmarkets --outdir out
```

---

## 9. Attribution

Tick data © Dukascopy Bank SA, retrieved via the open-source `dukascopy-node`
client. Provided for personal research and backtesting. Check Dukascopy's terms
before redistributing or using commercially.
