Path: `docs/Customer Onboarding/onboard-a-business/required-fields-for-businesses.md`
Heading: Prepare addresses

Quote:

```text
Array of [Addresses](https://docs.moderntreasury.com/platform/reference/address-object) - P.O. boxes are not accepted with `address_type` of `business_registeredprimary` marked as `false`
```

Replacement:

```text
Array of [Addresses](https://docs.moderntreasury.com/platform/reference/address-object) - P.O. boxes are not accepted with `address_type` of `business_registered` and `primary` marked as `false`. For a registered-agent Legal Entity, submit the agent's address as the business registered address.
```
