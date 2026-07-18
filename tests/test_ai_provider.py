    #Тесты для AI-провайдеров.


import pytest
from app.services.ai_provider import MockAIClient, create_ai_client
from app.models import RequestType


# Тесты для MockAIClient


class TestMockAIClient:

    @pytest.fixture
    def mock_client(self):
        """Фикстура: создаём экземпляр MockAIClient."""
        return MockAIClient()

    @pytest.mark.asyncio
    async def test_tech_support_detection(self, mock_client):
        """Тест: определение технической поддержки."""
        text = "Не могу войти в систему, ошибка 500"
        result = await mock_client.process_text(text)

        assert result["request_type"] == RequestType.TECH_SUPPORT.value
        assert "summary" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_sales_detection(self, mock_client):
        """Тест: определение продаж."""
        text = "Сколько стоит премиум тариф?"
        result = await mock_client.process_text(text)

        assert result["request_type"] == RequestType.SALES.value
        assert len(result["summary"]) > 0

    @pytest.mark.asyncio
    async def test_complaint_detection(self, mock_client):
        """Тест: определение жалобы."""
        text = "Ваш сервис ужасен, хочу вернуть деньги"
        result = await mock_client.process_text(text)

        assert result["request_type"] == RequestType.COMPLAINT.value
        assert result["confidence"] >= 0.5

    @pytest.mark.asyncio
    async def test_general_detection(self, mock_client):
        """Тест: определение общего вопроса."""
        text = "Как дела? Какая сегодня погода?"
        result = await mock_client.process_text(text)

        assert result["request_type"] == RequestType.GENERAL.value

    @pytest.mark.asyncio
    async def test_case_insensitive(self, mock_client):
        """Тест: регистронезависимость."""
        text_lower = "не работает система"
        text_upper = "НЕ РАБОТАЕТ СИСТЕМА"

        result_lower = await mock_client.process_text(text_lower)
        result_upper = await mock_client.process_text(text_upper)

        assert result_lower["request_type"] == result_upper["request_type"]

    @pytest.mark.asyncio
    async def test_multiple_keywords(self, mock_client):
        """Тест: текст с несколькими ключевыми словами."""
        text = "Ошибка, баг, не работает, сломалось"
        result = await mock_client.process_text(text)

        assert result["request_type"] == RequestType.TECH_SUPPORT.value
        # Уверенность должна быть выше из-за множества совпадений
        assert result["confidence"] >= 0.7

    @pytest.mark.asyncio
    async def test_summary_generation(self, mock_client):
        """Тест: генерация summary."""
        text = "Проблема с оплатой"
        result = await mock_client.process_text(text)

        assert "summary" in result
        assert len(result["summary"]) >= 10
        assert len(result["summary"]) <= 500

    @pytest.mark.asyncio
    async def test_long_text_truncation(self, mock_client):
        """Тест: обрезка длинного текста в summary."""
        text = "a" * 200  # Очень длинный текст
        result = await mock_client.process_text(text)

        # Summary не должен быть слишком длинным
        assert len(result["summary"]) <= 500


# Тесты для Factory


class TestCreateAIClient:
    """Тесты фабрики создания AI-клиентов."""

    def test_create_mock_client(self):
        """Тест: создание мок клиента."""
        client = create_ai_client(use_mock=True)
        assert isinstance(client, MockAIClient)

    def test_create_real_client_without_key_raises_error(self):
        """Тест: создание реального клиента без ключа вызывает ошибку."""
        with pytest.raises(ValueError, match="API key is required"):
            create_ai_client(use_mock=False, api_key=None)

    def test_create_real_client_with_key(self):
        """Тест: создание реального клиента с ключом."""
        from app.services.ai_provider import RealAIClient

        client = create_ai_client(use_mock=False, api_key="test-key")
        assert isinstance(client, RealAIClient)
