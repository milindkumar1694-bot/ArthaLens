import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.config.settings import Settings
from app.config.validator import validate_production_config
from app.services.llm import LLMService
from app.main import app


def test_xai_provider_settings():
    settings = Settings(
        LLM_PROVIDER="xai",
        XAI_API_KEY="xai-secret-key-123",
        XAI_BASE_URL="https://api.x.ai/v1",
        XAI_MODEL="grok-4.6",
    )
    assert settings.llm_provider == "xai"
    assert settings.active_llm_api_key == "xai-secret-key-123"
    assert settings.active_llm_base_url == "https://api.x.ai/v1"
    assert settings.active_llm_model == "grok-4.6"
    assert settings.is_llm_configured is True


def test_openai_provider_settings():
    settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-openai-secret-456",
        OPENAI_BASE_URL="https://api.openai.com/v1",
        OPENAI_MODEL="gpt-4o",
    )
    assert settings.llm_provider == "openai"
    assert settings.active_llm_api_key == "sk-openai-secret-456"
    assert settings.active_llm_base_url == "https://api.openai.com/v1"
    assert settings.active_llm_model == "gpt-4o"
    assert settings.is_llm_configured is True


def test_startup_validation_xai_provider():
    # Unconfigured XAI
    unconfig_settings = Settings(DATA_MODE="live", LLM_PROVIDER="xai", XAI_API_KEY="")
    status_unconfig = validate_production_config(unconfig_settings)
    assert status_unconfig["llm"] == "UNCONFIGURED (XAI_API_KEY missing)"

    # Configured XAI
    config_settings = Settings(DATA_MODE="live", LLM_PROVIDER="xai", XAI_API_KEY="xai-test-key")
    status_config = validate_production_config(config_settings)
    assert status_config["llm"] == "CONFIGURED (XAI)"


def test_startup_validation_openai_provider():
    # Unconfigured OpenAI
    unconfig_settings = Settings(DATA_MODE="live", LLM_PROVIDER="openai", OPENAI_API_KEY="")
    status_unconfig = validate_production_config(unconfig_settings)
    assert status_unconfig["llm"] == "UNCONFIGURED (OPENAI_API_KEY missing)"

    # Configured OpenAI
    config_settings = Settings(DATA_MODE="live", LLM_PROVIDER="openai", OPENAI_API_KEY="sk-openai-key")
    status_config = validate_production_config(config_settings)
    assert status_config["llm"] == "CONFIGURED (OPENAI)"


@pytest.mark.asyncio
async def test_llm_service_xai_completion():
    settings = Settings(
        LLM_PROVIDER="xai",
        XAI_API_KEY="xai-test-key",
        XAI_BASE_URL="https://api.x.ai/v1",
        XAI_MODEL="grok-4.6",
    )
    service = LLMService(settings)
    assert service.is_configured is True

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Grok market analysis"}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 20},
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await service.generate_completion(
            prompt="Analyze option chain PCR 1.2",
            system_prompt="You are a market analyst",
        )

        assert result["status"] == "ok"
        assert result["provider"] == "xai"
        assert result["model"] == "grok-4.6"
        assert result["content"] == "Grok market analysis"

        # Verify call parameters
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        call_kwargs = mock_post.call_args[1]
        assert call_url == "https://api.x.ai/v1/chat/completions"
        assert call_kwargs["headers"]["Authorization"] == "Bearer xai-test-key"
        assert call_kwargs["json"]["model"] == "grok-4.6"
        assert call_kwargs["json"]["messages"][0] == {"role": "system", "content": "You are a market analyst"}
        assert call_kwargs["json"]["messages"][1] == {"role": "user", "content": "Analyze option chain PCR 1.2"}


@pytest.mark.asyncio
async def test_llm_service_openai_completion():
    settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-openai-key",
        OPENAI_BASE_URL="https://api.openai.com/v1",
        OPENAI_MODEL="gpt-4o",
    )
    service = LLMService(settings)
    assert service.is_configured is True

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "OpenAI market analysis"}}],
        "usage": {"prompt_tokens": 15, "completion_tokens": 25},
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await service.generate_completion(prompt="Summarize Fed announcement")

        assert result["status"] == "ok"
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4o"
        assert result["content"] == "OpenAI market analysis"

        call_url = mock_post.call_args[0][0]
        call_kwargs = mock_post.call_args[1]
        assert call_url == "https://api.openai.com/v1/chat/completions"
        assert call_kwargs["headers"]["Authorization"] == "Bearer sk-openai-key"
        assert call_kwargs["json"]["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_llm_service_unconfigured_returns_unavailable():
    settings = Settings(LLM_PROVIDER="xai", XAI_API_KEY="")
    service = LLMService(settings)
    assert service.is_configured is False

    result = await service.generate_completion(prompt="Test prompt")
    assert result["status"] == "unavailable"
    assert result["content"] is None
    assert "not configured" in result["message"]


def test_health_endpoint_masks_llm_credentials():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        checks = response.json().get("checks", {})
        assert "llm" in checks
        for val in checks.values():
            assert "xai-" not in str(val)
            assert "sk-" not in str(val)
