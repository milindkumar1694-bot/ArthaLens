from app.config.settings import Settings

def test_defaults_and_optional_credentials():
    settings = Settings()
    assert settings.app_env == "testing" and settings.fyers_access_token == ""

def test_cors_csv_parsing(): assert Settings(CORS_ORIGINS="http://a,http://b").cors_origins == ("http://a", "http://b")
