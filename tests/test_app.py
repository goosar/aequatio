from fastapi.testclient import TestClient

from app.core.config import Settings
from main import create_app


def test_create_app_uses_configured_cors_origins():
    app_settings = Settings(
        database_url="sqlite:///:memory:",
        rabbitmq_url="amqp://guest:guest@localhost:5672/",
        secret_key="x" * 32,
        algorithm="HS256",
        access_token_expire_minutes=30,
        cors_origins=("https://app.example",),
    )
    client = TestClient(create_app(app_settings))

    response = client.options(
        "/api/v1/",
        headers={
            "Origin": "https://app.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example"
