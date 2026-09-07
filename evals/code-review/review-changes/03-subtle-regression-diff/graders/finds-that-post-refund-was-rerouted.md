---
type: llm
focus: last_message
---
Finds that post_refund was rerouted to refund(), bypassing the already_refunded guard that only refund_order still applies, so a second full refund through the endpoint now succeeds where main rejected it.
