from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def create_database_engine(database_url: str) -> Engine | None:
    if not database_url:
        return None
    # Normalize postgres:// to postgresql:// for Render PostgreSQL compatibility
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return create_engine(database_url, pool_pre_ping=True)


def database_check(engine: Engine | None) -> str:
    if engine is None:
        return "not_configured"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unavailable"
