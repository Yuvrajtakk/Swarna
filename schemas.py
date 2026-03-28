# schemas/schemas.py
# Pydantic models — used for request validation and response serialization
# Think of these as "contracts" for the API: what goes in and what comes out

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.models import ItemType, UnitType, BasePriceType, BookingStatus


# ─── Item Schemas ─────────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    """Schema for creating a new item (admin POST /admin/item)"""
    name: str = Field(..., min_length=1, max_length=100, example="24K Gold Bar")
    type: ItemType
    unit: UnitType
    base_price_type: BasePriceType
    margin: float = Field(default=0.0, description="Added or subtracted from base price")
    manual_price: Optional[float] = Field(None, description="Used only if base_price_type=manual")
    is_active: bool = True


class ItemUpdate(BaseModel):
    """Schema for editing an item (admin PUT /admin/item/{id})"""
    name: Optional[str] = None
    type: Optional[ItemType] = None
    unit: Optional[UnitType] = None
    base_price_type: Optional[BasePriceType] = None
    margin: Optional[float] = None
    manual_price: Optional[float] = None
    is_active: Optional[bool] = None


class ItemResponse(BaseModel):
    """Schema for returning item data to clients"""
    id: int
    name: str
    type: ItemType
    unit: UnitType
    base_price_type: BasePriceType
    margin: float
    manual_price: Optional[float]
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True   # Allows reading from SQLAlchemy model directly


class ItemWithPrice(ItemResponse):
    """Item with calculated final price appended"""
    final_price: Optional[float] = None
    price_label: Optional[str] = None   # e.g., "₹6,250 / gram"


# ─── Price Schemas ────────────────────────────────────────────────────────────

class PriceUpdate(BaseModel):
    """Admin can manually override prices"""
    metal: str = Field(..., example="gold")
    current_price: float
    prev_month: Optional[float] = None
    next_month: Optional[float] = None


class PriceResponse(BaseModel):
    id: int
    metal: str
    current_price: float
    prev_month: Optional[float]
    next_month: Optional[float]
    usd_to_inr: Optional[float]
    fetched_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Booking Schemas ──────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    """Schema for submitting a booking request (public POST /booking)"""
    customer_name: str  = Field(..., min_length=1, max_length=100)
    customer_phone: Optional[str] = Field(None, max_length=20, description="WhatsApp/phone for shop owner to contact")
    item_id: int
    quantity: float     = Field(..., gt=0)
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    customer_name: str
    customer_phone: Optional[str]
    item_id: int
    item_name: str
    price_at_booking: float
    quantity: float
    unit: str
    total_amount: float
    status: BookingStatus
    notes: Optional[str]
    created_at: Optional[datetime]
    contacted_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    suggestion: Optional[str] = None  # additive — computed in service layer, absent on non-admin routes

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    """Admin uses this to advance a booking through its lifecycle."""
    status: BookingStatus


# ─── Admin Settings Schemas ───────────────────────────────────────────────────

class AdminSettingsCreate(BaseModel):
    bank_name: Optional[str] = None
    account_no: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None
    qr_code_url: Optional[str] = None
    phone: Optional[str] = None   # WhatsApp/call contact number shown to customers


class AdminSettingsResponse(AdminSettingsCreate):
    id: int
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Generic Response ─────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    """Simple success/error message wrapper"""
    message: str
    success: bool = True
