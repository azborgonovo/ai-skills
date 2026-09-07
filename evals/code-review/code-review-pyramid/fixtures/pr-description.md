# Add outbound webhook delivery

Closes ORD-311.

## What this does

- Adds a new `webhooks/` module that delivers order events to customer endpoints.
- Signs every payload. The key comes from a new `WEBHOOK_SIGNING_KEY` environment variable.
- Renames the Kafka topic `orders.events` to `orders.v2.events`.
- Adds `httpx` to `requirements.txt`.

## How to test

Run the service locally and post an order. You should see the delivery in the log.

## Notes

I kept the retry logic simple for now. Ready for review.
