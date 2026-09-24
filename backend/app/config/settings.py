from functools import lru_cache
from typing import Literal, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single environment-backed configuration source; secrets never leave this module."""
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")
    app_name: str = "ArthaLens"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    data_mode: Literal["mock", "live"] = "live"
    broker_provider: str = ""
    cors_origins: Any = ("http://localhost:5173",)
    database_url: str = ""
    redis_url: str = ""
    market_cache_ttl_seconds: int = 10
    option_chain_cache_ttl_seconds: int = 30
    expiry_cache_ttl_seconds: int = 3600
    max_market_data_age_seconds: int = 30
    max_option_chain_age_seconds: int = 90
    market_refresh_seconds: int = 15
    option_chain_refresh_seconds: int = 30
    expiry_refresh_seconds: int = 3600
    instrument_master_cache_seconds: int = 21600
    risk_free_rate: float = 0.065
    dividend_yield: float = 0.0
    default_lot_size: int = 1
    
    # Broker Credentials
    fyers_client_id: str = ""
    fyers_secret: str = ""
    fyers_access_token: str = ""
    angel_one_api_key: str = ""
    angel_one_client_id: str = ""
    angel_one_password: str = ""
    angel_one_totp: str = ""
    angel_one_instrument_master_url: str = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

    # News Credentials
    news_provider: str = "newsapi"
    news_api_key: str = ""

    # Telegram Credentials
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # AI / LLM Credentials
    llm_provider: str = "openai"
    
    # OpenAI Settings
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # xAI (Grok) Settings
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4.6"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | tuple[str, ...]) -> tuple[str, ...]:
        if isinstance(value, str): return tuple(item.strip() for item in value.split(",") if item.strip())
        return value

    @property
    def provider_name(self) -> str:
        return self.broker_provider.lower().strip()

    @property
    def is_broker_configured(self) -> bool:
        if self.data_mode == "mock":
            return True
        p = self.provider_name
        if p in ("angelone", "smartapi"):
            return bool(self.angel_one_api_key and self.angel_one_client_id and self.angel_one_password and self.angel_one_totp)
        if p == "fyers":
            return bool(self.fyers_client_id and self.fyers_access_token)
        return False

    @property
    def broker_configuration_status(self) -> str:
        if self.data_mode == "mock":
            return "MOCK_SIMULATION"
        provider = self.provider_name
        if not provider:
            return "MISSING_PROVIDER"
        if provider in ("angelone", "smartapi"):
            if self.angel_one_api_key and self.angel_one_client_id and self.angel_one_password and self.angel_one_totp:
                return "COMPLETE"
            return "INCOMPLETE"
        if provider == "fyers":
            if self.fyers_client_id and self.fyers_access_token:
                return "COMPLETE"
            return "INCOMPLETE"
        return "UNSUPPORTED_PROVIDER"

    @property
    def is_news_configured(self) -> bool:
        if self.data_mode == "mock":
            return True
        return bool(self.news_api_key)

    @property
    def is_database_configured(self) -> bool:
        return bool(self.database_url)

    @property
    def is_redis_configured(self) -> bool:
        return bool(self.redis_url)

    @property
    def is_telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def active_llm_api_key(self) -> str:
        provider = self.llm_provider.lower().strip()
        if provider == "xai":
            return self.xai_api_key
        elif provider == "openai":
            return self.openai_api_key
        return ""

    @property
    def active_llm_base_url(self) -> str:
        provider = self.llm_provider.lower().strip()
        if provider == "xai":
            return self.xai_base_url.rstrip("/") if self.xai_base_url else "https://api.x.ai/v1"
        elif provider == "openai":
            return self.openai_base_url.rstrip("/") if self.openai_base_url else "https://api.openai.com/v1"
        return ""

    @property
    def active_llm_model(self) -> str:
        provider = self.llm_provider.lower().strip()
        if provider == "xai":
            return self.xai_model or "grok-4.6"
        elif provider == "openai":
            return self.openai_model or "gpt-4o"
        return ""

    @property
    def is_llm_configured(self) -> bool:
        return bool(self.active_llm_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
