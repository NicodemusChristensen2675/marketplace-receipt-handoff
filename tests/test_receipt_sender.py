from typing import Any

import pytest

from receipt_service.models import HandoffStatus, OrderHandoff, SellerAsset
from receipt_service.receipt_sender import OrderNotDeliveredError, send_handoff_receipt


class RecordingEmailClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def send_receipt(self, **payload: Any) -> str:
        self.calls.append(payload)
        return "msg_receipt_1042"


def order(status: HandoffStatus) -> OrderHandoff:
    return OrderHandoff(
        order_id="ORDER-1042",
        buyer_email="buyer@example.com",
        seller_name="Northstar Type Co.",
        item_name="Editorial font family",
        amount="49.00",
        currency="USD",
        status=status,
        assets=[SellerAsset(name="Fonts", download_url="https://example.com/fonts.zip")],
    )


def test_delivered_order_sends_receipt_with_assets_and_stable_retry_key() -> None:
    client = RecordingEmailClient()

    result = send_handoff_receipt(order(HandoffStatus.DELIVERED), client)  # type: ignore[arg-type]

    assert result.message_id == "msg_receipt_1042"
    assert client.calls[0]["to"] == "buyer@example.com"
    assert client.calls[0]["idempotency_key"] == "marketplace-receipt:ORDER-1042"
    assert "https://example.com/fonts.zip" in client.calls[0]["html"]


def test_paid_order_waits_for_seller_delivery() -> None:
    client = RecordingEmailClient()

    with pytest.raises(OrderNotDeliveredError):
        send_handoff_receipt(order(HandoffStatus.PAID), client)  # type: ignore[arg-type]

    assert client.calls == []
