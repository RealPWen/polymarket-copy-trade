# Goldsky Crawler

Tools for fetching and processing Polymarket trade data from the Goldsky subgraph.

## Scripts

### update_archive.py

Main script to update the local archive with Polymarket trade data.

```powershell
# Full update (goldsky + markets + process + split)
python update_archive.py

# Show current data status
python update_archive.py --status

# Individual steps
python update_archive.py --goldsky    # Only update goldsky events
python update_archive.py --markets    # Only update markets metadata
python update_archive.py --process    # Only process goldsky to trades
python update_archive.py --split-only # Only split trades to market files
```

### query_wallet.py

Query recent trades for a specific wallet address.

```powershell
# Query wallet trades
python query_wallet.py 0x6022a1784a55b8070de42d19484bbff95fa7c60a

# With options
python query_wallet.py 0x... -n 10 -o output.json
```

## Data Directory

Data is stored in the sibling `archive/` folder:

```
archive/
├── goldsky/                 # Raw order events from Goldsky subgraph
│   └── orderFilled.csv      # ~39GB, all order fill events
├── processed/               # Processed trade data
│   └── trades.csv           # ~35GB, structured trades
├── market_trades/           # Per-market trade files (1500+ files)
│   └── market_XXXXX.csv     # Individual market trades
└── markets.csv              # Market metadata (50MB)
```

## Data Sources

| Source | Latency | Use Case |
|--------|---------|----------|
| Goldsky Subgraph | < 1 min | Historical data, real-time monitoring |
| Polymarket Gamma API | ~1 min | Market metadata |

## Requirements

```powershell
pip install polars requests gql flatten-json pandas
```
