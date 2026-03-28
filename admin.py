# routes/admin.py
# Admin-only API routes
# In production: protect these with JWT authentication middleware

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database.db import get_db
from schemas.schemas import (
    ItemCreate, ItemUpdate, ItemResponse,
    PriceUpdate, PriceResponse,
    BookingResponse, BookingStatusUpdate,
    AdminSettingsCreate, AdminSettingsResponse,
    MessageResponse
)
from services import (
    get_all_items, create_item, update_item, delete_item,
    admin_update_price, get_all_prices,
    get_all_bookings, advance_booking_status,
    get_settings, upsert_settings
)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Simple API Key Guard ─────────────────────────────────────────────────────
# In production: replace with proper JWT auth (e.g., FastAPI-Users or OAuth2)

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "secret-admin-key-change-me")

def verify_admin(x_api_key: Optional[str] = Header(None)):
    """
    Basic API key authentication for admin routes.
    Pass as: Header → X-Api-Key: your-key
    
    Replace this with JWT/OAuth2 in production.
    """
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key")
    return True


# ─── Item Management ──────────────────────────────────────────────────────────

@router.get("/items", response_model=List[ItemResponse])
def admin_list_items(db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    """Admin view: all items including disabled ones."""
    return get_all_items(db, active_only=False)


@router.post("/item", response_model=ItemResponse, status_code=201)
def admin_create_item(
    data: ItemCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Create a new tradeable item."""
    return create_item(db, data)


@router.put("/item/{item_id}", response_model=ItemResponse)
def admin_update_item(
    item_id: int,
    data: ItemUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Update item details. Only send fields you want to change."""
    return update_item(db, item_id, data)


@router.delete("/item/{item_id}", response_model=MessageResponse)
def admin_delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """
    Soft-deletes an item (sets is_active=False).
    Item won't appear publicly but order history is preserved.
    """
    return delete_item(db, item_id)


# ─── Price Management ─────────────────────────────────────────────────────────

@router.get("/prices", response_model=List[PriceResponse])
def admin_get_prices(db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    """View currently stored prices."""
    return get_all_prices(db)


@router.put("/prices", response_model=PriceResponse)
def admin_set_price(
    data: PriceUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Manually override MCX prices for a specific metal."""
    return admin_update_price(db, data)


# ─── Booking Management ───────────────────────────────────────────────────────

@router.get("/bookings", response_model=List[BookingResponse])
def admin_get_bookings(db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    """All booking requests, newest first."""
    return get_all_bookings(db)


@router.put("/bookings/{booking_id}/status", response_model=BookingResponse)
def admin_update_booking_status(
    booking_id: int,
    data: BookingStatusUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """
    Advance a booking through its lifecycle.
    Valid statuses: requested → contacted → confirmed → completed
    contacted_at and confirmed_at are auto-stamped on first transition.
    """
    return advance_booking_status(db, booking_id, data)


# ─── Admin Settings (Payment Info) ───────────────────────────────────────────

@router.get("/settings", response_model=AdminSettingsResponse)
def admin_get_settings(db: Session = Depends(get_db), _: bool = Depends(verify_admin)):
    """View current payment/business settings."""
    return get_settings(db)


@router.post("/settings", response_model=AdminSettingsResponse)
def admin_save_settings(
    data: AdminSettingsCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Create or update bank/UPI payment details."""
    return upsert_settings(db, data)
