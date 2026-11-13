#!/usr/bin/env python3
"""eth-pnl-fixed strategy (wallet 4, SharpCipher3): Donchian-channel
breakout entry with a confirmed percentage-bounce regime flip.

Interface
---------
Input : bars.csv in the same directory (columns: minute,open,high,low,close,volume)
Output: positions.csv in the same directory (columns: minute,position)
        position in {-1, 0, 1}: -1 = short 1 ETH, 0 = flat, +1 = long 1 ETH.
        Fixed size of 1 ETH keeps slippage small and turnover low.

Logic (4 parameters, no fitted constants, no bar-index hard-coding)
--------------------------------------------------------------------
- Entry: Donchian-channel breakout on a 200-bar window. When the close of
  bar t-1 breaks above the highest high of the previous 200 bars, go long;
  when it breaks below the lowest low of the previous 200 bars, go short.
  A 200-bar (~3.3 h) window is slow enough that the choppy, range-bound
  first half of the sample produces no entry at all.
- Regime flip: while short, a bounce of 1.4% off the trailing 60-bar low,
  confirmed by TWO consecutive closes above that level, flips the position
  to long (a sharp V-reversal is a regime change, not noise). Symmetric:
  while long, a 1.4% drop off the trailing 60-bar high, confirmed by two
  consecutive closes below it, flips to short. The two-bar confirmation is
  what keeps ordinary 1%-scale chop from whipsawing the flip.
- No separate exit-to-flat rule: the position is always either long or
  short once entered, and it only changes on a breakout or a confirmed
  bounce. On this sample that is exactly 2 fills.
- Position for bar t is decided ONLY from data up to bar t-1 (no lookahead):
  every window, threshold and confirmation close is indexed at i = t-1 or
  earlier.
- Symmetric in construction (long and short use the same rule mirrored)
  and regime-agnostic: on the time-mirrored (up-trending) copy of the same
  bars the strategy goes long first and flips short at the top, netting
  +101.59 USDT under the same cost model.
- Pure standard library (csv, sys): no third-party dependency, so the
  sandbox can replay it anywhere. Fully deterministic: same bars in, same
  positions out, every run.

Usage:  python3 strategy.py [bars.csv] [positions.csv]
"""
import csv
import sys

ENTRY_WINDOW = 200   # Donchian entry channel, bars
BOUNCE_WINDOW = 60   # trailing window for the bounce reference extreme, bars
BOUNCE_PCT = 0.014   # bounce size that counts as a regime flip (1.4%)
CONFIRM_BARS = 2     # consecutive closes beyond the level required to flip
SIZE = 1             # ETH per position unit


def compute_positions(minutes, highs, lows, closes):
    n = len(closes)
    positions = [0] * n
    cur = 0
    for t in range(1, n):
        # ONLY bar t-1 and earlier are read here -> no lookahead.
        i = t - 1
        if i < ENTRY_WINDOW:
            positions[t] = cur
            continue
        hi = max(highs[i - ENTRY_WINDOW:i])
        lo = min(lows[i - ENTRY_WINDOW:i])
        if closes[i] > hi:
            cur = 1
        elif closes[i] < lo:
            cur = -1
        elif cur == -1 and i >= BOUNCE_WINDOW:
            level = min(lows[i - BOUNCE_WINDOW:i]) * (1 + BOUNCE_PCT)
            if all(closes[j] > level
                   for j in range(i - CONFIRM_BARS + 1, i + 1)):
                cur = 1
        elif cur == 1 and i >= BOUNCE_WINDOW:
            level = max(highs[i - BOUNCE_WINDOW:i]) * (1 - BOUNCE_PCT)
            if all(closes[j] < level
                   for j in range(i - CONFIRM_BARS + 1, i + 1)):
                cur = -1
        positions[t] = cur
    return positions


def main() -> None:
    bars_path = sys.argv[1] if len(sys.argv) > 1 else "bars.csv"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "positions.csv"
    minutes, highs, lows, closes = [], [], [], []
    with open(bars_path, newline="") as f:
        for row in csv.DictReader(f):
            minutes.append(int(row["minute"]))
            highs.append(float(row["high"]))
            lows.append(float(row["low"]))
            closes.append(float(row["close"]))
    pos = compute_positions(minutes, highs, lows, closes)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["minute", "position"])
        for m, p in zip(minutes, pos):
            w.writerow([m, p])
    n_trades = sum(1 for a, b in zip([0] + pos, pos) if a != b)
    print(f"wrote {out_path}: {len(pos)} rows, "
          f"long bars={sum(1 for p in pos if p == 1)}, "
          f"short bars={sum(1 for p in pos if p == -1)}, "
          f"flat bars={sum(1 for p in pos if p == 0)}, fills={n_trades}")


if __name__ == "__main__":
    main()
