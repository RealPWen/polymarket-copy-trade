# Polymarket 数据获取工具

这是一个完整的 Python 工具，用于从 Polymarket 的公开 API 获取数据。支持 **Gamma API**（市场发现）和 **Data API**（用户数据）。

## 📋 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [API 概览](#api-概览)
- [详细用法](#详细用法)
  - [Gamma API - 事件和市场](#gamma-api---事件和市场)
  - [Data API - 用户数据](#data-api---用户数据)
- [完整示例](#完整示例)
- [数据导出](#数据导出)

---

## 🚀 安装

### 依赖要求

```bash
pip install requests pandas
```

### 文件说明

- `polymarket_data_fetcher.py` - 主要的数据获取工具类
- `README.md` - 本文档

---

## ⚡ 快速开始

```python
from polymarket_data_fetcher import PolymarketDataFetcher

# 创建实例
fetcher = PolymarketDataFetcher()

# 获取活跃事件
events = fetcher.get_events(active=True, limit=10)
print(events.head())

# 获取市场数据
markets = fetcher.get_markets(active=True, limit=10)
print(markets.head())

# 保存为 CSV
events.to_csv('events.csv', index=False)
```

运行示例脚本：

```bash
python polymarket_data_fetcher.py
```

---

## 📚 API 概览

### 🔵 Gamma API (`https://gamma-api.polymarket.com`)
用于市场发现、元数据和分类

| 功能 | 方法 | 说明 |
|------|------|------|
| 事件列表 | `get_events()` | 获取所有事件 |
| 事件详情 | `get_event_by_id()` | 通过 ID 获取事件 |
| 事件详情 | `get_event_by_slug()` | 通过 slug 获取事件 |
| 市场列表 | `get_markets()` | 获取所有市场 |
| 市场详情 | `get_market_by_id()` | 通过 ID 获取市场 |
| 标签列表 | `get_tags()` | 获取所有分类标签 |
| 标签详情 | `get_tag_by_slug()` | 通过 slug 获取标签 |
| 系列列表 | `get_series()` | 获取事件系列 |

### 🟢 Data API (`https://data-api.polymarket.com`)
用于用户特定数据、投资组合跟踪和市场活动

| 功能 | 方法 | 说明 |
|------|------|------|
| 用户持仓 | `get_user_positions()` | 获取用户当前持仓 |
| 用户活动 | `get_user_activity()` | 获取用户交易历史 |
| 投资组合价值 | `get_user_value()` | 获取总价值和表现 |
| 交易记录 | `get_trades()` | 获取市场或用户的交易 |
| 市场持有者 | `get_market_holders()` | 获取顶级持有者 |



---

## 📖 详细用法

### Gamma API - 事件和市场

#### 1. 获取事件列表

```python
# 获取所有活跃事件
events = fetcher.get_events(active=True, closed=False, limit=20)

# 按标签筛选
events = fetcher.get_events(tag_id="crypto", limit=10)

# 按系列筛选
events = fetcher.get_events(series_id="presidential-election", limit=10)

# 分页
events_page1 = fetcher.get_events(limit=10, offset=0)
events_page2 = fetcher.get_events(limit=10, offset=10)
```

#### 2. 获取特定事件

```python
# 通过 ID 获取
event = fetcher.get_event_by_id("16167")
print(event['title'])

# 通过 slug 获取
event = fetcher.get_event_by_slug("bitcoin-price-2025")
print(event)
```

#### 3. 获取市场数据

```python
# 获取所有活跃市场
markets = fetcher.get_markets(active=True, closed=False, limit=20)

# 按事件筛选
markets = fetcher.get_markets(event_id="16167", limit=10)

# 按条件ID筛选
markets = fetcher.get_markets(condition_id="0x123...", limit=10)

# 通过 slug 筛选
markets = fetcher.get_markets(slug="trump-wins-2024", limit=1)
```

#### 4. 获取标签和系列

```python
# 获取所有标签
tags = fetcher.get_tags()
print(tags[['id', 'name', 'slug']])

# 获取特定标签
tag = fetcher.get_tag_by_slug("politics")

# 获取事件系列
series = fetcher.get_series(limit=20)
```

---

### Data API - 用户数据

#### 1. 获取用户持仓

```python
wallet = "0x1234567890abcdef1234567890abcdef12345678"

# 获取当前持仓
positions = fetcher.get_user_positions(wallet, limit=100)
print(positions[['market', 'outcome', 'size', 'value']])
```

#### 2. 获取用户活动

```python
# 获取用户所有活动（交易、存款、提款等）
activity = fetcher.get_user_activity(wallet, limit=100)
print(activity.head())
```

#### 3. 获取投资组合价值

```python
# 获取总价值和表现
portfolio = fetcher.get_user_value(wallet)
print(f"总价值: ${portfolio['total_value']}")
print(f"总收益: ${portfolio['total_profit']}")
```

#### 4. 获取交易记录

```python
# 获取特定用户的交易
trades = fetcher.get_trades(wallet_address=wallet, limit=50)

# 获取特定市场的交易
trades = fetcher.get_trades(market_id="12345", limit=100)

# 获取特定用户在特定市场的交易
trades = fetcher.get_trades(
    wallet_address=wallet,
    market_id="12345",
    limit=50
)
```

#### 5. 获取市场持有者

```python
# 获取市场的顶级持有者
holders = fetcher.get_market_holders(market_id="12345", limit=50)
print(holders[['address', 'size', 'value']])
```



---

## 💡 完整示例

### 示例 1: 分析热门市场

```python
from polymarket_data_fetcher import PolymarketDataFetcher
import pandas as pd

fetcher = PolymarketDataFetcher()

# 获取活跃市场
markets = fetcher.get_markets(active=True, limit=100)

# 按交易量排序
markets_sorted = markets.sort_values('volume', ascending=False)

# 显示前10个最热门市场
print("前10个最热门市场:")
for idx, row in markets_sorted.head(10).iterrows():
    print(f"{row['question']}")
    print(f"  交易量: ${row['volume']:,.2f}")
    print(f"  流动性: ${row['liquidity']:,.2f}")
    print()
```

### 示例 2: 跟踪用户投资组合

```python
wallet = "0x1234567890abcdef1234567890abcdef12345678"

# 获取用户持仓
positions = fetcher.get_user_positions(wallet)

# 获取投资组合价值
portfolio = fetcher.get_user_value(wallet)

# 获取最近交易
recent_trades = fetcher.get_trades(wallet_address=wallet, limit=20)

print(f"总价值: ${portfolio.get('total_value', 0):,.2f}")
print(f"持仓数量: {len(positions)}")
print(f"最近交易数: {len(recent_trades)}")
```


### 示例 3: 导出所有数据

```python
import os

# 创建输出目录
os.makedirs('polymarket_data', exist_ok=True)

# 获取并保存所有数据
print("正在获取数据...")

# Events
events = fetcher.get_events(active=True, limit=100)
events.to_csv('polymarket_data/events.csv', index=False, encoding='utf-8-sig')

# Markets
markets = fetcher.get_markets(active=True, limit=100)
markets.to_csv('polymarket_data/markets.csv', index=False, encoding='utf-8-sig')

# Tags
tags = fetcher.get_tags()
tags.to_csv('polymarket_data/tags.csv', index=False, encoding='utf-8-sig')

# Series
series = fetcher.get_series(limit=100)
series.to_csv('polymarket_data/series.csv', index=False, encoding='utf-8-sig')

print("✅ 所有数据已保存到 polymarket_data/ 目录")
```

---

## 💾 数据导出

所有返回 DataFrame 的方法都可以轻松导出为各种格式：

```python
# CSV (推荐用于 Excel)
df.to_csv('data.csv', index=False, encoding='utf-8-sig')

# JSON
df.to_json('data.json', orient='records', indent=2)

# Excel
df.to_excel('data.xlsx', index=False)

# Parquet (高效压缩)
df.to_parquet('data.parquet')
```

---

## 🔧 高级技巧

### 1. 批量获取数据

```python
def get_all_events(fetcher, limit_per_page=100):
    """获取所有事件（自动分页）"""
    all_events = []
    offset = 0
    
    while True:
        events = fetcher.get_events(limit=limit_per_page, offset=offset)
        if events.empty:
            break
        all_events.append(events)
        offset += limit_per_page
        
        if len(events) < limit_per_page:
            break
    
    return pd.concat(all_events, ignore_index=True) if all_events else pd.DataFrame()

# 使用
all_events = get_all_events(fetcher)
print(f"总共获取 {len(all_events)} 个事件")
```

### 2. 错误处理

```python
try:
    markets = fetcher.get_markets(active=True, limit=10)
    if markets.empty:
        print("未获取到数据")
    else:
        print(f"成功获取 {len(markets)} 个市场")
except Exception as e:
    print(f"发生错误: {e}")
```

### 3. 数据过滤和分析

```python
# 获取市场数据
markets = fetcher.get_markets(active=True, limit=100)

# 过滤高流动性市场
high_liquidity = markets[markets['liquidity'] > 10000]

# 按分类统计
if 'tags' in markets.columns:
    # 展开标签并统计
    markets_with_tags = markets.explode('tags')
    tag_counts = markets_with_tags['tags'].value_counts()
    print(tag_counts)
```

---

## 📝 注意事项

1. **API 限制**: Polymarket API 可能有速率限制，建议在循环中添加适当的延迟
2. **钱包地址**: Data API 的用户相关功能需要有效的以太坊钱包地址
3. **数据更新**: 市场数据会实时更新，建议定期刷新

---

## 🔗 相关链接

- [Polymarket 官网](https://polymarket.com/)
- [Polymarket API 文档](https://docs.polymarket.com/)
- [Gamma API 文档](https://docs.polymarket.com/api-reference/gamma-markets-api)
- [Data API 文档](https://docs.polymarket.com/api-reference/data-api)

---

## 📄 许可证

本项目仅供学习和研究使用。使用 Polymarket API 时请遵守其服务条款。

---

## 🤝 贡献

欢迎提交问题和改进建议！

---

**Happy Trading! 📈**
