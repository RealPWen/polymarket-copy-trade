
import requests
import json
import sys

# 设置输出编码为 utf-8
sys.stdout.reconfigure(encoding='utf-8')

# 目标用户（来自您的 JSON output rank 10）
USER = "0xdc876e6873772d38716fda7f2452a78d426d7ab6"
URL = "https://data-api.polymarket.com/v1/closed-positions"

print(f"Fetching closed positions for: {USER}")
try:
    resp = requests.get(URL, params={"user": USER, "limit": 2})
    print(f"Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"Received {len(data)} records.")
        if len(data) > 0:
            first_item = data[0]
            print("\nKeys in first record:")
            print(list(first_item.keys()))
            
            print("\nFull Record Content:")
            print(json.dumps(first_item, indent=2))
        else:
            print("No records found.")
    else:
        print(f"Error: {resp.text}")

except Exception as e:
    print(f"Exception: {e}")
