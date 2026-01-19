# Source: https://docs.polymarket.com/developers/CLOB/timeseries

Get price history for a traded token

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/prices-history
```

200

400

404

500

Copy

Ask AI

```
{
  "history": [
    {
      "t": 1697875200,
      "p": 1800.75
    }
  ]
}
```

GET

/

prices-history

Try it

Get price history for a traded token

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/prices-history
```

200

400

404

500

Copy

Ask AI

```
{
  "history": [
    {
      "t": 1697875200,
      "p": 1800.75
    }
  ]
}
```

The CLOB provides detailed price history for each traded token.
**HTTP REQUEST**
`GET /<clob-endpoint>/prices-history`

We also have a Interactive Notebook to visualize the data from this endpoint available [here](https://colab.research.google.com/drive/1s4TCOR4K7fRP7EwAH1YmOactMakx24Cs?usp=sharing#scrollTo=mYCJBcfB9Zu4).

#### Query Parameters

[​](#parameter-market)

market

string

required

The CLOB token ID for which to fetch price history

[​](#parameter-start-ts)

startTs

number

The start time, a Unix timestamp in UTC

[​](#parameter-end-ts)

endTs

number

The end time, a Unix timestamp in UTC

[​](#parameter-interval)

interval

enum<string>

A string representing a duration ending at the current time. Mutually exclusive with startTs and endTs

Available options:

`1m`,

`1w`,

`1d`,

`6h`,

`1h`,

`max`

[​](#parameter-fidelity)

fidelity

number

The resolution of the data, in minutes

#### Response

200

application/json

A list of timestamp/price pairs

[​](#response-history)

history

object[]

required

Show child attributes

[Get bid-ask spreads](/api-reference/spreads/get-bid-ask-spreads)[Orders Overview](/developers/CLOB/orders/orders)

⌘I