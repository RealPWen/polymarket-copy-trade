
import requests
import json
import sys

# 解决 Windows 乱码
sys.stdout.reconfigure(encoding='utf-8')

WALLET = "0xd82079c0d6b837bad90abf202befc079da5819f6"
URL = "https://data-api.polymarket.com/value"

print(f"🔍 正在查询余额信息: {WALLET}")

try:
    r = requests.get(URL, params={"user": WALLET})
    if r.status_code == 200:
        data = r.json()
        print(f"✅ API 响应成功:")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        
        # 尝试解析
        if isinstance(data, list) and len(data) > 0:
            item = data[0]
            val = item.get('value')
            cash = item.get('cash') # 这是一个文档未记录但可能存在的字段
            print(f"\n💰 投资组合总值 (Value): ${val}")
            if cash is not None:
                print(f"💵 现金余额 (Cash): ${cash}")
            else:
                print(f"❓ 现金余额 (Cash): 未在响应中找到")
    else:
         print(f"❌ 请求失败: {r.status_code} - {r.text}")

except Exception as e:
    print(f"❌ 发生错误: {e}")
