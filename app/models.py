"""
Pydantic модели для AI Text Processor.

Этот модуль определяет структуру входных и выходных данных,
а также обеспечивает их валидацию.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict


# ============================================================================
# ENUM: Типы запросов
# ============================================================================


class RequestType(str, Enum):
    """
    Типы обращений, которые может определить AI-агент.

    Наследуемся от str, чтобы можно было сериализовать в JSON как строку.
    """

    TECH_SUPPORT = "TECH_SUPPORT"  # Техническая поддержка (проблемы, ошибки, баги)
    SALES = "SALES"  # Продажи (цены, покупка, предложения)
    COMPLAINT = "COMPLAINT"  # Жалобы (недовольство, претензии)
    GENERAL = "GENERAL"  # Общие вопросы (всё остальное)


# ============================================================================
# ВХОДНАЯ МОДЕЛЬ: Запрос на обработку
# ============================================================================


class ProcessRequest(BaseModel):
    """
    Модель входного запроса для обработки текста.

    Attributes:
        text: Текст обращения для анализа (обязательное поле)

    Example:
        ```json
        {
            "text": "Не могу войти в личный кабинет, ошибка 500"
        }
        ```
    """

    # Поле с валидацией
    text: str = Field(
        ...,  # ... означает, что поле обязательное
        min_length=1,
        max_length=10000,
        description="Текст обращения для анализа",
        examples=["Не могу войти в личный кабинет, ошибка 500"],
    )

    # Pydantic v2 конфиг
    model_config = ConfigDict(
        # Генерируем JSON схему с примерами (для Swagger/OpenAPI)
        json_schema_extra={
            "examples": [
                {"text": "Не могу войти в личный кабинет, ошибка 500"},
                {"text": "Сколько стоит премиум тариф?"},
                {"text": "Ваш сервис ужасен, хочу вернуть деньги"},
            ]
        }
    )

    # Кастомный валидатор: убираем пробелы по краям
    @field_validator("text")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Убираем пробелы в начале и конце текста."""
        return v.strip()

    # Кастомный валидатор: проверяем, что текст не состоит только из пробелов
    @field_validator("text")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Проверяем, что текст не пустой после удаления пробелов."""
        if not v:
            raise ValueError("Текст не может быть пустым или состоять только из пробелов")
        return v


# ============================================================================
# ВЫХОДНАЯ МОДЕЛЬ: Результат обработки
# ============================================================================


class ProcessResponse(BaseModel):
    """
    Модель ответа с результатом обработки текста.

    Attributes:
        request_type: Определённый тип запроса
        summary: Краткое содержание обращения (1-3 предложения)
        confidence: Уверенность AI в определении типа (0.0 - 1.0)
        is_processed_by_mock: Флаг, указывающий, использовался ли мок

    Example:
        ```json
        {
            "request_type": "TECH_SUPPORT",
            "summary": "Пользователь не может войти в личный кабинет, получает ошибку 500.",
            "confidence": 0.95,
            "is_processed_by_mock": true
        }
        ```
    """

    # Тип запроса (enum)
    request_type: RequestType = Field(..., description="Определённый тип запроса")

    # Краткое содержание
    summary: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Краткое содержание обращения (1-3 предложения)",
    )

    # Уверенность AI (от 0.0 до 1.0)
    confidence: float = Field(
        ...,
        ge=0.0,  # greater than or equal
        le=1.0,  # less than or equal
        description="Уверенность AI в определении типа (0.0 - 1.0)",
        examples=[0.95],
    )

    # Флаг использования мока
    is_processed_by_mock: bool = Field(
        ..., description="True, если обработка выполнена моком, False - если реальным AI"
    )

    # Pydantic v2 конфиг
    model_config = ConfigDict(
        # Автоматически конвертируем enum в строку при сериализации
        use_enum_values=True,
        # JSON схема с примерами
        json_schema_extra={
            "examples": [
                {
                    "request_type": "TECH_SUPPORT",
                    "summary": "Пользователь не может войти в личный кабинет, получает ошибку 500.",
                    "confidence": 0.95,
                    "is_processed_by_mock": True,
                },
                {
                    "request_type": "SALES",
                    "summary": "Пользователь интересуется стоимостью премиум тарифа.",
                    "confidence": 0.88,
                    "is_processed_by_mock": True,
                },
            ]
        },
    )

    # Валидатор: округляем confidence до 2 знаков после запятой
    @field_validator("confidence")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        """Округляем значение confidence до 2 знаков после запятой."""
        return round(v, 2)


# ============================================================================
# МОДЕЛЬ ОШИБКИ: Для обработки исключений
# ============================================================================


class ErrorResponse(BaseModel):
    """
    Модель для возврата ошибок клиенту.

    Attributes:
        error: Тип ошибки
        message: Человекочитаемое описание ошибки
        details: Дополнительные детали (опционально)
    """

    error: str = Field(
        ..., description="Тип ошибки (например, VALIDATION_ERROR, AI_PROVIDER_ERROR)"
    )

    message: str = Field(..., description="Описание ошибки")

    details: Optional[dict] = Field(None, description="Дополнительные детали ошибки")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Текст не может быть пустым",
                "details": {"field": "text"},
            }
        }
    )
