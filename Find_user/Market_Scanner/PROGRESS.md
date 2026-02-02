# Insider Detection Project - Progress Report

## 项目目标
实时检测 Polymarket 市场中的 insider 交易活动，生成方向性信号。

## 当前进度

### 已验证的核心发现

1. **Insider 特征有效** (Trump Win 2024 市场测试)
   - 符合 insider 特征的钱包（burst pattern, high conviction, size anomaly）
   - 37/37 天都给出 YES 方向信号
   - 平均 insider direction = +0.692
   - 最终 Trump 胜选 (YES)，预测正确！

2. **方法论比较**
   | 方法 | 描述 | 准确率 |
   |------|------|--------|
   | 累计钱包数量 | 数 insider-like 钱包 | ❌ 错误 |
   | 累计 conviction 金额 | 看总投入金额 | ✅ 5/6 |
   | 增量流向 (每日新钱包) | 每日新钱包方向 | ✅ 30/30 |
   | **Insider Direction** | 只看高分 insider 钱包 | **✅ 37/37** |

3. **关键洞察**
   - 只看**符合 insider 特征**的钱包方向，信号更稳定
   - Insider 特征: 时间集中 (burst)、大单异常、高定向性

### 待验证

- [ ] 多市场随机验证（证明不是运气）
- [ ] 实时监控实现
- [ ] 交易策略回测（含入场价、仓位等）

---

## 核心代码文件 (清理后)

```
Market_Scanner/
├── PROGRESS.md          # 本文件 - 进度记录
├── BACKTEST_REPORT.md   # 回测报告
├── README.md            # 项目说明
│
├── insider_direction.py       # ⭐ 主要分析脚本 (insider评分 + 方向)
├── insider_finder.py          # 基础 insider 评分逻辑
├── historical_backtest_v2.py  # 历史回测框架
├── smart_money_detector.py    # Conviction 加权分析
├── spike_detector.py          # 增量流向分析
├── directional_detector.py    # 方向性检测
│
├── batch_validation.py        # 批量验证 (待完善)
├── random_validation.py       # 随机市场验证 (待完善)
│
├── archive/                   # 历史数据
│   ├── goldsky/orderFilled.csv (39GB) - 完整交易数据
│   └── markets.csv (52MB) - 市场元数据
│
├── output/                    # 分析结果
│   ├── trump_win_trades_oct_nov.csv (1GB)
│   └── insider_direction.json
│
└── deprecated/                # 已清理的调试/测试脚本 (54个)
```

---

## 数据文件说明

### archive/
- `goldsky/orderFilled.csv` (39GB) - **完整原始交易数据**
- `markets.csv` (52MB) - 市场元数据
- `processed/trades.csv` (34GB) - 处理后格式（含 market_id）

### output/
- `trump_win_trades_oct_nov.csv` (1GB) - Trump 市场 10-11月交易
- `all_trades_election_day.csv` (246MB) - 选举日交易
- `insider_direction.json` - 分析结果

---

## 下一步

1. **多市场验证** - 需要解决的问题：
   - goldsky 数据没有 market_id 列，需要通过 asset_id 关联
   - 缺少市场结算结果（需从 API 获取或从最后价格推断）

2. **实时监控** - 基于 `insider_direction.py` 逻辑实现

---

*Report generated: 2026-02-02*
