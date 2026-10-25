import os
from pydantic_settings import BaseSettings

def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    neon_host = os.getenv("NEON_HOST")
    neon_password = os.getenv("NEON_PASSWORD")
    neon_user = os.getenv("NEON_USER", "neondb_owner")
    neon_db = os.getenv("NEON_DB", "neondb")
    if neon_host and neon_password:
        return f"postgresql://{neon_user}:{neon_password}@{neon_host}/{neon_db}?sslmode=require"
    return "sqlite:///./kazilen.db"

def get_redis_url() -> str:
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return redis_url
    redis_host = os.getenv("REDIS_HOST")
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_port = os.getenv("REDIS_PORT", "6379")
    if redis_host:
        if redis_password:
            return f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
        return f"redis://{redis_host}:{redis_port}/0"
    return "redis://localhost:6379/0"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Kazilen Backend"
    SECRET_KEY: str = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "super-secret-key-for-local-dev"
    JWT_SECRET: str = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "super-secret-key-for-local-dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # Set to "true" in production (HTTPS) so the auth cookie is only sent over secure connections
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    REDIS_URL: str = get_redis_url()
    DATABASE_URL: str = get_database_url()

    # Membership / quota enforcement: free bookings per worker before a
    # subscription is required. Override with FREE_BOOKINGS env var.
    FREE_BOOKINGS: int = int(os.getenv("FREE_BOOKINGS", "2"))

    # =========================================================================
    # OTP DELIVERY PROVIDER CONFIGURATION
    # Options: "console" (Dev), "whatsapp" (Meta), "twilio" (SMS), "custom" (HTTP API)
    # =========================================================================
    OTP_PROVIDER: str = os.getenv("OTP_PROVIDER", "console")

    # Meta WhatsApp Cloud API Settings
    # Get these from https://developers.facebook.com/
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_TEMPLATE_NAME: str = os.getenv("WHATSAPP_TEMPLATE_NAME", "kazilen_otp")

    # Twilio SMS API Settings
    # Get these from https://console.twilio.com/
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID") or os.getenv("ACCOUNT_SID") or ""
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN") or os.getenv("AUTH_TOKEN") or ""
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER") or os.getenv("COMPANY_NUMBER") or ""

    # Custom HTTP / SMS Gateway Settings (e.g., MSG91, Fast2SMS, Infobip, AWS SNS)
    SMS_GATEWAY_URL: str = os.getenv("SMS_GATEWAY_URL", "")
    SMS_GATEWAY_API_KEY: str = os.getenv("SMS_GATEWAY_API_KEY", "")

    # =========================================================================
    # CLOUDFLARE R2 OBJECT STORAGE (worker profile photos, S3-compatible)
    # Get these from https://dash.cloudflare.com/ → R2 → Manage R2 API Tokens
    # Public bucket must allow public read (r2.dev domain or custom domain).
    # =========================================================================
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_PUBLIC_BUCKET_NAME: str = os.getenv("R2_PUBLIC_BUCKET_NAME", "")
    R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "").rstrip("/")

    # =========================================================================
    # RAZORPAY (worker membership payments — online option alongside manual)
    # Test keys start with rzp_test_, live with rzp_live_. Webhook secret is
    # set in the Razorpay dashboard when registering /api/payments/webhook.
    # =========================================================================
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    # =========================================================================
    # ADMIN PANEL AUTHENTICATION (bcrypt + JWT, env-driven single admin)
    # =========================================================================
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@kazilen.com")
    # Plain fallback password (dev convenience only).
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    # bcrypt hash of the admin password — PRIMARY secure credential.
    # Generate with: python -c "import bcrypt; print(bcrypt.hashpw(b'<pw>', bcrypt.gensalt()).decode())"
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
