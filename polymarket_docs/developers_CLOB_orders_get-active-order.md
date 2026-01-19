# Source: https://docs.polymarket.com/developers/CLOB/orders/get-active-order

Python

Typescript

Copy

Ask AI

```
from py_clob_client.clob_types import OpenOrderParams

resp = client.get_orders(
    OpenOrderParams(
        market="0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
    )
)
print(resp)
print("Done!")
```

This endpoint requires a L2 Header.

Get active order(s) for a specific market.
**HTTP REQUEST**
`GET /<clob-endpoint>/data/orders`

### [​](#request-parameters) Request Parameters

| Name | Required | Type | Description |
| --- | --- | --- | --- |
| id | no | string | id of order to get information about |
| market | no | string | condition id of market |
| asset\_id | no | string | id of the asset/token |

### [​](#response-format) Response Format

| Name | Type | Description |
| --- | --- | --- |
| null | OpenOrder[] | list of open orders filtered by the query parameters |

Python

Typescript

Copy

Ask AI

```
from py_clob_client.clob_types import OpenOrderParams

resp = client.get_orders(
    OpenOrderParams(
        market="0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
    )
)
print(resp)
print("Done!")
```

[Get Order](/developers/CLOB/orders/get-order)[Check Order Reward Scoring](/developers/CLOB/orders/check-scoring)

⌘I