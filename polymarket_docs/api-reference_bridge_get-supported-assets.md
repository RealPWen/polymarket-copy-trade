# Source: https://docs.polymarket.com/api-reference/bridge/get-supported-assets

Get supported assets

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://bridge.polymarket.com/supported-assets
```

200

500

Copy

Ask AI

```
{
  "supportedAssets": [
    {
      "chainId": "1",
      "chainName": "Ethereum",
      "token": {
        "name": "USD Coin",
        "symbol": "USDC",
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": 6
      },
      "minCheckoutUsd": 45
    }
  ]
}
```

GET

/

supported-assets

Try it

Get supported assets

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://bridge.polymarket.com/supported-assets
```

200

500

Copy

Ask AI

```
{
  "supportedAssets": [
    {
      "chainId": "1",
      "chainName": "Ethereum",
      "token": {
        "name": "USD Coin",
        "symbol": "USDC",
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": 6
      },
      "minCheckoutUsd": 45
    }
  ]
}
```

#### Response

200

application/json

Successfully retrieved supported assets

[​](#response-supported-assets)

supportedAssets

object[]

List of supported assets with minimum deposit amounts

Show child attributes

[Create deposit addresses](/api-reference/bridge/create-deposit-addresses)[Overview](/developers/subgraph/overview)

⌘I