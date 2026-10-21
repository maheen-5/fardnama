"""Tests for backend application settings."""

from pathlib import Path

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Avoid cached environment values leaking between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_defaults(monkeypatch):
    for name in (
        "APP_ENV",
        "CORS_ORIGINS",
        "FARDNAMA_UPLOAD_DIR",
        "FARDNAMA_MAX_UPLOAD_BYTES",
        "TESSERACT_CMD",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()

    assert settings.upload_dir == Path("data/evidence")
    assert settings.max_upload_bytes == 10485760
    assert settings.app_env == "development"
    assert settings.cors_origins == ["*"]
    assert settings.tesseract_cmd is None


def test_settings_environment_overrides(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("FARDNAMA_UPLOAD_DIR", "/srv/evidence")
    monkeypatch.setenv("FARDNAMA_MAX_UPLOAD_BYTES", "2048")
    monkeypatch.setenv("TESSERACT_CMD", "/usr/bin/tesseract")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.app_env == "production"
    assert settings.upload_dir == Path("/srv/evidence")
    assert settings.max_upload_bytes == 2048
    assert settings.tesseract_cmd == "/usr/bin/tesseract"
    assert settings.cors_origins == []


def test_settings_parse_cors_origins(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "a,b")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.cors_origins == ["a", "b"]
