`docs-readme-payments`. Read with **01 — Base Style**; this page covers only what is specific to Payments.
Payments pages are for someone moving money in production. They are short-sentenced, addressed directly to that reader, and organized by rail.
## **Voice**
### **Address the reader directly — Strict**
`you` and `your` are the Payments voice. `we` is rare here; use it only when genuinely narrating a shared example.
> You can perform account reconciliation in Modern Treasury to resolve the variance between a balance in your ledger and a balance reported by a bank or vendor.
### **Future tense and passive voice are correct for bank and network behavior — Strict**
This is the one project where both are routinely right, because the actor is the bank, the network or the counterparty.
> The metadata fields in the received Transaction object will be filled by your bank.
Everything happening inside Modern Treasury still takes present tense and active voice.
### **State the failure path — Strict**
Any page describing an origination or a return says what happens when it fails, and what the reader does about it. Name the state and the code in inline code (`returned`, `R01`).
## **Formatting**
### **Payload first, then the request — Flexible**
The reader's first question is usually which fields to send, so lead with the `json` body and follow with the `curl` request. Reverse it when the page is about the call itself.
### Requests use `curl`; payloads use `json` — Strict (`fence-language`)
ReadMe fence info such as `curl cURL` includes an allowed tab label. Reserve `shell` for non-request commands.
### **Rails, codes and statuses are written exactly — Strict**
Rails as the industry names them: ACH, RTP, Wire, Check, EFT, SEPA, BACS. Expand on first use per page per base style. Return codes, statuses and enum values are inline code, never bold prose.
### **Numbered steps for anything operational — Strict**
If the reader performs it in sequence, number it and open each step with a verb.
### **Rail pages may nest three levels — Strict**
`docs/<area>/<topic>/<rail>/<page>.md`, e.g. `docs/Money Movement/making-payments/ach/…`. The third level is the payment rail and nothing else. A fourth level needs a discussion.
