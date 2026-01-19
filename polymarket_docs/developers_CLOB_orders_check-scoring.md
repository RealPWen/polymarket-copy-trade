# Source: https://docs.polymarket.com/developers/CLOB/orders/check-scoring

Python

Typescript

Copy

Ask AI

```
scoring = client.is_order_scoring(
    OrderScoringParams(
        orderId="0x..."
    )
)
print(scoring)

scoring = client.are_orders_scoring(
    OrdersScoringParams(
        orderIds=["0x..."]
    )
)
print(scoring)
```

This endpoint requires a L2 Header.

Returns a boolean value where it is indicated if an order is scoring or not.
**HTTP REQUEST**
`GET /<clob-endpoint>/order-scoring?order_id={...}`

### [​](#request-parameters) Request Parameters

| Name | Required | Type | Description |
| --- | --- | --- | --- |
| orderId | yes | string | id of order to get information about |

### [​](#response-format) Response Format

| Name | Type | Description |
| --- | --- | --- |
| null | OrdersScoring | order scoring data |

An `OrdersScoring` object is of the form:

| Name | Type | Description |
| --- | --- | --- |
| scoring | boolean | indicates if the order is scoring or not |

# [​](#check-if-some-orders-are-scoring) Check if some orders are scoring

> This endpoint requires a L2 Header.

Returns to a dictionary with boolean value where it is indicated if an order is scoring or not.
**HTTP REQUEST**
`POST /<clob-endpoint>/orders-scoring`

### [​](#request-parameters-2) Request Parameters

| Name | Required | Type | Description |
| --- | --- | --- | --- |
| orderIds | yes | string[] | ids of the orders to get information about |

### [​](#response-format-2) Response Format

| Name | Type | Description |
| --- | --- | --- |
| null | OrdersScoring | orders scoring data |

An `OrdersScoring` object is a dictionary that indicates the order by if it score.

Python

Typescript

Copy

Ask AI

```
scoring = client.is_order_scoring(
    OrderScoringParams(
        orderId="0x..."
    )
)
print(scoring)

scoring = client.are_orders_scoring(
    OrdersScoringParams(
        orderIds=["0x..."]
    )
)
print(scoring)
```

[Get Active Orders](/developers/CLOB/orders/get-active-order)[Cancel Orders(s)](/developers/CLOB/orders/cancel-orders)

⌘I