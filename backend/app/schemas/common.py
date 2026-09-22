from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


def utc_now() -> datetime: return datetime.now(timezone.utc)


class Status(str, Enum):
    OK = "ok"; STALE = "stale"; PARTIAL = "partial"; UNAVAILABLE = "unavailable"; ERROR = "error"


class DataStatus(BaseModel):
    status: Status
    source: str
    timestamp: datetime = Field(default_factory=utc_now)
    is_stale: bool = False
    message: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "arthalens-api"
    version: str = "0.1.0"
    environment: str
    checks: dict[str, str]
    timestamp: datetime = Field(default_factory=utc_now)
