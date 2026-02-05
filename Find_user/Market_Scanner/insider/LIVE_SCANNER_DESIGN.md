# 实盘检测系统设计文档

## 系统概述

基于已验证的回测策略（79% Win Rate, +65% ROI），设计一个完整的实盘扫描和交易信号生成系统。

## 核心挑战

| 挑战 | 回测环境 | 实盘环境 | 解决方案 |
|------|----------|----------|----------|
| 结束时间 | 已知 `closedTime` | 只有估计的 `endDate` | V3b 已验证 ±12h 误差仍盈利 |
| 数据延迟 | 无延迟 | Goldsky ~1min | 可接受，内幕信号持续数小时 |
| 胜方 | 事后已知 | 未知 | 策略本身预测方向 |
| 市场发现 | 历史档案 | 需实时获取活跃市场 | Polymarket API |

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIVE SCANNER SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Market     │────▶│   Trade      │────▶│   Insider    │    │
│  │   Discovery  │     │   Fetcher    │     │   Analyzer   │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         │                    │                    ▼             │
│         │                    │           ┌──────────────┐       │
│         │                    │           │   Signal     │       │
│         │                    │           │   Generator  │       │
│         │                    │           └──────────────┘       │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    State Manager                         │   │
│  │  - Active Markets    - Signal History    - Position Tracker│   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Alert System                          │   │
│  │  - Terminal Output   - JSON Log    - (Optional) Webhook  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. Market Discovery (市场发现)

**职责**: 获取所有活跃的、即将结束的市场

**数据源**: Polymarket Gamma API

**过滤条件**:
- `acceptingOrders = True` (还在交易)
- `volume >= 100,000` (足够流动性)
- `endDate` 在未来 1-72 小时内 (即将结束)
- `outcomePrices` 在 0.15 - 0.85 之间 (还有盈利空间)

```python
class MarketDiscovery:
    def get_active_markets(
        self,
        min_volume: float = 100000,
        hours_until_end: Tuple[float, float] = (1, 72),
        price_range: Tuple[float, float] = (0.15, 0.85)
    ) -> List[MarketInfo]
```

### 2. Trade Fetcher (交易获取)

**职责**: 获取市场的实时交易数据

**数据源**: Goldsky Subgraph (延迟 <1min)

**策略**:
1. 首次扫描: 获取最近 30 天交易
2. 增量更新: 只获取上次扫描后的新交易
3. 本地缓存: 减少 API 调用

```python
class TradeFetcher:
    def fetch_recent_trades(
        self,
        market_id: int,
        lookback_days: int = 30
    ) -> pd.DataFrame
    
    def fetch_incremental(
        self,
        market_id: int,
        since_timestamp: int
    ) -> pd.DataFrame
```

### 3. Insider Analyzer (内幕分析)

**职责**: 分析交易数据，检测内幕信号

**复用**: `insider_analyzer.py` 中的 `InsiderDirectionAnalyzer`

**关键改动**: 
- 使用当前时间作为 `closed_time` 参数
- 返回实时信号而非回测结果

```python
class LiveInsiderAnalyzer:
    def analyze_live(
        self,
        trades_df: pd.DataFrame,
        current_time: datetime = None  # 默认 now()
    ) -> AnalysisResult
```

### 4. Signal Generator (信号生成)

**职责**: 综合分析结果，生成交易信号

**复用**: `trading_strategy.py` 中的策略逻辑

**输出**:
```python
@dataclass
class LiveSignal:
    market_id: int
    question: str
    direction: str              # "YES" or "NO"
    direction_score: float      # -1.0 to +1.0
    signal_strength: str        # WEAK/MODERATE/STRONG/EXTREME
    current_price: float        # 当前价格
    max_entry_price: float      # 最高入场价
    recommended_position: float # 建议仓位 %
    hours_until_end: float      # 距离 endDate 的小时数
    insider_count: int          # 检测到的内幕钱包数
    confidence: str             # 置信度说明
```

### 5. State Manager (状态管理)

**职责**: 管理扫描状态，避免重复告警

**存储**:
```json
{
  "last_scan_time": "2026-02-05T09:00:00",
  "active_markets": {
    "12345": {
      "first_seen": "2026-02-05T08:00:00",
      "last_signal": {...},
      "signal_history": [...]
    }
  },
  "alerts_sent": ["12345_YES_STRONG_20260205"]
}
```

### 6. Alert System (告警系统)

**职责**: 输出和通知

**输出渠道**:
1. **Terminal**: 彩色格式化输出
2. **JSON Log**: 详细日志记录
3. **Webhook**: (可选) Discord/Telegram 通知

## 扫描流程

```
每 N 分钟执行一次扫描循环:

1. Market Discovery
   ├─ 从 Polymarket API 获取活跃市场
   └─ 过滤: 流动性、时机、价格

2. 遍历每个市场:
   ├─ 检查本地缓存
   ├─ Fetch 新交易 (Goldsky)
   └─ Run Insider Analysis
   
3. 信号评估:
   ├─ direction_score >= 0.30 → STRONG
   ├─ direction_score >= 0.50 + 5+ days → EXTREME
   └─ 价格 <= max_entry_price → ACTIONABLE

4. 输出:
   ├─ 新信号 → 发送告警
   ├─ 信号增强 → 更新告警
   └─ 信号消失 → 记录警告
```

## 入场条件 (与回测一致)

| 条件 | 阈值 | 说明 |
|------|------|------|
| `direction_score` | >= 0.30 | 信号强度 |
| `current_price` | <= 0.70 | 有盈利空间 |
| `hours_until_end` | 1 - 48 | 不太早也不太晚 |
| `insider_count` | >= 3 | 多个内幕钱包确认 |
| `acceptingOrders` | True | 还能交易 |

## 文件结构

```
insider/
├── LIVE_SCANNER_DESIGN.md     # 本设计文档
├── live_scanner.py            # 主扫描器 (入口)
├── modules/
│   ├── __init__.py
│   ├── market_discovery.py    # 市场发现
│   ├── trade_fetcher.py       # 交易获取 (Goldsky)
│   ├── live_analyzer.py       # 实时分析 (包装 insider_analyzer)
│   ├── signal_generator.py    # 信号生成
│   ├── state_manager.py       # 状态管理
│   └── alert_system.py        # 告警输出
├── insider_analyzer.py        # [现有] 核心分析逻辑
├── trading_strategy.py        # [现有] 策略配置
└── data_extractor.py          # [现有] 数据提取
```

## 运行方式

```powershell
# 单次扫描
python live_scanner.py --once

# 持续运行 (每 15 分钟扫描)
python live_scanner.py --interval 15

# 指定参数
python live_scanner.py --interval 15 --min-volume 100000 --min-score 0.30

# 只监控特定市场
python live_scanner.py --markets 12345,67890 --interval 5
```

## 输出示例

```
================================================================================
LIVE SCANNER - 2026-02-05 09:15:00
================================================================================

[SCAN] Fetching active markets from Polymarket...
[INFO] Found 127 markets matching criteria

[MARKET 1/127] Will Trump win 2024 Election?
  - Hours until end: 23.5h
  - Current YES price: 0.52
  - Fetching trades... 15,432 trades loaded
  
  [SIGNAL] STRONG YES DETECTED!
    - Direction Score: +0.42
    - Signal Strength: STRONG
    - Insider Count: 12
    - Days Consistent: 5
    - Max Entry Price: 0.65
    - Recommended Position: 10%

[MARKET 2/127] Will Giannis play tonight?
  - Hours until end: 5.2h
  - Current YES price: 0.68
  - Fetching trades... 2,341 trades loaded
  
  [SKIP] Weak signal (score: 0.08)

...

================================================================================
SCAN COMPLETE
================================================================================
  Markets Scanned: 127
  Signals Found: 3
  Strong Signals: 1
  Time Elapsed: 4.2 minutes
  
ACTIVE SIGNALS:
  1. [STRONG] Market 12345 - YES @ 0.52 (score: +0.42)
  2. [MODERATE] Market 67890 - NO @ 0.38 (score: -0.28)
  3. [WEAK] Market 11111 - YES @ 0.61 (score: +0.15)
================================================================================
```

## 风险控制

1. **价格保护**: 不在 > 0.70 时入场
2. **时机过滤**: 不在结束前 < 1h 入场 (太晚)
3. **信号确认**: 要求多个内幕钱包
4. **仓位限制**: 单市场最大 20%
5. **市场限制**: 只交易高流动性市场

## 与 Copy Trader 集成

扫描器输出可以直接给 copy_trader 使用:

```python
# live_scanner.py 输出
signal = {
    "market_id": 12345,
    "action": "BUY",
    "outcome": "YES",
    "max_price": 0.65,
    "position_usd": 1000
}

# copy_trader 可以读取并执行
```

## 下一步实现顺序

1. [ ] **Phase 1**: `market_discovery.py` - 市场发现
2. [ ] **Phase 2**: `trade_fetcher.py` - Goldsky 实时获取
3. [ ] **Phase 3**: `live_analyzer.py` - 包装现有分析器
4. [ ] **Phase 4**: `signal_generator.py` - 信号生成
5. [ ] **Phase 5**: `live_scanner.py` - 主入口
6. [ ] **Phase 6**: 测试和优化
7. [ ] **Phase 7**: (可选) Webhook 集成

---

*设计时间: 2026-02-05*
*基于回测结果: V3b 79% Win Rate, +65% ROI*
