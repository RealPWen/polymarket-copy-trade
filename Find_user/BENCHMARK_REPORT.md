
# Polymarket 扫描能力基准测试报告

## 1. 测试环境
- **测试脚本**: `benchmark_scan_capacity.py` (多线程轮询 `get_trades` 接口)
- **测试样本**: 20/50/100 个 Active Markets (按 Volume 排序)
- **运行平台**: Windows (Thread Pool Mode)

## 2. 性能测试数据

| 市场数量 | 并发数(Workers) | 总耗时 (秒) | 每秒处理市场数 (MPS) | 平均 API 响应 (秒) | 平均数据延迟 (秒)* |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **20** | 10 | 1.14s | ~17.5 | 0.52s | ~5400s |
| **50** | 10 | 5.3s | ~9.4 | 0.65s | ~ varies |
| **50** | 20 | 2.5s | ~20.0 | 0.85s | ~ varies |
| **100** | 20 | 5.5s | ~18.2 | 0.95s | ~32000s |

**(注*: 数据延迟数值异常是因为很多“热门”市场的最新一笔成交可能发生在几小时前。Polymarket 的长尾效应很明显，只有 Top 10-20 的市场是秒级成交。)**

#### 核心发现：
1.  **最大吞吐量**: 你的硬件/网络环境下，极限扫描速度约为 **20 个市场/秒** (使用 20 线程)。
2.  **瓶颈**: 主要瓶颈是 **Polymarket Data API 的响应速度** (约 0.5 - 1.0 秒/次) 和 **Rate Limits** (过快会触发 429)。
3.  **循环周期**:
    *   扫描 Top 100 市场: 需要约 **5.5 秒**。
    *   扫描 Top 500 市场 (推算): 需要约 **25-30 秒**。

## 3. 设计建议：如何设计“全量”监听

鉴于每秒只能处理 20 个市场，想做到“毫秒级全量监听”是不现实的（也不必要，因为冷门市场几小时才一笔成交）。

### 推荐架构：分级扫描策略 (Tiered Scanning Strategy)

不要对所有 5000 个市场一视同仁。采用分级队列：

#### **Tier 1: 爆款区 (Top 200)**
- **特征**: 分钟级有成交，Smart Money 最活跃。
- **扫描频率**: 每 **10 秒** 扫描一轮。
- **并发数**: 20 Workers。
- **实现**: 
  ```python
  while True:
      scan(markets[:200])
      sleep(10)
  ```

#### **Tier 2: 观察区 (Top 200-1000)**
- **特征**: 小时级成交。
- **扫描频率**: 每 **5 分钟** 扫描一轮。
- **实现**: 独立的后台 Cron Job。

#### **Tier 3: 僵尸区 (Others)**
- **特征**: 仅有人挂单，几乎无成交。
- **策略**: **不主动扫描**，依靠 WebSocket 的 `tick_size_change` 或 `price_change` (非常轻量) 信号来触发唤醒。

---

## 4. 数据结构与存储方案

为了“找到聪明钱并跟单”，你需要存储两类数据：

### A. 内存中 (Runtime Data Structure)
使用 Python 的 `set` 或 Redis `Set` 来去重：
```python
# 避免重复分析同一个人的同一笔交易
processed_trades_cache = set()  # Store: "{tx_hash}" or "{timestamp}_{wallet}_{amount}"
known_smart_wallets = set()     # Store: "0xABC..."
```

### B. 持久化存储 (Database)
建议使用 **SQLite** (单机足够) 或 **PostgreSQL**。

**表 1: SmartWallets (聪明钱包库)**
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `address` | String (PK) | 钱包地址 |
| `first_seen` | Timestamp | 首次发现时间 |
| `tags` | JSON | `['whale', 'sniper', 'trump-insider']` |
| `sharpe_ratio` | Float | 历史夏普比率 |
| `win_rate` | Float | 胜率 |
| `status` | Enum | `Active`, `Blacklisted`, `Watching` |

**表 2: AlphaSignals (信号记录)**
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | Auto Inc | |
| `wallet` | String (FK) | 关联钱包 |
| `market_question` | String | 市场名称 |
| `side` | String | BUY/SELL |
| `amount_usdc` | Float | 金额 |
| `timestamp` | Timestamp | |

## 5. 过滤规则 (Filters)

在扫描时，直接丢弃以下“噪音”：

1.  **金额过滤**: `Value < $500` USDC 的交易直接忽略（散户噪音）。
2.  **机器人过滤**: 
    *   如果某钱包在 1 秒内对 10 个不同市场下单 -> 标记为 Arb Bot (套利机器人) -> **排除**。
    *   Smart Trader 通常是“单点突破”，而不是“全网撒网”。
3.  **做市商过滤**: 
    *   Data API 有时会返回 `maker` 和 `taker`。重点关注 **Taker** (主动吃单者)。Maker 通常是被动成交。
    
## 6. 结论
你的硬件完全足以支撑 **Top 500 市场的准实时扫描** (30秒延迟内)。无需升级硬件，只需优化代码为**分级轮询**模式即可。
