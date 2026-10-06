import os

from dotenv import load_dotenv


load_dotenv()


def _build_database_uri():
    """Return the SQLAlchemy database URI from the environment.

    Checks DATABASE_URL first, then falls back to SUPABASE_DB_URL.
    Normalizes Postgres-style URLs to the psycopg2 driver.
    """
    uri = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

    if not uri:
        return None

    # Normalize Postgres-style URLs to the psycopg2 driver SQLAlchemy expects.
    if uri.startswith("postgres://"):
        uri = "postgresql+psycopg2://" + uri[len("postgres://"):]
    elif uri.startswith("postgresql://"):
        uri = "postgresql+psycopg2://" + uri[len("postgresql://"):]

    return uri


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "driftbridge-dev-secret-key"
    )

    SQLALCHEMY_DATABASE_URI = _build_database_uri()

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")


        # Email / SMTP
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv(
        "MAIL_USE_TLS",
        "true"
    ).lower() == "true"
    MAIL_FROM = os.getenv(
        "MAIL_FROM",
        MAIL_USERNAME
    )