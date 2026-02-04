# Insider Trading Strategy - Last Hour Detection

## Strategy Overview

This strategy detects insider trading activity in the final hours before market close, when informed traders are most likely to act with high conviction.

## Key Findings

### Backtest Results (326 markets, $100K+ volume)

| Metric | Value |
|--------|-------|
| **Win Rate** | 95.59% (65/68) |
| **ROI** | +93.06% |
| **P-value** | 1.78 × 10⁻¹⁶ (extremely significant) |
| **Total PnL** | +$54,896.25 |

## Strategy Logic

### Entry Conditions

1. **Timing**: Analyze 1 hour before market close
2. **Insider Signal**: `direction_score >= 0.30` (30% threshold)
3. **Price Filter**: `sim_price <= 0.70` (only enter when odds are reasonable)

### Signal Calculation

The insider direction score is calculated using:
- **Time-weighted average**: Recent days get higher weight
  - Last day: 3x weight
  - Days 2-3: 2x weight
  - Days 4-7: 1.5x weight
  - Older days: 1x weight
- **Last-day burst detection**: If last day has extreme signal (>0.5 score, >=5 insiders), blend with overall

### Why It Works

1. **Information asymmetry**: Insiders know the outcome before the public
2. **Last-minute action**: They act close to resolution to maximize profit
3. **Price filter**: We only enter when market hasn't fully priced in the information
4. **High conviction trades**: Score threshold (0.30) filters out noise

## Usage

### Backtest

```bash
# Test on 1000 markets, 1 hour before close, score >= 0.30
python strategy_backtest_v3.py --target 1000 --threads 8 --hours 1 --volume 100000 --score 0.30
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--hours` | 1.0 | Hours before close to simulate entry |
| `--days` | None | Days before close (alternative to hours) |
| `--score` | 0.15 | Minimum direction score threshold |
| `--volume` | 100000 | Minimum market volume |
| `--target` | 200 | Target number of results |
| `--threads` | 8 | Number of parallel threads |

## Files

- `insider_analyzer.py`: Core analysis logic with time-weighted signals
- `trading_strategy.py`: Entry price and position sizing calculations
- `strategy_backtest_v3.py`: Multi-threaded backtest runner
- `data_extractor.py`: Market data loading and caching

## Limitations

1. **Hindsight bias**: Backtest uses closed markets, real-time detection is harder
2. **Liquidity**: May not be able to execute at simulated prices
3. **Market type**: Works best on sports/events with sudden outcomes

## Next Steps

1. Implement real-time scanner for live markets
2. Add alerts for high-confidence signals
3. Test with different time windows (2h, 6h, 12h)
