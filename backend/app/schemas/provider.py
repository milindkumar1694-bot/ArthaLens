from datetime import datetime
from pydantic import BaseModel
from .common import Status


class ProviderStatus(BaseModel):
    provider: str
    configured: bool
    connected: bool
    status: Status
    message: str | None = None
    last_success: datetime | None = None
