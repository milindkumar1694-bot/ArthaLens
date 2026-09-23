import pytest

from app.services.cache import Cache


class _BrokenRedis:
    async def ping(self):
        raise RuntimeError("redis unavailable")


@pytest.mark.asyncio
async def test_redis_unavailable_state(monkeypatch):
    monkeypatch.setattr("app.services.cache.Redis.from_url", lambda *args, **kwargs: _BrokenRedis())
    cache = Cache("redis://localhost:6379/0")

    await cache.connect()

    assert cache.status == "unavailable"
    assert cache.redis is None
