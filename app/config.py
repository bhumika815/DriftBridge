import os

from dotenv import load_dotenv


load_dotenv()


def _build_database_uri():
    """Return the SQLAlchemy database URI from the environment.

    DriftBridge is designed for MySQL (mysql+pymysql://...). If a
    Supabase/Postgres DATABASE_URL is provided in the environment, we
    transparently rewrite it to the psycopg2 driver so the same code
    runs in both local MySQL and hosted Postgres environments without
    hard-coding credentials.
    """
    uri = os.getenv("DATABASE_URL")
    if not uri:
        return None

    # Normalize Postgres-style URLs to the psycopg2 driver SQLAlchemy expects.
    if uri.startswith("postgres://"):
        uri = "postgresql+psycopg2://" + uri[len("postgres://"):]
    elif uri.startswith("postgresql://"):
        uri = "postgresql+psycopg2://" + uri[len("postgresql://"):]

    return uri


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "driftbridge-dev-secret-key")

    SQLALCHEMY_DATABASE_URI = _build_database_uri()

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
