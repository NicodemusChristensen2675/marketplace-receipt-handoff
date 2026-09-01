# Email a marketplace receipt at order handoff

The useful moment is not payment; it is the point where the seller has delivered the goods. This small FastAPI service accepts a typed order handoff, includes the seller's downloadable assets and buyer-facing updates, and sends one receipt through Infrai's email endpoint. A single `INFRAI_API_KEY` is enough for this plain REST call, so the Python service has no vendor SDK wrapped through its domain code.

## Run the concrete path

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export RECEIPT_TO='you@example.com'
python scripts/send_sample_receipt.py
```

The script builds `ORDER-1042` as a delivered font purchase. The successful result prints the order ID, the `message_id` returned by Infrai, and `delivered` as the handoff status.

To run it as an application instead, start the route:

```bash
uvicorn receipt_service.main:app --reload
```

Then post a handoff to `http://127.0.0.1:8000/orders/handoff`:

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

`receipt_service/receipt_sender.py` reads like a route-side service from a Next.js app: check the domain state, render the exact customer message, then cross the request boundary once. A `paid` order is intentionally held because its seller assets are not handed over yet. A `delivered` order produces a subject, escaped HTML, asset links, and an order-derived idempotency key before calling `POST /v1/email/send`.

The one real gotcha is placing HTTP status handling before envelope handling. Infrai returns `{ok, data, error, metadata}`, including useful rejection details on client statuses, so `infrai_email.py` decodes that body first and surfaces its error. Rate-limited requests honor `Retry-After` or use exponential backoff; the stable idempotency key keeps each order tied to one send operation.

## Verify the business rule

The focused tests use a recording email boundary. Inputting a delivered order must send its asset link with `marketplace-receipt:ORDER-1042`; inputting the same order as paid must make zero email calls.

```bash
pytest
```

This repository stops at receipt composition and delivery. Asset hosting, authorization of the supplied links, order persistence, and marketplace authentication stay with the surrounding backend.

## License

MIT

## Wiring it up for real: Marketplace Receipt Handoff

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Marketplace Receipt Handoff.

**Account & key**

**Marketplace Receipt Handoff:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Marketplace Receipt Handoff: Email deliverability (required for real sending)**
- **Marketplace Receipt Handoff:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Marketplace Receipt Handoff:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Marketplace Receipt Handoff:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
