
import requests
import json

URL = "https://data-api.polymarket.com/v1/closed-positions"
USER = "0xdc876e6873772d38716fda7f2452a78d426d7ab6"

params = {
    "user": USER,
    "limit": 1
}

resp = requests.get(URL, params=params)
if resp.status_code == 200:
    data = resp.json()
    if data:
        item = data[0]
        print("Keys found:", list(item.keys()))
        print(f"PercentRoi present? {'percentRoi' in item}")
        print("Values:", json.dumps(item, indent=2))
