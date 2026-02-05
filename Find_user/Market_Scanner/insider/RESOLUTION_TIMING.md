# 市场结束时间检测问题 - 解决方案总结

## 问题
在实盘交易时，Polymarket 的 `endDate` 字段不可靠：
- 它只是**交易窗口关闭**的最后期限
- 实际事件可能**提前数天**发生并导致市场 resolve
- 有些市场甚至延迟 resolve

## 数据验证
分析 100 个已解决的市场：
- **14%** 在 endDate **之前 >24h** 就关闭了（最多提前 21 天）
- **7%** 在 endDate **之后 >24h** 才关闭
- 仅 **79%** 在 endDate 附近关闭

## 解决方案：多信号检测

### 1. 价格收敛检测（最可靠）
```python
# 当价格接近极端值时，市场可能即将 resolve
if yes_price > 0.90:
    # YES 结果很可能，可能即将 resolve
elif yes_price < 0.10:
    # NO 结果很可能，可能即将 resolve
```

### 2. 交易状态监控
```python
# acceptingOrders = False 意味着市场即将/已经 resolve
if not market.get('acceptingOrders'):
    # 停止交易，resolution imminent
```

### 3. 内幕交易信号（我们的策略核心）
- 监控大额定向交易
- 当检测到内幕信号时，说明有人知道结果即将出现
- **这本身就是一个 resolution 信号**

### 4. 实时监控策略（推荐）

```python
def should_enter_trade(market, insider_signals):
    """
    判断是否应该入场
    
    条件组合：
    1. 价格在 30-70% 范围内（还有利润空间）
    2. 检测到内幕交易信号
    3. acceptingOrders = True
    4. 可选：在 endDate 的合理窗口内
    """
    price = market['yes_price']
    
    # 必须还有利润空间
    if price > 0.85 or price < 0.15:
        return False, "Price too converged, limited profit"
    
    # 必须还在交易
    if not market.get('acceptingOrders'):
        return False, "Not accepting orders"
    
    # 必须检测到内幕信号
    if not insider_signals.get('detected'):
        return False, "No insider signal"
    
    # 入场！
    return True, f"Entry signal: {insider_signals['direction']}"
```

## 关键洞察

**内幕交易者的行为就是最好的 "resolution 时间" 指标：**
- 当他们开始大量买入某个方向时，说明他们知道结果即将出现
- 我们不需要预测"什么时候结束"，我们只需要跟随内幕信号

## 测试脚本

已创建以下测试脚本：
1. `test_enddate_reliability.py` - 验证 endDate 不可靠
2. `test_price_convergence.py` - 价格收敛检测
3. `test_market_resolution.py` - 综合市场时间分析
4. **`test_giannis_live.py`** - 实盘模拟测试（使用 Goldsky API）

## 实盘应用示例

```python
from insider_analyzer import InsiderDirectionAnalyzer, AnalysisConfig
from datetime import datetime

# 实盘中：用当前时间作为分析截止点（不是 closedTime）
now = datetime.utcnow()

analyzer = InsiderDirectionAnalyzer(AnalysisConfig(
    min_insider_score=0.3,
    lookback_days=30
))

analysis = analyzer.analyze_market(
    trades_df,
    closed_time=now,  # 关键：使用当前时间
    return_daily=True
)

if analysis.get("predicted") != "NEUTRAL":
    if abs(analysis.get("direction_score", 0)) > 0.20:
        print(f"Insider signal: {analysis['predicted']}")
```

## 监控策略

1. 每小时运行一次 `test_giannis_live.py`
2. 当 `direction_score` 突然变大时，说明内幕交易者开始行动
3. 这就是入场信号！
