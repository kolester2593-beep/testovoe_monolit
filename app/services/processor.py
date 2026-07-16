"""
Процессор для обработки текстовых обращений.

Этот модуль содержит бизнес-логику обработки запросов:
1. Получает текст от клиента
2. Вызывает AI-провайдер для анализа
3. Валидирует ответ через Pydantic
4. Возвращает структурированный результат
"""

from typing import Optional

from pydantic import ValidationError

from app.models import ProcessRequest, ProcessResponse, RequestType
from app.services.ai_provider import AIClient, create_ai_client


class TextProcessor:
    """
    Процессор для обработки текстовых обращений.

    Координирует работу между входными данными, AI-провайдером
    и выходной валидацией.
    """

    def __init__(self, ai_client: AIClient):
        """
        Инициализация процессора.

        Args:
            ai_client: Экземпляр AI-клиента (Mock или Real)
        """
        self.ai_client = ai_client

    async def process(self, request: ProcessRequest) -> ProcessResponse:
        """
        Обработать текстовый запрос.

        Args:
            request: Валидированный входной запрос

        Returns:
            Структурированный ответ с результатом обработки

        Raises:
            Exception: Если AI-провайдер вернул невалидный ответ
        """
        # Вызываем AI-провайдер
        ai_result = await self.ai_client.process_text(request.text)

        # Определяем, использовался ли мок
        is_mock = isinstance(self.ai_client, type(self.ai_client).__mro__[1].__subclasses__()[0])
        # Более простой способ:
        from app.services.ai_provider import MockAIClient

        is_mock = isinstance(self.ai_client, MockAIClient)

        # Валидируем и создаём ответ через Pydantic
        try:
            response = ProcessResponse(
                request_type=ai_result["request_type"],
                summary=ai_result["summary"],
                confidence=ai_result["confidence"],
                is_processed_by_mock=is_mock,
            )
        except (KeyError, ValidationError) as e:
            raise Exception(f"AI provider returned invalid response: {e}")

        return response


# ============================================================================
# ГЛОБАЛЬНЫЙ ПРОЦЕССОР (синглтон для использования в API)
# ============================================================================

_processor: Optional[TextProcessor] = None


def get_processor(
    use_mock: bool = True, api_key: Optional[str] = None, model: str = "gpt-4o-mini"
) -> TextProcessor:
    """
    Получить глобальный экземпляр процессора (синглтон).

    Args:
        use_mock: Использовать ли мок AI-клиент
        api_key: API ключ для реального AI (если use_mock=False)
        model: Название модели для реального AI

    Returns:
        Экземпляр TextProcessor
    """
    global _processor

    if _processor is None:
        ai_client = create_ai_client(use_mock=use_mock, api_key=api_key, model=model)
        _processor = TextProcessor(ai_client=ai_client)

    return _processor


def reset_processor():
    """Сбросить глобальный процессор (для тестирования)."""
    global _processor
    _processor = None
