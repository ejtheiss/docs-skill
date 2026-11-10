---
title: '{{title}}'
---
# {{heading}}

{{purpose}}

## Prerequisites

{{prerequisite}}

***

## Phase 1: initiate

1. Customer API call: {{action}}

Modern Treasury transition: {{transition}}

Webhook gate: wait for `{{event}}` before step 2. Match the event to `{{correlation_field}}` and verify `{{state_field}}` before continuing.

***

## Phase 2: continue

2. Customer API call: {{next_action}}

Bank-driven transition: {{bank_transition}}

## Retry and failure handling

{{retry_guidance}}

{{failure_guidance}}

## Verify the result

{{verification}}
