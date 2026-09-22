import logging
import httpx
from app.config.settings import Settings

logger = logging.getLogger("arthalens.llm")


class LLMService:
    """Provider-independent LLM service supporting xAI (Grok) and OpenAI."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.llm_provider.lower().strip()
        self.api_key = settings.active_llm_api_key
        self.base_url = settings.active_llm_base_url
        self.model = settings.active_llm_model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout_seconds: float = 15.0,
    ) -> dict:
        """Sends a completion request to the active LLM provider via OpenAI-compatible endpoint."""
        if not self.is_configured:
            logger.warning("LLM request skipped: Provider '%s' is missing API credentials.", self.provider)
            return {
                "status": "unavailable",
                "provider": self.provider,
                "model": self.model,
                "message": f"LLM provider '{self.provider}' is not configured.",
                "content": None,
            }

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            logger.info("Sending LLM completion request to provider='%s' model='%s' endpoint='%s'", self.provider, self.model, endpoint)
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                
                if resp.status_code != 200:
                    logger.error("LLM request failed status_code=%d response=%s", resp.status_code, resp.text[:200])
                    return {
                        "status": "error",
                        "provider": self.provider,
                        "model": self.model,
                        "message": f"API request failed with HTTP {resp.status_code}",
                        "content": None,
                    }

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return {
                        "status": "error",
                        "provider": self.provider,
                        "model": self.model,
                        "message": "No choices returned by LLM provider.",
                        "content": None,
                    }

                content = choices[0].get("message", {}).get("content", "")
                return {
                    "status": "ok",
                    "provider": self.provider,
                    "model": self.model,
                    "content": content,
                    "usage": data.get("usage", {}),
                }

        except Exception as exc:
            logger.exception("Unexpected error during LLM call for provider='%s'", self.provider)
            return {
                "status": "error",
                "provider": self.provider,
                "model": self.model,
                "message": f"LLM execution error: {type(exc).__name__}",
                "content": None,
            }
