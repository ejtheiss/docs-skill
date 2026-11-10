---
title: Fixture
---
# Checks

```json Response
{"internal_account_id":"abc", "rows":[{"amount":5,"currency":"USD","description":"free string"},{"typo/nested~key":3}], "metadata":{"status":"not_an_enum", "secret_key":2}}
```

```json
{"third_party_field":1}
```

```curl cURL
curl https://app.moderntreasury.com/api/example -d '{"internal_account_id":"abc", "status":"unknown"}'
```
