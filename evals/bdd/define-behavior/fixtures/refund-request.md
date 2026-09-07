# SHOP-482: Self-service refund requests

Customers wait three days for support to process a refund by hand. We want the
customer to raise the request themselves from the order page.

## Acceptance criteria

- A customer can request a refund on a delivered order for 30 days after delivery.
- Once the request is raised, the order shows the state "Refund requested".
- An order delivered more than 30 days ago cannot be refunded.
- An order can carry only one open refund request at a time.

## Notes from refinement

Support asked that a customer who is turned down is told why. Today they email
support to ask, and that is the cost we are trying to remove.

Finance confirmed the refund amount is always the full order total. Partial
refunds stay out of scope for this ticket.
