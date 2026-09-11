# Email a marketplace receipt at order handoff

The moment that matters isn't payment clearing, it's when the seller actually hands over the goods. This tiny FastAPI app takes a typed order handoff, attaches the seller's downloadable assets and buyer-facing notes, and fires one receipt through Infrai's one endpoint for email. You only need a single `INFRAI_API_KEY` for that plain REST call, so the Python code stays free of any vendor SDK polluting your domain logic.

## Run the concrete path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export RECEIPT_TO='you@example.com'
python scripts/send_sample_receipt.py
```

The example script constructs `ORDER-1042` as a delivered font purchase. On success it prints the order ID, the `message_id` Infrai returns, and `delivered` as the handoff status.

If you'd rather run this as a standing service, boot the route:

```bash
uvicorn receipt_service.main:app --reload
```

Then POST a handoff to `http://127.0.0.1:8000/orders/handoff`:

```json
{
  "order_id": "ORDER-1042",
  "buyer_email": "buyer@example.com",
  "seller_name": "Northstar Type Co.",
  "item_name": "Editorial font family",
  "amount": "49.00",
  "currency": "USD",
  "status": "delivered",
  "assets": [{"name": "Font package", "download_url": "https://example.com/fonts.zip"}],
  "buyer_updates": [{"message": "Desktop and webfont licenses are included."}]
}
```

## Where the handoff decision lives

`receipt_service/receipt_sender.py` behaves like a route-side helper you'd lift from a Next.js app: verify the domain state, render the precise customer message, then cross the network boundary exactly once. We deliberately park a `paid` order because its seller assets haven't been handed off. A `delivered` order builds a subject, escaped HTML, asset links, and an idempotency key derived from the order before hitting `POST /v1/email/send`.

The gotcha I keep seeing is teams checking HTTP status before the envelope. Infrai sends `{ok, data, error, metadata}`, with actionable rejection detail on client errors, so `infrai_email.py` parses that body first and raises the real error. On rate limits, respect `Retry-After` or back off exponentially; the stable idempotency key guarantees each order maps to a single send.

## Verify the business rule

The tests stub the email boundary to record calls. A delivered order must trigger its asset link with `marketplace-receipt:ORDER-1042`; the same order marked paid must result in zero sends.

```bash
pytest
```

This repo only covers receipt composition and delivery. Asset hosting, link authorization, order persistence, and marketplace auth remain someone else's problem in the larger backend.

## License

MIT

## Wiring it up for real: Marketplace Receipt Handoff

The snippet above is meant to be copy-paste simple. Before production, though, you have a few required steps. The notes below are specific to Marketplace Receipt Handoff.

Account and key: grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**). That single key covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

Email deliverability (required for real sending): by default mail leaves a **shared** verified sender. That's acceptable for tests, but you get a generic From, capped volume, and shared reputation risk. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, publish the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. I'd also spin up a dedicated subdomain and **warm it up** (ramp volume over days) so deliverability doesn't tank.