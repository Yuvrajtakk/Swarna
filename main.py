# main.py
# Entry point for the Gold & Silver Trading API
# Run with: uvicorn main:app --reload

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from database.db import engine
from models.models import Base  # Import all models so they register with Base
from routes.public import router as public_router
from routes.admin import router as admin_router


# ─── Lifespan Event Handler ───────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    - On startup: creates all DB tables if they don't exist
    - On shutdown: cleanup (if needed)
    
    In production, use Alembic migrations instead of create_all.
    """
    print("🚀 Starting Gold & Silver Trading API...")
    Base.metadata.create_all(bind=engine)  # Auto-create tables
    print("✅ Database tables ready")
    yield  # App runs between startup and shutdown
    print("🛑 Shutting down API...")


# ─── App Initialization ───────────────────────────────────────────────────────

app = FastAPI(
    title="Gold & Silver Trading API",
    description="""
    ## A production-ready backend for a local gold & silver trading business.
    
    ### Features:
    - **Items Management** — Add/edit/disable tradeable items
    - **Live Prices** — MCX market prices with margin calculation
    - **Orders** — Customer purchase flow with price locking
    - **Admin Panel** — Full control over items, prices, orders, payments
    
    ### Authentication:
    Admin routes require `X-Api-Key` header.
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Global Exception Handlers (Task 6) ──────────────────────────────────────
# Ensures all errors return { "error": "...", "detail": "..." } consistently.

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Pydantic validation failures — return a human-readable message."""
    first = exc.errors()[0] if exc.errors() else {}
    msg   = first.get("msg", "Invalid request data")
    field = " → ".join(str(l) for l in first.get("loc", []))
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": f"{field}: {msg}" if field else msg}
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    """Catch-all for unexpected server errors — never leak stack traces."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "Something went wrong. Please try again."}
    )


# ─── CORS Middleware ──────────────────────────────────────────────────────────
# Allows the frontend (React/Flutter Web) to call the API from a browser

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # In production: specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Register Routers ─────────────────────────────────────────────────────────

app.include_router(public_router)          # /items, /prices, /order, /payment-info
app.include_router(admin_router)           # /admin/item, /admin/orders, etc.


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": "Gold & Silver Trading API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ─── Run directly (for development) ──────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
