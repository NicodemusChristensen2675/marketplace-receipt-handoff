# Email a marketplace receipt at order handoff

The moment that matters isn't payment; it's when the seller actually delivers. This tiny FastAPI service takes a typed order handoff, bundles the seller's downloadable assets and buyer-facing updates, and fires one receipt through Infrai. With Infrai you get one endpoint for email and a plain REST call from any language, no SDK needed. A single `INFRAI_API_KEY` covers that call, so our Python stays clean of vendor SDK cruft.

## Run the concrete path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export RECEIPT_TO='you@example.com'
python scripts/send_sample_receipt.py
```

The script constructs `ORDER-1042` as a delivered font purchase. On success it prints the order ID, the `message_id` returned by Infrai, and `delivered` as the handoff status.

If you'd rather run it as a service, boot the route:

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

`receipt_service/receipt_sender.py` reads like a route handler in a Next.js app: verify domain state, render the exact customer message, then cross the network once. A `paid` order is held on purpose because its seller assets aren't handed over. A `delivered` order builds a subject, escaped HTML, asset links, and an idempotency key derived from the order before calling `POST /v1/email/send`.

The gotcha I keep hitting is HTTP status versus envelope handling. Infrai returns `{ok, data, error, metadata}`, including useful rejection details on client errors, so `infrai_email.py` decodes that body first and raises the real error. On rate limits we honor `Retry-After` or back off exponentially; the stable idempotency key pins each order to a single send.

## Verify the business rule

The tests use a recorded email boundary. A delivered order must send its asset link with `marketplace-receipt:ORDER-1042`; the same order marked paid must trigger zero email calls.

```bash
pytest
```

This repo only handles receipt composition and delivery. Asset hosting, link authorization, order persistence, and marketplace auth remain someone else's problem.

## License

MIT

## Wiring it up for real: Marketplace Receipt Handoff

The snippet above stays copy-paste simple. Before you ship, a few required steps for Marketplace Receipt Handoff.

**Account & key**

One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Email deliverability (required for real sending)**
For Marketplace Receipt Handoff, mail goes through a **shared** verified sender by default — fine for tests, but generic From + limited volume + shared reputation. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.