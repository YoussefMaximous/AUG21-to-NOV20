# XAUUSD tick data — 2026-10-29 → 2026-11-19

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
| Range | **2026-10-29 00:00:00 UTC → 2026-11-19 23:59:59.999 UTC** |
| Ticks | **8,630,538** |
| Trading days | 17 full days + 3 Sunday evening opens |
| Price range | 3590.255 – 4148.578 |
| Broker time used for MT4 export | **UTC+2** (IC Markets server time in winter) |

Exact command used:

```bash
npx dukascopy-node -i xauusd -from 2026-10-29 -to 2026-11-20 -t tick -f csv -v
```

`-to` is exclusive, so `2026-11-20` means "through the end of 19 Nov".

> **Naming note:** Dukascopy has no `XASUUSD` symbol. Their gold instrument is
> `xauusd`; silver is `xagusd`. This repo is gold.

---

## 2. Tick files — `data/`

One CSV per UTC day (19 files, ~16–31 MB each):

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

No Saturday files. Sunday files are small because the market only opens in the
evening (e.g. 2026-11-01 has 15,983 ticks).

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
| `XAUUSD1.hst` | MT4 v400 M1 history — 22,020 bars, 148-byte header + 44-byte bars |
| `XAUUSD_M1.csv` | same bars as `YYYY.MM.DD,HH:MM,O,H,L,C,V` for History Center import |
| `report.txt` | counts, price range, file-size check, bars per day |

### The decimals (not "digits") issue — read this

- Dukascopy quotes gold with **3 decimals** (`4054.425`).
- IC Markets quotes XAUUSD with **2 decimals** (`4054.43`).

MT4 prices are doubles, so the extra decimal does not break anything, but the
HST header records the precision and the chart axis follows it. For IC, use the
**2-decimal** build so the chart matches the platform and prices align with
IC quotes. Rounding moves a price by at most **0.005**, which is irrelevant at
gold prices around 4,000.

The converter takes `--digits` (the MT4 field name is literally "digits", which
is why older docs say digits — it means decimal places here):

```bash
python tools/convert_to_mt4.py data.csv --symbol XAUUSD --digits 2 --offset-hours 2
```

### Time zone

MT4 stores server time, not UTC. IC Markets runs **GMT+2** in winter and
**GMT+3** under DST. EU DST ended 25 Oct 2026, so this whole range is **GMT+2**,
and timestamps were shifted accordingly. Bars therefore run **02:00 → 01:59**
server time. If your broker uses another offset, re-run the converter with
`--offset-hours`.

### Install into MT4 (2 minutes)

1. **Close MT4.**
2. MT4 → **File → Open Data Folder**.
3. Open `history\` and find your server folder, e.g. `history\ICMarkets-Live01\`
   (exact name depends on your account).
4. Copy `XAUUSD1.hst` (from the 2-decimal folder) into that server folder.
5. Start MT4 → **Tools → History Center (F2)** → select **XAUUSD** → **Refresh**.
6. Open an XAUUSD M1 chart. The bars should start at 02:00 on 29 Oct.

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
  spread from the tester settings, not the historical Dukascopy spread. The
  bid and ask are both in the raw tick CSVs if you need real spread.
- **Volume = tick count** per M1 bar, the standard MT4 meaning.
- "Every tick" is still **M1-interpolated**, not exchange-grade tick replay.
  For true tick-by-tick MT4 tests you need an `.fxt` built by a third-party tool
  (e.g. Tick Data Suite). MT4 itself cannot import raw ticks.
- Sunday bars only exist after the 22:00 UTC open — that is normal, not missing data.

---

## 4. Verification

`XAUUSD1.hst` was read back after writing:

- version **400**, symbol `XAUUSD`, period **1** (M1)
- **22,020** bars, no trailing bytes
- file size = 148 + 44 × 22,020 = **969,028 bytes** (exact)
- OHLC invariants checked on first, last, and interior bars

Per-file SHA-256 checksums are in [`MANIFEST.md`](MANIFEST.md).

---

## 5. Tools

| Script | Purpose |
|---|---|
| `tools/convert_to_mt4.py` | tick CSV → `.hst` v400 + MT4 import CSV |
| `tools/split_by_day.py` | combined tick CSV → one file per UTC day |

Python 3.9+, no third-party packages.

```bash
python tools/convert_to_mt4.py data.csv \
  --symbol XAUUSD --digits 2 --offset-hours 2 --outdir out
```

---

## 6. Attribution

Tick data © Dukascopy Bank SA, retrieved via the open-source `dukascopy-node`
client. Provided for personal research and backtesting. Check Dukascopy's terms
before redistributing or using commercially.
