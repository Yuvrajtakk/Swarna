# services/booking_service.py
# Business logic for managing booking requests.
# These are NOT confirmed sales — just customer intent captured online.
# The shop owner follows up via WhatsApp/phone and closes offline.

from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import Booking, BookingStatus, Item
from schemas.schemas import BookingCreate, BookingStatusUpdate
from services.price_service import get_item_final_price


# Task 5: Enforce linear lifecycle — no skipping states.
ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "requested": ["contacted"],
    "contacted": ["confirmed"],
    "confirmed": ["completed"],
    "completed": [],           # terminal state
}


def create_booking(db: Session, data: BookingCreate) -> Booking:
    """
    Records a new booking request from a customer.
    Price is locked at this moment (indicative — actual deal happens offline).
    Status starts as 'requested'; shop owner advances it manually.
    """
    item = db.query(Item).filter(Item.id == data.item_id, Item.is_active == True).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item not found or currently unavailable (id={data.item_id})"
        )

    # ── Task 1: Duplicate booking protection ─────────────────────────────────
    # Prevent same phone + same item within the last 10 minutes.
    # Guard: only meaningful when a phone is provided — NULL phone cannot
    # identify a customer, so matching on NULL would incorrectly group all
    # anonymous users together and block legitimate distinct bookings.
    if data.customer_phone:
        recent_booking = db.query(Booking).filter(
            Booking.customer_phone == data.customer_phone,
            Booking.item_id == data.item_id,
            Booking.created_at >= datetime.now(timezone.utc) - timedelta(minutes=10)
        ).first()

        if recent_booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already requested this item recently. Please wait before trying again."
            )
    # ─────────────────────────────────────────────────────────────────────────

    price_info  = get_item_final_price(item, db)
    final_price = price_info.get("final_price")

    if final_price is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Price for '{item.name}' is temporarily unavailable. Please try again shortly."
        )

    booking = Booking(
        customer_name    = data.customer_name,
        customer_phone   = data.customer_phone,
        item_id          = item.id,
        item_name        = item.name,
        price_at_booking = final_price,
        quantity         = data.quantity,
        unit             = item.unit.value,
        total_amount     = round(final_price * data.quantity, 2),
        notes            = data.notes,
        status           = BookingStatus.requested,
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    # ── Task 2: Console logging after successful commit ───────────────────────
    print(f"[BOOKING CREATED] phone={data.customer_phone} item={data.item_id} time={datetime.now(timezone.utc)}")
    # ─────────────────────────────────────────────────────────────────────────

    return booking


def get_all_bookings(db: Session) -> List[dict]:
    """
    Admin: all bookings, newest first.
    Task 4: Returns dicts with an extra 'suggestion' field for admin action guidance.
    All existing BookingResponse fields are preserved — no schema changes needed.
    """
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    return [_booking_with_suggestion(b) for b in bookings]


def _get_suggestion(status: str) -> str:
    """Return a short actionable hint for the admin based on booking status."""
    if status == "requested":
        return "Call now"
    elif status == "contacted":
        return "Follow up"
    elif status == "confirmed":
        return "Prepare order"
    return ""


def _booking_with_suggestion(b: Booking) -> dict:
    """
    Convert a Booking ORM object to a dict and append the 'suggestion' field.
    All original fields are kept intact so the frontend never breaks.
    """
    return {
        "id":               b.id,
        "customer_name":    b.customer_name,
        "customer_phone":   b.customer_phone,
        "item_id":          b.item_id,
        "item_name":        b.item_name,
        "price_at_booking": b.price_at_booking,
        "quantity":         b.quantity,
        "unit":             b.unit,
        "total_amount":     b.total_amount,
        "status":           b.status,
        "notes":            b.notes,
        "created_at":       b.created_at,
        "contacted_at":     b.contacted_at,
        "confirmed_at":     b.confirmed_at,
        # ── Task 4: extra field — safe, additive only ──
        "suggestion":       _get_suggestion(b.status.value),
    }


def get_booking_by_id(db: Session, booking_id: int) -> Booking:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking #{booking_id} not found"
        )
    return booking


def advance_booking_status(db: Session, booking_id: int, data: BookingStatusUpdate) -> Booking:
    """
    Advance a booking through its lifecycle.
    Task 5: Rejects invalid/skipped transitions with a clear error.
    Task 6: Returns descriptive HTTPException messages.
    Auto-stamps contacted_at and confirmed_at on first transition.
    """
    booking   = get_booking_by_id(db, booking_id)
    current   = booking.status.value
    requested = data.status.value

    # Task 5: Guard against invalid transitions
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    if requested not in allowed:
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking #{booking_id} is already completed — no further changes allowed."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot move booking from '{current}' to '{requested}'. "
                f"Next allowed status: '{allowed[0]}'"
            )
        )

    now = datetime.now(timezone.utc)
    booking.status = data.status

    if data.status == BookingStatus.contacted and booking.contacted_at is None:
        booking.contacted_at = now
    if data.status == BookingStatus.confirmed and booking.confirmed_at is None:
        booking.confirmed_at = now

    db.commit()
    db.refresh(booking)
    return booking
