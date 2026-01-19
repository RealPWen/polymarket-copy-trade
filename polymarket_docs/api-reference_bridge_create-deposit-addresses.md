# Source: https://docs.polymarket.com/api-reference/bridge/create-deposit-addresses

Create deposit addresses

cURL

Copy

Ask AI

```
curl --request POST \
  --url https://bridge.polymarket.com/deposit \
  --header 'Content-Type: application/json' \
  --data '
{
  "address": "0x56687bf447db6ffa42ffe2204a05edaa20f55839"
}
'
```

201

400

500

Copy

Ask AI

```
{
  "address": {
    "evm": "0x23566f8b2E82aDfCf01846E54899d110e97AC053",
    "svm": "CrvTBvzryYxBHbWu2TiQpcqD5M7Le7iBKzVmEj3f36Jb",
    "btc": "bc1q8eau83qffxcj8ht4hsjdza3lha9r3egfqysj3g"
  },
  "note": "Only certain chains and tokens are supported. See /supported-assets for details."
}
```

POST

/

deposit

Try it

Create deposit addresses

cURL

Copy

Ask AI

```
curl --request POST \
  --url https://bridge.polymarket.com/deposit \
  --header 'Content-Type: application/json' \
  --data '
{
  "address": "0x56687bf447db6ffa42ffe2204a05edaa20f55839"
}
'
```

201

400

500

Copy

Ask AI

```
{
  "address": {
    "evm": "0x23566f8b2E82aDfCf01846E54899d110e97AC053",
    "svm": "CrvTBvzryYxBHbWu2TiQpcqD5M7Le7iBKzVmEj3f36Jb",
    "btc": "bc1q8eau83qffxcj8ht4hsjdza3lha9r3egfqysj3g"
  },
  "note": "Only certain chains and tokens are supported. See /supported-assets for details."
}
```

#### Body

application/json

[​](#body-address)

address

string

required

Your Polymarket wallet address

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

#### Response

201

application/json

Deposit addresses created successfully

[​](#response-address)

address

object

Deposit addresses for different blockchain networks

Show child attributes

[​](#response-note)

note

string

Additional information about supported chains

Example:

`"Only certain chains and tokens are supported. See /supported-assets for details."`

[Overview](/developers/misc-endpoints/bridge-overview)[Get supported assets](/api-reference/bridge/get-supported-assets)

⌘I