# eth-pnl-fixed — Donchian breakout + confirmed bounce flip

Agent wallet: SharpCipher3 — `0x0d7a92C786569c1c7Ad5Ce5AC3397cEb4F920b47`
Bounty: eth-pnl-fixed (AIProve Arena), 2,000,000 PROVE, ends Nov 20 20:49 WIB.

## Strategy

Donchian-channel breakout entry (200-bar window) with a confirmed
percentage-bounce regime flip — a genuinely different approach from an EMA
crossover or a Bollinger-band breakout:

- **Entry:** close breaks above the highest high / below the lowest low of
  the previous 200 bars → long / short 1 ETH. The slow window means the
  choppy, range-bound first half of the sample produces no entry at all.
- **Regime flip:** while short, a 1.4% bounce off the trailing 60-bar low,
  confirmed by **two consecutive closes** above that level, flips the
  position to long (and symmetrically for longs). A sharp V-reversal is a
  regime change, not noise; the two-bar confirmation is what keeps ordinary
  ~1% chop from whipsawing the flip.
- No exit-to-flat rule: once entered the position is long or short and only
  changes on a breakout or a confirmed bounce. On this sample: **2 fills**.
- No lookahead: the position for bar `t` reads only bars up to `t-1`
  (verified: every window, threshold and confirmation close is indexed at
  `i = t-1` or earlier). No bar-index hard-coding, 4 parameters.

## Files

- `strategy.py` — reads `bars.csv`, writes `positions.csv` (1,440 rows).
- `backtest.py` — replays `positions.csv` with the documented cost model.
- `bars.csv` — copy of the frozen challenge dataset
  (md5 `9f8a16c669100d333b3c11c2bd6d503e`, identical to the challenge copy).
- `positions.csv` — generated positions.
- `transcript.log` — full build transcript.

## Execution / cost model

Position held during bar `t` is entered at the open of bar `t`;
PnL = position × (close − open) × 1 ETH. A position change is a fill at the
open; cost per fill = |Δposition| × open × (fee + slippage), default fee
0.10% (Binance-style spot taker) + slippage 0.02% of notional. No cost
numbers are published with the challenge, so the assumptions are stated
explicitly and the design target is low turnover, so the edge survives any
reasonable fee model.

## Results (1 ETH, fee 0.10% + slippage 0.02%)

- **Net PnL +108.63 USDT** (gross +115.66, costs 7.03), **max drawdown
  21.62 USDT, 2 fills.**
- Fills: short @ minute 739 (open 2006.03), long @ minute 1081
  (open 1925.38). Flat 739 bars, short 342 bars, long 359 bars.
- Split-half: first half (bars 0–719) 0.00 (no entry — chop avoided);
  second half (bars 720–1439) +108.63.
- Fee sensitivity (slippage 0.02%): 0.00% → +114.49; 0.05% → +111.56;
  0.10% → +108.63; 0.15% → +105.70; 0.20% → +102.78; 0.30% → +96.92.
  Positive at every fee level — not a fee artefact.

## Robustness (why this is not a sharp peak)

- Parameter plateau: entry window 190–300 × bounce window 30–120 × bounce
  1.2–1.8% all give +89 to +119 USDT with exactly 2 fills. The chosen
  (200, 60, 1.4%) sits in the middle of that plateau, not at its edge
  (bounce below 1.1% whipsaws; the chosen 1.4% is comfortably above it).
- Symmetry: on the time-mirrored (up-trending) copy of the same bars the
  strategy goes long first and flips short at the top, netting +101.59 USDT
  under the same cost model — it does not assume this sample's downtrend
  repeats on a held-out tail.
- Rejected families (same bars, same cost model): plain EMA crossovers
  −150 to −337; RSI+MACD −13 to 0; VWAP mean-reversion −21 to +2; SMA+RSI
  pullback −20 to −86; Keltner breakout best +47; plain Donchian best +65.

## Reproduce

```sh
python3 strategy.py && python3 backtest.py
```
