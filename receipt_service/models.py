from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class HandoffStatus(str, Enum):
    PAID = "paid"
    DELIVERED = "delivered"


class SellerAsset(BaseModel):
    name: str = Field(min_length=1)
    download_url: HttpUrl


class BuyerUpdate(BaseModel):
    message: str = Field(min_length=1)


class OrderHandoff(BaseModel):
    order_id: str = Field(min_length=1)
    buyer_email: EmailStr
    seller_name: str = Field(min_length=1)
    item_name: str = Field(min_length=1)
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    status: HandoffStatus
    assets: list[SellerAsset] = Field(min_length=1)
    buyer_updates: list[BuyerUpdate] = Field(default_factory=list)


class ReceiptAccepted(BaseModel):
    order_id: str
    message_id: str
    handoff_status: HandoffStatus


class ErrorResponse(BaseModel):
    detail: str
    code: str
