"""
Тесты для процессора.

Демонстрируем подход QA Engineer к тестированию бизнес-логики.
"""

import pytest
from app.services.processor import TextProcessor, get_processor, reset_processor
from app.services.ai_provider import MockAIClient
from app.models import ProcessRequest, ProcessResponse, RequestType


# ============================================================================
# Тесты для TextProcessor
# ============================================================================


class TestTextProcessor:
    """Тесты процессора."""

    @pytest.fixture
    def processor(self):
        """Фикстура: создаём процессор с мок клиентом."""
        mock_client = MockAIClient()
        return TextProcessor(ai_client=mock_client)

    @pytest.mark.asyncio
    async def test_process_valid_request(self, processor):
        """Тест: обработка валидного запроса."""
        request = ProcessRequest(text="Не работает система")
        response = await processor.process(request)

        assert isinstance(response, ProcessResponse)
        assert response.request_type == RequestType.TECH_SUPPORT.value
        assert len(response.summary) > 0
        assert 0.0 <= response.confidence <= 1.0
        assert response.is_processed_by_mock is True

    @pytest.mark.asyncio
    async def test_process_returns_correct_type(self, processor):
        """Тест: процессор возвращает правильный тип запроса."""
        test_cases = [
            ("Ошибка 500", RequestType.TECH_SUPPORT),
            ("Сколько стоит?", RequestType.SALES),
            ("Хочу жалобу", RequestType.COMPLAINT),
            ("Привет", RequestType.GENERAL),
        ]

        for text, expected_type in test_cases:
            request = ProcessRequest(text=text)
            response = await processor.process(request)
            assert response.request_type == expected_type.value

    @pytest.mark.asyncio
    async def test_process_marks_as_mock(self, processor):
        """Тест: процессор помечает ответ как обработанный моком."""
        request = ProcessRequest(text="Тестовый запрос")
        response = await processor.process(request)

        assert response.is_processed_by_mock is True


# ============================================================================
# Тесты для глобального процессора (синглтон)
# ============================================================================


class TestGetProcessor:
    """Тесты функции получения глобального процессора."""

    def setup_method(self):
        """Сбрасываем процессор перед каждым тестом."""
        reset_processor()

    def test_get_processor_creates_singleton(self):
        """Тест: get_processor создаёт синглтон."""
        processor1 = get_processor(use_mock=True)
        processor2 = get_processor(use_mock=True)

        assert processor1 is processor2

    def test_get_processor_with_mock(self):
        """Тест: получение процессора с мок клиентом."""
        processor = get_processor(use_mock=True)
        assert isinstance(processor, TextProcessor)
        assert isinstance(processor.ai_client, MockAIClient)

    def teardown_method(self):
        """Сбрасываем процессор после каждого теста."""
        reset_processor()
