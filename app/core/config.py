from dataclasses import dataclass
from os import environ as process_environment
from typing import Mapping

from dotenv import load_dotenv


PLACEHOLDER_SECRET = "your-secret-key-change-in-production"


@dataclass(frozen=True)
class Settings:
    database_url: str
    rabbitmq_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    cors_origins: tuple[str, ...]


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    values = process_environment if environ is None else environ
    database_url = values.get("DATABASE_URL", "").strip()
    secret_key = values.get("SECRET_KEY", "")
    if not database_url:
        raise ValueError("DATABASE_URL is required")
    if not secret_key:
        raise ValueError("SECRET_KEY is required")
    if secret_key == PLACEHOLDER_SECRET or len(secret_key) < 32:
        raise ValueError("SECRET_KEY must contain at least 32 characters and must not use the placeholder")

    raw_origins = values.get("CORS_ORIGINS", "http://localhost:5173")
    cors_origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
    if not cors_origins:
        raise ValueError("CORS_ORIGINS must contain at least one origin")

    return Settings(
        database_url=database_url,
        rabbitmq_url=values.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
        secret_key=secret_key,
        algorithm="HS256",
        access_token_expire_minutes=int(values.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        cors_origins=cors_origins,
    )


load_dotenv()
settings = load_settings()
