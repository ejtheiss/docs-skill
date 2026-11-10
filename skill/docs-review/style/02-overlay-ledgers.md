<!-- Compiled from Notion by scripts/notion_sync.py. Do not edit; edit https://app.notion.com/p/3c8d6bfc268380beb423e6cce5948e8d
     policy 718466089eff · synced 2026-09-03T21:34:37+00:00 -->
`docs-readme-ledgers`. Read with **01 — Base Style**; this page covers only what is specific to Ledgers.
Ledgers pages teach double-entry accounting to readers who have not modelled it before. They are longer than other pages, built around worked examples, and carry the most code. That is intentional.
## **Voice**
### **Walk through worked examples in first person plural — Strict**
`we` is the Ledgers voice for tutorials and design walkthroughs. Keep `you` for what the reader decides or does outside Modern Treasury.
> We will use Ledger Account Categories to track the overall balance across the digital wallets of all our users.
> You will need to calculate total interest due to the loan provider outside of Modern Treasury.
### **Name the account and the direction for every balance change — Strict**
Never describe money moving without saying which account and which side.
**Do**
> This account will get deducted (debited) by \$1,200 in USD when the transfer is posted.
> Debiting a Virtual Account credits the Internal Account's Ledger Account for the outbound payment amount.
**Don't**
> The balance updates once the transfer goes through.
### **Pair the accounting term with the plain word on first use — Flexible**
*deducted (debited)*, *added (credited)* on first use, then the accounting term alone.
### **Spell out ledger objects, always — Strict**
Ledgers is where `LA`, `LT` and `LAS` creep in. Base style bans them; that ban matters most here, because "Account" and "Transaction" both mean something else in this product.
## **Formatting**
### **`shell`**** for requests, ****`json`**** for payloads — Strict**
Tutorials show the request and the body. Use `shell` and `json`; never `curl` or `bash`.
### **Code carries the lesson — Flexible**
A Ledgers page can be mostly code. Show the full request and the resulting Ledger Entries rather than describing them in prose.
### **Callouts are rare — Flexible**
Ledgers explains constraints in prose, which reads better in a tutorial. Use 🚧 only for a genuine early-access or limitation notice. Do not sprinkle callouts to match other projects.
### **Tutorial pages nest one level under their tutorial index — Strict**
`docs/Get Started/ledgers-tutorials/<tutorial>.md`. Deeper nesting needs a discussion.
