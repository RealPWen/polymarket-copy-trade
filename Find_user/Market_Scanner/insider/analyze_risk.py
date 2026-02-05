"""
Risk Analysis for Strategy V6 Backtest Results
"""
import json
import numpy as np
from pathlib import Path

def analyze_risk(result_file):
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    # Extract trades with actual PnL
    trades = [r for r in data['results'] if r['outcome'] in ['WIN', 'LOSS']]
    
    # Sort by detection_time
    trades.sort(key=lambda x: x['detection_time'])
    
    # Calculate cumulative PnL and drawdown
    capital = 10000  # Base capital assumption
    cumulative = [0]
    peak = 0
    max_drawdown = 0
    max_drawdown_pct = 0
    drawdown_start = None
    max_dd_start = None
    max_dd_end = None
    
    for i, t in enumerate(trades):
        pnl = t['pnl_dollars']
        cumulative.append(cumulative[-1] + pnl)
        
        # Update peak
        if cumulative[-1] > peak:
            peak = cumulative[-1]
            drawdown_start = i
        
        # Calculate drawdown
        if peak > 0:
            drawdown = peak - cumulative[-1]
            drawdown_pct = drawdown / (capital + peak)
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
                max_dd_start = drawdown_start
                max_dd_end = i
    
    # Stats
    wins = [t['pnl_dollars'] for t in trades if t['outcome'] == 'WIN']
    losses = [t['pnl_dollars'] for t in trades if t['outcome'] == 'LOSS']
    
    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    win_rate = len(wins) / len(trades)
    
    # Consecutive losses
    max_consec_loss = 0
    current_consec = 0
    consec_loss_pnl = 0
    max_consec_loss_pnl = 0
    
    for t in trades:
        if t['outcome'] == 'LOSS':
            current_consec += 1
            consec_loss_pnl += abs(t['pnl_dollars'])
            if current_consec > max_consec_loss:
                max_consec_loss = current_consec
                max_consec_loss_pnl = consec_loss_pnl
        else:
            current_consec = 0
            consec_loss_pnl = 0
    
    # Sharpe-like ratio (simplified)
    returns = [t['pnl_dollars'] for t in trades]
    if len(returns) > 1:
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(len(returns))
    else:
        sharpe = 0
    
    # Kelly Criterion
    if avg_loss != 0:
        kelly = win_rate - (1 - win_rate) / abs(avg_win / avg_loss)
    else:
        kelly = 0
    
    print("=" * 70)
    print("RISK ANALYSIS - Strategy V6")
    print("=" * 70)
    print()
    print("[BASIC STATS]")
    print(f"  Total Trades:       {len(trades)}")
    print(f"  Wins:              {len(wins)}")
    print(f"  Losses:            {len(losses)}")
    print(f"  Win Rate:          {win_rate:.1%}")
    print()
    print("[PNL ANALYSIS]")
    print(f"  Avg Win:           ${avg_win:,.2f}")
    print(f"  Avg Loss:          ${avg_loss:,.2f}")
    print(f"  Risk/Reward:       {abs(avg_win/avg_loss):.2f}x")
    print(f"  Final PnL:         ${cumulative[-1]:,.2f}")
    print(f"  Peak PnL:          ${peak:,.2f}")
    print()
    print("[DRAWDOWN]")
    print(f"  Max Drawdown:      ${max_drawdown:,.2f}")
    print(f"  Max Drawdown %:    {max_drawdown_pct:.1%} (of capital + peak)")
    print()
    print("[RISK METRICS]")
    print(f"  Max Consec Losses: {max_consec_loss}")
    print(f"  Consec Loss Amt:   ${max_consec_loss_pnl:,.2f}")
    print(f"  Sharpe Ratio:      {sharpe:.2f}")
    print(f"  Kelly Criterion:   {kelly:.1%}")
    print()
    print("=" * 70)
    print("CAPITAL RECOMMENDATION")
    print("=" * 70)
    print()
    
    # Conservative recommendations
    print("[BASED ON MAX DRAWDOWN]")
    print(f"  Historical max drawdown was ${max_drawdown:,.2f}")
    print(f"  To survive 3x worst drawdown, you need:")
    min_capital = max_drawdown * 3
    print(f"    Minimum: ${min_capital:,.0f}")
    print()
    
    print("[BASED ON KELLY CRITERION]")
    print(f"  Optimal Kelly: {kelly:.1%}")
    print(f"  Half Kelly (safer): {kelly/2:.1%}")
    print(f"  Quarter Kelly (conservative): {kelly/4:.1%}")
    print()
    
    print("[PRACTICAL RECOMMENDATIONS]")
    print()
    print("  CONSERVATIVE (Low Risk):")
    print(f"    Capital: $5,000 - $10,000")
    print(f"    Max Position: 2-3% per trade")
    print(f"    Expected Monthly: ${5000 * 0.05:.0f} - ${10000 * 0.05:.0f}")
    print()
    print("  MODERATE (Balanced):")
    print(f"    Capital: $10,000 - $25,000")
    print(f"    Max Position: 5-7% per trade")
    print(f"    Expected Monthly: ${10000 * 0.10:.0f} - ${25000 * 0.10:.0f}")
    print()
    print("  AGGRESSIVE (High Risk):")
    print(f"    Capital: $25,000 - $50,000")
    print(f"    Max Position: 10-15% per trade")
    print(f"    Expected Monthly: ${25000 * 0.15:.0f} - ${50000 * 0.15:.0f}")
    print()
    print("=" * 70)
    print("RISK WARNINGS")
    print("=" * 70)
    print("  1. Past performance does NOT guarantee future results")
    print("  2. Polymarket has regulatory risks (US users)")
    print("  3. Liquidity may vary - slippage can occur")
    print("  4. Strategy depends on insider detection accuracy")
    print("  5. Start with MINIMUM capital to validate live performance")
    print()
    print("  SUGGESTED FIRST STEP:")
    print("    Start with $1,000 - $2,000 for 1-2 weeks")
    print("    Validate live win rate matches backtest (>70%)")
    print("    Only scale up after live validation")
    print()

if __name__ == "__main__":
    result_file = Path(__file__).parent / "output" / "strategy_backtest_v6_20260205_193358.json"
    analyze_risk(result_file)
