from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
import os
import traceback
import asyncio

from app.api.routes import auth, users, workers, bookings, reviews, addresses, admin, catalog, membership, payments
from app.db.database import engine, Base, SessionLocal
from app.core.config import settings
from app.services.referral_service import ensure_referral_codes

# Initialize database schema
Base.metadata.create_all(bind=engine)

def auto_migrate():
    """Applies lightweight schema migrations for existing local databases."""
    with engine.begin() as conn:
        dialect = engine.dialect.name
        # User table columns
        for col_name in ["dob", "gender", "offered_services", "referral_code", "availability"]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} VARCHAR"))
            except Exception:
                pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN referral_points INTEGER DEFAULT 0"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_online INTEGER DEFAULT 1"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN referral_earnings INTEGER DEFAULT 0"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN verification_status VARCHAR(20) DEFAULT 'approved'"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN profile_photo VARCHAR(1000)"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0"))
        except Exception:
            pass
        try:
            conn.execute(text("CREATE UNIQUE INDEX ix_users_referral_code ON users (referral_code)"))
        except Exception:
            pass
        # Booking table columns
        timestamp_type = "TIMESTAMPTZ" if dialect == "postgresql" else "DATETIME"
        for col_name, col_type in [
            ("start_otp", "VARCHAR(6)"),
            ("end_otp", "VARCHAR(6)"),
            ("amount", "VARCHAR(20)"),
            ("discount_code", "VARCHAR(50)"),
            ("discount_amount", "VARCHAR(20)"),
            ("updated_at", timestamp_type),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE bookings ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass

auto_migrate()

with SessionLocal() as db:
    ensure_referral_codes(db)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:4000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:4000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Local fallback for catalog uploads (PC → WebP) when R2 is not configured.
# Files land in backend/static/catalog/<uuid>.webp and are served at /static/...
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(os.path.join(STATIC_DIR, "catalog"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] Uncaught exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal Server Error"},
    )

# Include Router Modules
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Panel"])
app.include_router(catalog.router, prefix="/api", tags=["Catalog"])
app.include_router(membership.router, prefix="/api/membership", tags=["Membership"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(users.router, prefix="/api/users", tags=["Users Profile"])
app.include_router(workers.router, prefix="/api/workers", tags=["Worker Marketplace"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews & Feedback"])
app.include_router(addresses.router, prefix="/api/addresses", tags=["Saved Addresses"])

@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }
