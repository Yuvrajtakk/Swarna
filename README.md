# ⚜ Swarna — Gold & Silver Trading App

A production-ready backend + frontend for a local gold & silver trading business.

---

## 📁 Project Structure

```
gold-silver-app/
│
├── backend/
│   ├── main.py                    ← FastAPI entry point
│   ├── requirements.txt
│   ├── .env.example               ← Copy to .env and fill values
│   │
│   ├── database/
│   │   ├── db.py                  ← SQLAlchemy engine + session
│   │   ├── init_db.py             ← Run once to create tables
│   │   └── seed.py                ← Sample data for testing
│   │
│   ├── models/
│   │   └── models.py              ← ORM models: Item, Price, Order, AdminSettings
│   │
│   ├── schemas/
│   │   └── schemas.py             ← Pydantic request/response schemas
│   │
│   ├── routes/
│   │   ├── public.py              ← GET /items, /prices, POST /order
│   │   └── admin.py               ← /admin/* routes (API key protected)
│   │
│   ├── services/
│   │   ├── item_service.py        ← Item CRUD logic
│   │   ├── price_service.py       ← Price fetch + calculation
│   │   ├── order_service.py       ← Order placement logic
│   │   └── settings_service.py    ← Admin settings
│   │
│   └── utils/
│       └── price_fetcher.py       ← MCX mock + USD/INR + price calculator
│
└── frontend/
    └── index.html                 ← Full React UI (single file, zero build step)
```

---

## 🚀 Quick Start

### 1. Set up PostgreSQL

```bash
# Create database
psql -U postgres
CREATE DATABASE gold_silver_db;
\q
```

### 2. Configure environment

```bash
cd backend
cp .env.example .env
# Edit .env with your DB credentials and admin key
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create tables & seed data

```bash
python database/init_db.py   # Create tables
python database/seed.py      # Load sample items + settings
```

### 5. Run the backend

```bash
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 6. Open the frontend

```bash
# Just open frontend/index.html in a browser
# Or serve with any static server:
npx serve frontend/
```

---

## 🔌 API Reference

### Public Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Health check |
| GET | `/items` | All active items with calculated prices |
| GET | `/prices` | MCX gold/silver prices + USD/INR |
| POST | `/order` | Place a customer order |
| GET | `/payment-info` | Payment details (bank, UPI) |

### Admin Endpoints (require `X-Api-Key` header)

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/admin/items` | All items (including disabled) |
| POST | `/admin/item` | Create new item |
| PUT | `/admin/item/{id}` | Update item |
| DELETE | `/admin/item/{id}` | Soft-delete (disable) item |
| GET | `/admin/prices` | View stored prices |
| PUT | `/admin/prices` | Override prices manually |
| GET | `/admin/orders` | All orders |
| PUT | `/admin/orders/{id}/status` | Update payment status |
| GET | `/admin/settings` | View payment settings |
| POST | `/admin/settings` | Update payment settings |

---

## 📦 Sample Requests

### Place Order
```json
POST /order
{
  "customer_name": "Rahul Sharma",
  "customer_phone": "9876543210",
  "item_id": 1,
  "quantity": 10,
  "notes": "Urgent delivery"
}
```

### Add Item (Admin)
```json
POST /admin/item
Headers: X-Api-Key: your-key

{
  "name": "24K Gold Bar (10g)",
  "type": "gold",
  "unit": "gram",
  "base_price_type": "mcx",
  "margin": 150,
  "is_active": true
}
```

### Update Payment Settings (Admin)
```json
POST /admin/settings
{
  "bank_name": "State Bank of India",
  "account_no": "1234567890",
  "ifsc_code": "SBIN0001234",
  "upi_id": "goldshop@upi",
  "qr_code_url": "https://yoursite.com/qr.png"
}
```

---

## 💡 Price Logic

```
if item.base_price_type == "mcx":
    base = latest MCX price for gold/silver
elif item.base_price_type == "manual":
    base = item.manual_price

final_price = base + item.margin   ← margin can be negative (discount)
```

---

## 🔒 Security Notes

- In production, replace the simple `X-Api-Key` with **JWT authentication**
- Use **Alembic** for database migrations instead of `create_all`
- Store secrets in environment variables, never in code
- Replace mock price functions with real MCX/Forex API calls
- Set `allow_origins` in CORS to your actual frontend domain

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Server | Uvicorn (ASGI) |
| Frontend | React 18 (CDN, no build step) |
| Fonts | Cormorant Garamond + DM Mono + Outfit |
