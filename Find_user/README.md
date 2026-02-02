# Polymarket Smart Trader Discovery Engine
> *A high-precision modular engine to identify "Smart Money" on Polymarket.*

## 📌 Overview
This module is designed to identify profitable, consistent, and followable traders on Polymarket. Unlike simple leaderboard scrapers, this engine applies a rigorous **"Funnel Strategy"** to filter out lucky gamblers, market makers, and low-value accounts.

## 🚀 Core Filtering Logic (The Funnel)

We apply a multi-stage funnel to the raw leaderboard data:

### 1. Market Maker Filter
*   **Logic**: Exclude wallets with high volume but low ROI.
*   **Threshold**: High frequency trading with very thin profit margins implies market making or arbitrage bot activity, which is difficult to replicate manually or via copy-trading bots.

### 2. Capital Threshold Filter
*   **Logic**: Exclude "Small Fish".
*   **Threshold**: `Total Profit < $1,000`.
*   **Reason**: We are looking for meaningful signals. Accounts with negligible profits may be testing or just lucky with small bets.

### 3. "One-Hit Wonder" Filter (Luck Detection)
*   **Logic**: Exclude traders who made the majority of their profit from a single lucky bet.
*   **Threshold**: `Max_Single_Trade_Profit / Total_Profit > 90%`.
*   **Reason**: We seek **consistency**. A trader who bet once and won 10k is less valuable than a trader who made 10k over 50 trades.

## 📂 Module Structure

The codebase is modularized for maintainability and scalability:

*   **`main.py`**: The entry point. Orchestrates the flow: Fetch -> Filter -> Report.
*   **`config.py`**: Centralized configuration for thresholds, API limits, and file paths.
*   **`data_handler.py`**: Handles all interactions with Polymarket APIs (Leaderboard & detailed trade history). Includes rate limiting and retries.
*   **`filters.py`**: Contains the pure business logic for the filtering criteria described above.
*   **`utils.py`**: Helper functions for logging, formatting, and file I/O.

## 🛠 Usage

1.  **Install Dependencies** (if needed):
    ```bash
    pip install requests pandas tqdm
    ```

2.  **Run the Discovery Engine**:
    ```bash
    python main.py
    ```

3.  **Check Results**:
    *   The script will output `smart_traders_report.csv` in the `output/` directory.
    *   Top candidates will be printed to the console.

## 📊 Output Data

The final report includes:
*   `rank`: Leaderboard rank.
*   `address`: Wallet address.
*   `profit`: Total profit (PnL).
*   `volume`: Total trading volume.
*   `win_rate`: Calculated win rate.
*   `consistency_score`: (Derived metric).
*   `max_single_win`: The profit of their best single trade.

---
*Developed for the "PolyGlass" Smart Trading Suite.*
