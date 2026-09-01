from fastapi import FastAPI, HTTPException

from .infrai_email import InfraiEmailClient, InfraiError
from .models import ErrorResponse, OrderHandoff, ReceiptAccepted
from .receipt_sender import OrderNotDeliveredError, send_handoff_receipt

app = FastAPI(title="Marketplace receipt handoff")


@app.post(
    "/orders/handoff",
    response_model=ReceiptAccepted,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def handoff_order(order: OrderHandoff) -> ReceiptAccepted:
    try:
        return send_handoff_receipt(order, InfraiEmailClient())
    except OrderNotDeliveredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=caller_status, detail=str(exc)) from exc
