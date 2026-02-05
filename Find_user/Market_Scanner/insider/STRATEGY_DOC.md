# Insider Trading Strategy

## Strategy Overview

This strategy detects insider trading activity before market close. Insiders with privileged information tend to act with high conviction close to resolution time.

## Latest Results (2025-02-05)

### V3b Backtest (Real-world Simulation with endDate variance)

| Metric | Value |
|--------|-------|
| **Win Rate** | 79.1% (140/177) |
| **ROI** | +65.5% |
| **P-value** | 1.33 × 10⁻¹⁵ (extremely significant) |
| **Total PnL** | +$89,040 |

**Key**: V3b simulates real trading conditions where `closedTime` is unknown. 
Entry is based on `endDate` (API estimate) with ±12h variance.

### V3 Backtest (Ideal conditions using closedTime)

| Metric | Value |
|--------|-------|
| **Win Rate** | 95.6% (65/68) |
| **ROI** | +93.1% |
| **P-value** | 1.78 × 10⁻¹⁶ |

## Strategy Versions

| Version | Description | Speed | Realism |
|---------|-------------|-------|---------|
| V3 | Entry at `closedTime - N hours` | Fast | Low (uses future knowledge) |
| V3b | Entry at `endDate - N hours` (with variance) | Fast | **High** (simulates real trading) |
| V6 | Incremental cache + exponential sampling | Medium | High |

## Strategy Logic

### Entry Conditions

1. **Timing**: Analyze 1 hour before estimated end time
2. **Insider Signal**: `direction_score >= 0.30` (30% threshold)
3. **Price Filter**: `sim_price <= 0.70` (only enter when odds are reasonable)

### Signal Calculation

Time-weighted average of daily insider signals:
- Last day: 3x weight
- Days 2-3: 2x weight  
- Days 4-7: 1.5x weight
- Older days: 1x weight

### Position Sizing (Dynamic)

| Signal Strength | Multiplier | Example Position |
|-----------------|------------|-----------------|
| EXTREME | 3.0x | 15-20% |
| STRONG | 2.0x | 10-15% |
| MODERATE | 1.5x | 7.5-10% |
| WEAK | 1.0x | 5% |

## Usage

### Quick Backtest (Recommended)

```bash
# V3b - Real-world simulation
python strategy_backtest_v3b.py --target 1000 --threads 12 --hours 1 --score 0.30 --variance 12
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--hours` | 1.0 | Hours before end to simulate entry |
| `--score` | 0.15 | Minimum direction score threshold |
| `--variance` | 12.0 | (V3b only) endDate variance in hours |
| `--volume` | 100000 | Minimum market volume |
| `--target` | 200 | Target number of results |
| `--threads` | 8 | Number of parallel threads |

## Core Files

| File | Purpose |
|------|---------|
| `insider_analyzer.py` | Core analysis: detect insiders, calculate direction scores |
| `trading_strategy.py` | Entry price and position sizing calculations |
| `strategy_backtest_v3.py` | Fast backtest (ideal conditions) |
| `strategy_backtest_v3b.py` | **Recommended**: Real-world simulation |
| `strategy_backtest_v6.py` | Optimized: incremental cache + exponential sampling |
| `data_extractor.py` | Market data loading and caching |
| `batch_validation.py` | Batch analysis utilities |

## Key Insights

1. **Strategy is robust**: Even with ±12h timing error, still profitable (79% win rate)
2. **Insider signals persist**: Not just a momentary arbitrage opportunity
3. **Position sizing matters**: Heavy bet on strong signals drives returns
4. **Price protection works**: Rejecting expensive entries prevents losses

## Next Steps

1. [ ] Implement real-time scanner for live markets
2. [ ] Add alerts for high-confidence signals  
3. [ ] Integrate with copy_trader for automated execution
4. [ ] Test V6 with incremental caching for faster multi-scan
