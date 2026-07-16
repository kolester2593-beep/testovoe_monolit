"""
Конфигурация приложения.

Загружает настройки из переменных окружения (.env файл).
Использует pydantic-settings для автоматической валидации.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.

    Значения загружаются из переменных окружения или .env файла.
    """

    # Режим работы AI-провайдера
    USE_MOCK_AI: bool = True

    # Настройки приложения
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True

    # OpenAI настройки (используются, если USE_MOCK_AI=false)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TIMEOUT: int = 30

    # Pydantic-settings конфиг
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


# Глобальный экземпляр настроек (синглтон)
settings = Settings()
