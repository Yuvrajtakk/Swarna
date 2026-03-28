# models/models.py
# SQLAlchemy ORM models — each class maps to a database table

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from database.db import Base
import enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class ItemType(str, enum.Enum):
    gold = "gold"
    silver = "silver"
    other = "other"

class UnitType(str, enum.Enum):
    gram = "gram"
    kg = "kg"
    piece = "piece"

class BasePriceType(str, enum.Enum):
    mcx = "mcx"          # Fetched from MCX market data
    manual = "manual"    # Admin sets it manually

class BookingStatus(str, enum.Enum):
    """
    Reflects the real-world workflow of a local bullion shop:
    - requested  : Customer submitted the booking form online
    - contacted  : Shop owner called/WhatsApp'd the customer
    - confirmed  : Customer confirmed they're coming / deal is agreed
    - completed  : Physical transaction done, gold/silver handed over
    """
    requested  = "requested"
    contacted  = "contacted"
    confirmed  = "confirmed"
    completed  = "completed"


# ─── Item Model ───────────────────────────────────────────────────────────────

class Item(Base):
    """
    Represents a tradeable item like gold bar, silver coin, etc.
    Admin can add/edit/disable items.
    """
    __tablename__ = "items"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(100), nullable=False)                  # e.g., "24K Gold Bar"
    type           = Column(Enum(ItemType), nullable=False)               # gold / silver / other
    unit           = Column(Enum(UnitType), nullable=False)               # gram / kg / piece
    base_price_type = Column(Enum(BasePriceType), nullable=False)        # mcx or manual
    margin         = Column(Float, default=0.0)                           # ± applied to base price
    manual_price   = Column(Float, nullable=True)                         # used if base_price_type=manual
    is_active      = Column(Boolean, default=True)                        # soft delete / disable
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())


# ─── Price Model ──────────────────────────────────────────────────────────────

class Price(Base):
    """
    Stores MCX market prices for gold and silver.
    Supports current, next month, and previous month prices.
    """
    __tablename__ = "prices"

    id             = Column(Integer, primary_key=True, index=True)
    metal          = Column(String(20), nullable=False)   # "gold" or "silver"
    current_price  = Column(Float, nullable=False)
    prev_month     = Column(Float, nullable=True)
    next_month     = Column(Float, nullable=True)
    usd_to_inr     = Column(Float, nullable=True)         # USD → INR rate at time of fetch
    fetched_at     = Column(DateTime(timezone=True), server_default=func.now())


# ─── Booking Model ────────────────────────────────────────────────────────────

class Booking(Base):
    """
    Represents a customer order REQUEST — not a confirmed sale.
    Payment happens offline (UPI / cash). This just tracks the intent.
    
    Lifecycle: requested → contacted → confirmed → completed
    """
    __tablename__ = "bookings"

    id                = Column(Integer, primary_key=True, index=True)
    customer_name     = Column(String(100), nullable=False)
    customer_phone    = Column(String(20), nullable=True)
    item_id           = Column(Integer, nullable=False)      # ref to items table
    item_name         = Column(String(100), nullable=False)  # snapshot at booking time
    price_at_booking  = Column(Float, nullable=False)        # locked MCX price at time of request
    quantity          = Column(Float, nullable=False)
    unit              = Column(String(20), nullable=False)
    total_amount      = Column(Float, nullable=False)         # price_at_booking × quantity (indicative)
    status            = Column(Enum(BookingStatus), default=BookingStatus.requested)
    notes             = Column(Text, nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    contacted_at      = Column(DateTime(timezone=True), nullable=True)  # when shop owner reached out
    confirmed_at      = Column(DateTime(timezone=True), nullable=True)  # when deal was confirmed


# ─── Admin Settings Model ─────────────────────────────────────────────────────

class AdminSettings(Base):
    """
    Stores payment and business configuration for the admin.
    Single-row table (id=1 always). Use upsert pattern.
    """
    __tablename__ = "admin_settings"

    id          = Column(Integer, primary_key=True, default=1)
    bank_name   = Column(String(100), nullable=True)
    account_no  = Column(String(50), nullable=True)
    ifsc_code   = Column(String(20), nullable=True)
    upi_id      = Column(String(100), nullable=True)
    qr_code_url = Column(String(300), nullable=True)   # URL to QR code image
    phone       = Column(String(20), nullable=True)    # WhatsApp/call contact number
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())
