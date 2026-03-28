# services/price_service.py
# Handles fetching, storing, and calculating gold/silver prices

from sqlalchemy.orm import Session
from typing import List, Dict
from fastapi import HTTPException

from models.models import Price, Item
from schemas.schemas import PriceUpdate
from utils.price_fetcher import (
    fetch_mcx_prices,
    fetch_usd_to_inr,
    calculate_final_price,
    format_price_label
)


def refresh_prices(db: Session) -> List[Price]:
    """
    Fetches fresh MCX + USD/INR data and stores/updates it in the DB.
    Called by a background task or manually by admin via PUT /admin/prices.
    """
    mcx_data = fetch_mcx_prices()
    usd_inr = fetch_usd_to_inr()

    results = []

    for metal, price_data in mcx_data.items():
        # Check if we already have a record for this metal
        existing = db.query(Price).filter(Price.metal == metal).first()

        if existing:
            # Update existing record
            existing.current_price = price_data["current_price"]
            existing.prev_month    = price_data["prev_month"]
            existing.next_month    = price_data["next_month"]
            existing.usd_to_inr   = usd_inr
            results.append(existing)
        else:
            # Create new record
            new_price = Price(
                metal         = metal,
                current_price = price_data["current_price"],
                prev_month    = price_data["prev_month"],
                next_month    = price_data["next_month"],
                usd_to_inr    = usd_inr
            )
            db.add(new_price)
            results.append(new_price)

    db.commit()
    for r in results:
        db.refresh(r)

    return results


def get_all_prices(db: Session) -> List[Price]:
    """Returns all stored metal prices from DB."""
    return db.query(Price).all()


def get_price_by_metal(db: Session, metal: str) -> Price:
    """Returns price record for a specific metal (gold or silver)."""
    price = db.query(Price).filter(Price.metal == metal.lower()).first()
    if not price:
        raise HTTPException(status_code=404, detail=f"Price for '{metal}' not found. Try refreshing prices.")
    return price


def admin_update_price(db: Session, data: PriceUpdate) -> Price:
    """
    Admin can manually override prices (when MCX API is down or for manual control).
    """
    existing = db.query(Price).filter(Price.metal == data.metal.lower()).first()

    if existing:
        existing.current_price = data.current_price
        if data.prev_month is not None:
            existing.prev_month = data.prev_month
        if data.next_month is not None:
            existing.next_month = data.next_month
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_price = Price(
            metal         = data.metal.lower(),
            current_price = data.current_price,
            prev_month    = data.prev_month,
            next_month    = data.next_month,
        )
        db.add(new_price)
        db.commit()
        db.refresh(new_price)
        return new_price


def get_item_final_price(item: Item, db: Session) -> Dict:
    """
    Calculates the final price for a given item based on its pricing type.
    
    Logic:
      - If base_price_type = 'manual' → use item.manual_price as base
      - If base_price_type = 'mcx'    → look up MCX price by item.type
      Then: final_price = base_price + item.margin
    """
    base_price = None

    if item.base_price_type.value == "manual":
        base_price = item.manual_price
    else:
        # Fetch latest MCX price for the item's metal type
        price_record = db.query(Price).filter(
            Price.metal == item.type.value  # "gold" or "silver"
        ).first()

        if price_record:
            base_price = price_record.current_price

    if base_price is None:
        return {"final_price": None, "price_label": "Price unavailable"}

    final = calculate_final_price(base_price, item.margin)
    label = format_price_label(final, item.unit.value)

    return {"final_price": final, "price_label": label}
