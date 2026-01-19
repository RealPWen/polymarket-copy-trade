# Source: https://docs.polymarket.com/developers/CLOB/orders/get-order

Python

Typescript

Copy

Ask AI

```
order = clob_client.get_order("0xb816482a5187a3d3db49cbaf6fe3ddf24f53e6c712b5a4bf5e01d0ec7b11dabc")
print(order)
```

This endpoint requires a L2 Header.

Get single order by id.
**HTTP REQUEST**
`GET /<clob-endpoint>/data/order/<order_hash>`

### [​](#request-parameters) Request Parameters

| Name | Required | Type | Description |
| --- | --- | --- | --- |
| id | no | string | id of order to get information about |

### [​](#response-format) Response Format

| Name | Type | Description |
| --- | --- | --- |
| order | OpenOrder | order if it exists |

An `OpenOrder` object is of the form:

| Name | Type | Description |
| --- | --- | --- |
| associate\_trades | string[] | any Trade id the order has been partially included in |
| id | string | order id |
| status | string | order current status |
| market | string | market id (condition id) |
| original\_size | string | original order size at placement |
| outcome | string | human readable outcome the order is for |
| maker\_address | string | maker address (funder) |
| owner | string | api key |
| price | string | price |
| side | string | buy or sell |
| size\_matched | string | size of order that has been matched/filled |
| asset\_id | string | token id |
| expiration | string | unix timestamp when the order expired, 0 if it does not expire |
| type | string | order type (GTC, FOK, GTD) |
| created\_at | string | unix timestamp when the order was created |

Python

Typescript

Copy

Ask AI

```
order = clob_client.get_order("0xb816482a5187a3d3db49cbaf6fe3ddf24f53e6c712b5a4bf5e01d0ec7b11dabc")
print(order)
```

[Place Multiple Orders (Batching)](/developers/CLOB/orders/create-order-batch)[Get Active Orders](/developers/CLOB/orders/get-active-order)

⌘I