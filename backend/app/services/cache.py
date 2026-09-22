from time import monotonic
from typing import TypeVar
from pydantic import BaseModel
from redis.asyncio import Redis

T = TypeVar("T", bound=BaseModel)

class Cache:
    """Redis-ready interface with a safe in-process fallback for local development."""
    def __init__(self, redis_url: str = ""): self._memory: dict[str, tuple[float, str]] = {}; self.redis_url = redis_url; self.redis: Redis | None = None; self.status = "not_configured"
    async def connect(self) -> None:
        if not self.redis_url: return
        try:
            self.redis = Redis.from_url(self.redis_url, decode_responses=True); await self.redis.ping(); self.status = "ok"
        except Exception: self.redis = None; self.status = "unavailable"
    async def close(self) -> None:
        if self.redis: await self.redis.aclose()
    async def get(self, key: str, model: type[T]) -> T | None:
        if self.redis:
            value = await self.redis.get(key)
            if value: return model.model_validate_json(value)
        entry = self._memory.get(key)
        return model.model_validate_json(entry[1]) if entry and entry[0] >= monotonic() else None
    async def set(self, key: str, value: BaseModel, ttl_seconds: int) -> None:
        payload = value.model_dump_json(); self._memory[key] = (monotonic() + ttl_seconds, payload)
        if self.redis: await self.redis.set(key, payload, ex=ttl_seconds)
