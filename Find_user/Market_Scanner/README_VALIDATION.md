# Insider Direction Validation System

## 模块结构

```
Market_Scanner/
├── data_extractor.py      # 数据提取与缓存
├── insider_analyzer.py    # Insider 分析逻辑
├── batch_validation.py    # 批量验证主程序
├── archive/
│   ├── markets.csv        # 市场元数据
│   ├── processed/
│   │   └── trades.csv     # 35GB 原始交易数据
│   └── market_trades/     # 缓存目录 (自动创建)
│       ├── market_253591.csv
│       ├── market_504603.csv
│       └── ...
└── output/
    └── batch_validation_results.json
```

## 数据流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         batch_validation.py                         │
│                         (主程序入口)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        data_extractor.py                            │
│  1. 检查缓存 (archive/market_trades/market_XXX.csv)                 │
│  2. 如有缓存 → 直接加载                                             │
│  3. 如无缓存 → 从 35GB trades.csv 流式提取 → 保存到缓存             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        insider_analyzer.py                          │
│  1. 按天分组交易 → daily_profiles[date][wallet]                     │
│  2. 计算每个钱包的 insider score                                    │
│  3. 过滤高分钱包 (score >= 80)                                      │
│  4. 计算每日方向信号 (YES/NO/NEUTRAL)                               │
│  5. 汇总得到整体预测                                                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         验证结果                                    │
│  - 对比预测 vs 实际                                                 │
│  - 计算准确率                                                       │
│  - 统计显著性检验                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## 使用方法

### 1. 批量验证随机市场

```bash
# 验证 50 个随机市场
python batch_validation.py --sample 50 --seed 42

# 自定义参数
python batch_validation.py --sample 30 --volume 500000 --score 80 --lookback 30
```

### 2. 验证指定市场

```bash
# 验证特定市场
python batch_validation.py --markets 253591,504603,503303

# Trump 2024 市场
python batch_validation.py --markets 253591
```

### 3. 强制重新提取 (跳过缓存)

```bash
python batch_validation.py --sample 10 --no-cache
```

### 4. 单独提取数据

```bash
# 提取单个市场
python data_extractor.py --market 253591

# 提取多个市场
python data_extractor.py --markets 253591,504603,503303
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--sample` | 50 | 随机采样的市场数量 |
| `--seed` | 42 | 随机种子 (可复现) |
| `--volume` | 100000 | 最小市场交易量 ($) |
| `--score` | 80 | Insider 最低分数阈值 |
| `--lookback` | 30 | 分析结算前多少天的数据 |
| `--markets` | - | 指定市场ID (逗号分隔) |
| `--no-cache` | False | 跳过缓存，强制重新提取 |

## 缓存机制

- 首次提取市场数据后，自动保存到 `archive/market_trades/market_XXX.csv`
- 后续运行直接从缓存加载，速度快 100 倍
- 使用 `--no-cache` 可强制重新提取

## Insider Score 计算

| 组件 | 分数 | 条件 |
|------|------|------|
| **Conviction** | 10-40 | 交易量 $10K-$100K+ |
| **Size Anomaly** | 10-30 | 最大单 / 中位数 > 10-50x |
| **Timing Burst** | 10-30 | 交易集中在 2-12 小时内 |
| **Directional** | 10-20 | 单方向押注 > 70%-90% |

**最高分: ~120**，阈值默认 **80**
