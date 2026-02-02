
import requests
import pandas as pd
import sys

# Setup
WALLET = "0xd82079c0d6b837bad90abf202befc079da5819f6"
DATA_API_BASE = "https://data-api.polymarket.com"
sys.stdout.reconfigure(encoding='utf-8')

def analyze_trading_pattern(wallet):
    report = []
    
    report.append(f"Analyzing trading pattern for {wallet}...")
    
    # 1. Get recent trades
    limit = 1000
    r = requests.get(f"{DATA_API_BASE}/trades", params={"user": wallet, "limit": limit})
    trades = r.json() if r.status_code == 200 else []
    
    if not trades:
        report.append("No trades found.")
    else:
        df = pd.DataFrame(trades)
        if 'asset' not in df.columns:
             report.append("Error: 'asset' column not found in data.")
        else:
            asset_counts = df['asset'].value_counts()
            top_assets = asset_counts.head(3).index.tolist()
            
            report.append(f"\nAnalyzing Top {len(top_assets)} Active Assets (Tokens):")
            
            for asset in top_assets:
                subset = df[df['asset'] == asset]
                
                info = "Unknown"
                if 'outcome' in subset.columns:
                    info = f"{subset.iloc[0].get('slug', 'N/A')} [{subset.iloc[0].get('outcome', '?')}]"
                    
                report.append(f"\n[TOKEN]: {asset[:10]}... ({info})")
                
                buys = subset[subset['side'] == 'BUY']
                sells = subset[subset['side'] == 'SELL']
                
                buy_vol = buys['size'].astype(float).sum()
                sell_vol = sells['size'].astype(float).sum()
                buy_count = len(buys)
                sell_count = len(sells)
                
                net_vol = buy_vol - sell_vol
                total_vol = buy_vol + sell_vol
                
                report.append(f"   - Buys:  {buy_count} trades | Vol: {buy_vol:,.0f}")
                report.append(f"   - Sells: {sell_count} trades | Vol: {sell_vol:,.0f}")
                report.append(f"   - Net Position Change: {net_vol:,.0f}")
                
                if total_vol > 0:
                    ratio = min(buy_vol, sell_vol) / total_vol
                    report.append(f"   - Turnover Ratio: {ratio:.2f}")
                    
                    if ratio > 0.3:
                        report.append("   [WARNING] MM/Scalping Pattern Detected!")
                        report.append("      They are buying and selling frequently. Copying this will lose money to spread.")
                    else:
                        report.append("   [POSITIVE] Accumulation/Dump Pattern")
                        report.append("      They are mostly building or exiting a position. Safe to copy (directionally).")

    with open("final_pattern_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("Report saved to final_pattern_report.txt")

if __name__ == "__main__":
    analyze_trading_pattern(WALLET)
