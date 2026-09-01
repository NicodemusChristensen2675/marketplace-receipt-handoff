from html import escape

from .infrai_email import InfraiEmailClient
from .models import HandoffStatus, OrderHandoff, ReceiptAccepted


class OrderNotDeliveredError(ValueError):
    pass


def send_handoff_receipt(
    order: OrderHandoff, client: InfraiEmailClient
) -> ReceiptAccepted:
    if order.status is not HandoffStatus.DELIVERED:
        raise OrderNotDeliveredError("A receipt is sent after the seller delivers the order")

    asset_items = "".join(
        f'<li><a href="{escape(str(asset.download_url), quote=True)}">'
        f"{escape(asset.name)}</a></li>"
        for asset in order.assets
    )
    updates = "".join(
        f"<li>{escape(update.message)}</li>" for update in order.buyer_updates
    )
    updates_section = f"<h2>Seller updates</h2><ul>{updates}</ul>" if updates else ""
    html = (
        f"<h1>Your receipt for {escape(order.item_name)}</h1>"
        f"<p>Order {escape(order.order_id)} from {escape(order.seller_name)} is ready.</p>"
        f"<p>Total: {escape(order.currency.upper())} {order.amount:.2f}</p>"
        f"<h2>Your files</h2><ul>{asset_items}</ul>{updates_section}"
    )
    message_id = client.send_receipt(
        to=str(order.buyer_email),
        subject=f"Receipt and files for order {order.order_id}",
        html=html,
        idempotency_key=f"marketplace-receipt:{order.order_id}",
    )
    return ReceiptAccepted(
        order_id=order.order_id,
        message_id=message_id,
        handoff_status=order.status,
    )
