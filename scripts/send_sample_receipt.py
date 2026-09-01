import os

from receipt_service.infrai_email import InfraiEmailClient
from receipt_service.models import BuyerUpdate, HandoffStatus, OrderHandoff, SellerAsset
from receipt_service.receipt_sender import send_handoff_receipt


def main() -> None:
    buyer_email = os.environ.get("RECEIPT_TO")
    if not buyer_email:
        raise RuntimeError("RECEIPT_TO is required")
    order = OrderHandoff(
        order_id="ORDER-1042",
        buyer_email=buyer_email,
        seller_name="Northstar Type Co.",
        item_name="Editorial font family",
        amount="49.00",
        currency="USD",
        status=HandoffStatus.DELIVERED,
        assets=[
            SellerAsset(
                name="Font package",
                download_url="https://downloads.example.com/orders/ORDER-1042/fonts.zip",
            )
        ],
        buyer_updates=[BuyerUpdate(message="Desktop and webfont licenses are included.")],
    )
    result = send_handoff_receipt(order, InfraiEmailClient())
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
