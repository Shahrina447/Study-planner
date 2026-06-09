from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent


def _normalize_env_value(name: str, value: str | None) -> str | None:
    if not value:
        return None

    value = value.strip().strip("'\"")
    if name == "DATABASE_URL" and value.startswith("postgresql+asyncpg://"):
        value = "postgresql://" + value.removeprefix("postgresql+asyncpg://")
    return value or None


def _read_env_file_value(name: str) -> str | None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        key, separator, value = stripped.partition("=")
        if separator and key.strip() == name:
            return _normalize_env_value(name, value)

    return None


def get_env_value(name: str) -> str | None:
    from os import getenv

    return _normalize_env_value(name, getenv(name)) or _read_env_file_value(name)


class Settings(BaseSettings):
    MISTRAL_API_KEY: str = get_env_value("MISTRAL_API_KEY") or ""
    MISTRAL_MODEL: str = get_env_value("MISTRAL_MODEL") or "mistral-small-latest"
    DATABASE_URL: str | None = get_env_value("DATABASE_URL")
    CORS_ORIGIN: str = get_env_value("CORS_ORIGIN") or "http://localhost:3000"

settings = Settings()
