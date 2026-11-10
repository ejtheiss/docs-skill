---
title: ACH Debit Reserves
---

Every program that collects funds by Automated Clearing House (ACH) debit on Modern Treasury posts a reserve. This page covers how the reserve works, how Modern Treasury sizes it, and how it changes as your program grows.

## How a reserve works

The payer's bank can return an ACH debit after the money has moved, much like a card chargeback. Modern Treasury protects against returns in three layers:

1. **Two-day hold.** Modern Treasury holds the funds from an ACH debit for two banking days, because most returns arrive inside that window.
2. **72 hours to cover a negative balance.** If a return leaves your account negative, Modern Treasury notifies you right away. You have 72 hours to bring the account back to zero, usually by recovering the funds from the customer whose debit was returned.
3. **The reserve.** If you can't cover the shortfall within 72 hours, Modern Treasury uses the reserve to cover it.

## Which returns happen, and when

The return window depends on the return reason and on the type of bank account you debit:

- **Insufficient funds and account problems** — `R01` (insufficient funds), `R02` (account closed), `R03` (no account) and `R04` (invalid account number). The payer's bank will usually send these within two banking days.
- **Unauthorized, business account** — `R29`. The payer's bank has two banking days to send it.
- **Unauthorized, consumer account** — `R05`, `R07`, `R10` and `R11`. The payer's bank has up to 60 calendar days from settlement to send it.

The account type decides the window, not who the payer is. If you debit a personal account, even one that belongs to a business owner, the payer has the full 60 days.

When a return arrives, the debit's Payment Order moves to `returned` and Modern Treasury notifies you.

## Can one bad actor put my whole program at risk?

As the program owner, you're responsible for every account in your program, as you would be with any payments provider. Shutting down a program is a last resort.

In practice, the 72 hours are a conversation. Modern Treasury contacts you as soon as a return comes in and works with you on how and when you'll cover the account. If Modern Treasury doesn't hear from you, or there's no path to bringing the account back to zero, Modern Treasury can shut down your program.

## How much will my reserve be?

It depends on your program. Modern Treasury looks at:

- Your daily debit limit
- Your largest and average debit
- Whether you debit business or consumer accounts

As a rough guide, plan for a reserve of about 20% of your daily debit limit. Your actual number can be higher or lower. Share your expected volumes with your Modern Treasury account team to get a specific number.

## Does my existing payment history count?

Yes. New programs start with a standard estimate. If you already process ACH debits with another provider, share your return history, and Modern Treasury bases your reserve on your actual track record.

## Where is the reserve held, and do I get it back?

Modern Treasury holds the reserve separately from your accounts and your customers' accounts, so it never affects their balances. It's separate from your platform fees.

The reserve is fully refundable. If you stop working with Modern Treasury, Modern Treasury returns it after accounting for any final ACH returns or reversals.

## Will my reserve change over time?

Yes, in either direction. Once you have 90 to 120 days of live activity and enough volume to give a meaningful return rate, you can ask Modern Treasury to reassess it.

A low return rate can lower your reserve. If your volume or limits grow, your reserve can go up even when returns stay low.

You can ask for a higher daily limit at any time. A new limit can take effect as soon as the next business day.

## How can I keep my reserve low?

- **Ask for a daily limit that fits a typical day.** A higher limit means a higher reserve. Send occasional large payments by wire instead.
- **Get a clear, timestamped ACH authorization from every payer.** It's your strongest defense against unauthorized returns.
- **Know who you're debiting.** Debit business payers from business accounts, and use strong onboarding and identity checks to keep bad actors out of your program.

A low return rate does more than anything else to bring your reserve down.

> 📘 This page is for general information. It is not legal advice and does not amend the Platform Customer Agreement or any other agreement with Modern Treasury or M-Cubed. Reserve amounts are set case by case.
