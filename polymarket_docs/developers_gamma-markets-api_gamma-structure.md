# Source: https://docs.polymarket.com/developers/gamma-markets-api/gamma-structure

On this page

* [Detail](#detail)
* [Example](#example)

Gamma provides some organizational models. These include events, and markets. The most fundamental element is always markets and the other models simply provide additional organization.

# [​](#detail) Detail

1. **Market**
   1. Contains data related to a market that is traded on. Maps onto a pair of clob token ids, a market address, a question id and a condition id
2. **Event**
   1. Contains a set of markets
   2. Variants:
      1. Event with 1 market (i.e., resulting in an SMP)
      2. Event with 2 or more markets (i.e., resulting in an GMP)

# [​](#example) Example

* **[Event]** Where will Barron Trump attend College?
  + **[Market]** Will Barron attend Georgetown?
  + **[Market]** Will Barron attend NYU?
  + **[Market]** Will Barron attend UPenn?
  + **[Market]** Will Barron attend Harvard?
  + **[Market]** Will Barron attend another college?

[Overview](/developers/gamma-markets-api/overview)[Fetching Markets](/developers/gamma-markets-api/fetch-markets-guide)

⌘I