# routes/public.py
# Public-facing API routes — no authentication required
# These are accessible by customers and the frontend app

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from schemas.schemas import ItemWithPrice, PriceResponse, BookingCreate, BookingResponse
from services import (
    get_all_items,
    get_item_final_price,
    get_all_prices,
    refresh_prices,
    create_booking,
    get_settings
)
from schemas.schemas import AdminSettingsResponse

router = APIRouter(tags=["Public"])


# ─── GET /items ───────────────────────────────────────────────────────────────

@router.get("/items", response_model=List[ItemWithPrice])
def list_items(db: Session = Depends(get_db)):
    """
    Returns all active items with their current calculated prices.
    Price is computed per item based on MCX rate + margin or manual price.
    """
    items = get_all_items(db, active_only=True)

    result = []
    for item in items:
        price_info = get_item_final_price(item, db)
        item_data = ItemWithPrice.model_validate(item)
        item_data.final_price  = price_info.get("final_price")
        item_data.price_label  = price_info.get("price_label")
        result.append(item_data)

    return result


# ─── GET /prices ──────────────────────────────────────────────────────────────

@router.get("/prices", response_model=List[PriceResponse])
def get_prices(db: Session = Depends(get_db)):
    """
    Returns current gold/silver market prices (MCX data).
    Includes current, previous month, and next month prices.
    Also triggers a refresh from mock/real MCX source.
    """
    # Refresh prices on every call (or move to a scheduler in production)
    return refresh_prices(db)


# ─── POST /booking ────────────────────────────────────────────────────────────

@router.post("/booking", response_model=BookingResponse, status_code=201)
def request_booking(data: BookingCreate, db: Session = Depends(get_db)):
    """
    Submit a booking request.
    Locks in the current indicative price. Shop owner contacts customer offline.
    """
    return create_booking(db, data)


# ─── GET /payment-info ────────────────────────────────────────────────────────

@router.get("/payment-info", response_model=AdminSettingsResponse)
def get_payment_info(db: Session = Depends(get_db)):
    """
    Returns bank/UPI payment details for the customer to complete payment.
    Publicly accessible so customer can see how to pay after placing an order.
    """
    return get_settings(db)
