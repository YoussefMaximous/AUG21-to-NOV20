# XAUUSD tick data — 2026-08-21 → 2026-11-20 (3 months)

Real tick history for **XAUUSD (spot gold)** plus native **MetaTrader 4** history
built from it. Ready to download as ZIP, open, and use.

---

## 1. Where the ticks come from

| | |
|---|---|
| Source | **Dukascopy Bank SA** public tick datafeed (`datafeed.dukascopy.com`) |
| Pulled with | [dukascopy-node](https://github.com/Leo4815162342/dukascopy-node) |
| Instrument | `xauusd` — Gold vs US Dollar |
| Timeframe | raw ticks (`-t tick`) |
| Range | **2026-08-21 00:00:00 UTC → 2026-11-20 23:59:59.999 UTC** |
| Ticks | **23,532,983** |
| Trading days | **66** (63 full, 3 partial — see below) |
| Price range | 3502.690 – 4696.635 |
| Daily files | **79** (UTC days, incl. 13 Sunday opens) |

Exact command used (pulled in 3 monthly chunks because the feed drops long runs):

```bash
npx dukascopy-node -i xauusd -from 2026-08-21 -to 2026-09-21 -t tick -f csv -v
npx dukascopy-node -i xauusd -from 2026-09-21 -to 2026-10-21 -t tick -f csv -v
npx dukascopy-node -i xauusd -from 2026-10-21 -to 2026-11-21 -t tick -f csv -v
```

`-to` is exclusive, so `2026-11-21` means "through the end of 20 Nov".

> **Naming note:** Dukascopy has no `XASUUSD` symbol. Their gold instrument is
> `xauusd`; silver is `xagusd`. This repo is gold.

Partial days, explained:

| Day | Bars | Why |
|---|---:|---|
| 2026-08-21 | 1,260 | dataset starts at 00:00 UTC, so the first 2 h are absent |
| 2026-09-07 | 1,229 | US Labor Day, shortened gold session |
| 2026-10-01 | 1,379 | one minute with no ticks |

Every other trading day has the full **1,380** M1 bars. No Saturdays;
Sundays appear only from the 22:00 UTC open.

---

## 2. Tick files — `data/`

One CSV per UTC day (79 files, ~0.7–38 MB each):

```
timestamp,askPrice,bidPrice,askVolume,bidVolume
1793232000110,4055.005,4054.425,0.00012,0.00012
```

| Column | Meaning |
|---|---|
| `timestamp` | Unix epoch **milliseconds, UTC** |
| `askPrice` | ask quote |
| `bidPrice` | bid quote |
| `askVolume` / `bidVolume` | Dukascopy volume, in millions of units |

Sunday files are small because the market only opens in the evening
(e.g. 2026-11-01 has 15,983 ticks). Saturday files do not exist.

---

## 3. MT4 files — `mt4/`

**MT4 has no free-standing tick database.** Charts and the Strategy Tester read
**M1 bars** (`.hst`), and "Every tick" mode *synthesises* ticks from those M1
bars. So the ticks were aggregated into MT4's native v400 `.hst` container —
this is exactly what IC Markets MT4 loads.

| Folder | Decimals | Use it when |
|---|---|---|
| `mt4/2-decimals-icmarkets/` | 2 (e.g. `4054.43`) | **IC Markets XAUUSD** (default choice) |
| `mt4/3-decimals-dukascopy/` | 3 (e.g. `4054.425`) | brokers that quote gold with 3 decimals |

Each folder contains:

| File | What it is |
|---|---|
| `XAUUSD1.hst` | MT4 v400 M1 history — **90,808 bars**, 148-byte header + 44-byte bars |
| `XAUUSD_M1.csv` | same bars as `YYYY.MM.DD,HH:MM,O,H,L,C,V` for History Center import |
| `report.txt` | counts, price range, file-size check, bars per day |

### The decimals (not "digits") issue — read this

- Dukascopy quotes gold with **3 decimals** (`4054.425`).
- IC Markets quotes XAUUSD with **2 decimals** (`4054.43`).

MT4 prices are doubles, so the extra decimal does not break anything, but the
HST header records the precision and the chart axis follows it. For IC, use the
**2-decimal** build so the chart matches the platform and prices align with
IC quotes. Rounding moves a price by at most **0.005**, which is irrelevant at
gold prices around 3,500–4,700.

The converter flag is `--digits` (the MT4 field is literally named "digits";
here it means **decimal places**):

```bash
python tools/convert_to_mt4.py data.csv --symbol XAUUSD --digits 2 --server-tz icmarkets
```

The 2-decimal HST changes the header precision and the CSV text; the stored
double values keep full tick precision (difference ≤ 0.005).

### Time zone and DST — important for this range

MT4 stores server time, not UTC. IC Markets runs **GMT+3 in summer** and
**GMT+2 in winter**. This 3-month range crosses the EU DST switch:

| Period (UTC) | IC server time |
|---|---|
| 2026-08-21 → 2026-10-25 01:00 | **GMT+3** |
| 2026-10-25 01:00 → 2026-11-20 | **GMT+2** |

The converter's `--server-tz icmarkets` applies that switch automatically
(EU rule: last Sunday of March/October, 01:00 UTC). The change happens while the
market is closed, so no bars are duplicated or lost. Every day still has 1,380
bars. First bar is **03:00 server on 21 Aug** (00:00 UTC + 3); last is
**23:59 server on 20 Nov**.

If your broker uses another zone, use a fixed offset instead:

```bash
python tools/convert_to_mt4.py data.csv --symbol XAUUSD --digits 2 --offset-hours 3
```

### Install into MT4 (2 minutes)

1. **Close MT4.**
2. MT4 → **File → Open Data Folder**.
3. Open `history\` and find your server folder, e.g. `history\ICMarkets-Live01\`
   (exact name depends on your account).
4. Copy `XAUUSD1.hst` (from the 2-decimal folder) into that server folder.
5. Start MT4 → **Tools → History Center (F2)** → select **XAUUSD** → **Refresh**.
6. Open an XAUUSD M1 chart. Bars start at 03:00 on 21 Aug.

Alternative without copying files: F2 → XAUUSD → **Import** →
`XAUUSD_M1.csv`.

Then in the Strategy Tester: symbol XAUUSD, period M1, model **Every tick**.

### Caveats worth knowing

- **Symbol must already exist** in Market Watch as `XAUUSD`. If your account
  uses a suffix (e.g. `XAUUSD.a`), rename `XAUUSD1.hst` to match, or re-run the
  converter with `--symbol`.
- MT4 may **merge or re-download** server history for the same dates after you
  connect. Imported bars usually survive, but keep a copy of `XAUUSD1.hst`.
- **Spread is not stored** in v400 HST. The tester applies the current/fixed
  spread from its settings, not the historical Dukascopy spread. Both bid and
  ask are in the raw tick CSVs if you need real spread.
- **Volume = tick count** per M1 bar, the standard MT4 meaning.
- "Every tick" is still **M1-interpolated**, not exchange-grade tick replay.
  For true tick-by-tick MT4 tests you need an `.fxt` built by a third-party tool
  (e.g. Tick Data Suite). MT4 itself cannot import raw ticks.
- Sunday bars only exist after the 22:00 UTC open — that is normal.
- 2026-09-07 is short (US Labor Day); that is a real session, not missing data.

---

## 4. Verification

`XAUUSD1.hst` was read back after writing:

- version **400**, symbol `XAUUSD`, period **1** (M1)
- **90,808** bars, no trailing bytes
- file size = 148 + 44 × 90,808 = **3,995,700 bytes** (exact)
- OHLC invariants checked on first, last, and interior bars

Per-file SHA-256 checksums are in [`MANIFEST.md`](MANIFEST.md).

---

## 5. Tools

| Script | Purpose |
|---|---|
| `tools/convert_to_mt4.py` | tick CSV → `.hst` v400 + MT4 import CSV |
| `tools/split_by_day.py` | combined tick CSV → one file per UTC day |
| `tools/merge_csvs.py` | merge chunked downloads into one CSV |

Python 3.9+, no third-party packages.

```bash
python tools/convert_to_mt4.py data.csv \
  --symbol XAUUSD --digits 2 --server-tz icmarkets --outdir out
```

---

## 6. Attribution

Tick data © Dukascopy Bank SA, retrieved via the open-source `dukascopy-node`
client. Provided for personal research and backtesting. Check Dukascopy's terms
before redistributing or using commercially.
