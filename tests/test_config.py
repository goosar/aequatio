import pytest

from app.core.config import load_settings

BASE_ENV = {
    "DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "x" * 32,
}


def test_load_settings_requires_secret_key():
    environment = {"DATABASE_URL": BASE_ENV["DATABASE_URL"]}

    with pytest.raises(ValueError, match="SECRET_KEY is required"):
        load_settings(environment)


@pytest.mark.parametrize(
    "secret",
    ["your-secret-key-change-in-production", "too-short"],
)
def test_load_settings_rejects_insecure_secret(secret: str):
    with pytest.raises(ValueError, match="SECRET_KEY"):
        load_settings({**BASE_ENV, "SECRET_KEY": secret})


def test_load_settings_requires_database_url():
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        load_settings({"SECRET_KEY": "x" * 32})


def test_load_settings_parses_cors_origins():
    settings = load_settings(
        {**BASE_ENV, "CORS_ORIGINS": "https://one.example, https://two.example"}
    )

    assert settings.cors_origins == (
        "https://one.example",
        "https://two.example",
    )


def test_load_settings_defaults_to_local_vite_origin():
    settings = load_settings(BASE_ENV)

    assert settings.cors_origins == ("http://localhost:5173",)


def test_load_settings_rejects_invalid_access_token_expiration_without_echoing_value():
    with pytest.raises(ValueError, match="^ACCESS_TOKEN_EXPIRE_MINUTES must be an integer$"):
        load_settings({**BASE_ENV, "ACCESS_TOKEN_EXPIRE_MINUTES": "not-a-number"})
