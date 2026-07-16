"""
Тесты для FastAPI эндпоинтов.

Используем TestClient для тестирования HTTP-запросов.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.processor import reset_processor


# ============================================================================
# ФИКСТУРЫ
# ============================================================================


@pytest.fixture
def client():
    """Фикстура: создаём тестовый клиент."""
    # Сбрасываем процессор перед каждым тестом
    reset_processor()
    with TestClient(app) as c:
        yield c
    # Сбрасываем после
    reset_processor()


# ============================================================================
# Тесты для GET /health
# ============================================================================


class TestHealthEndpoint:
    """Тесты эндпоинта health check."""

    def test_health_check_success(self, client):
        """Тест: health check возвращает 200."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AI Text Processor"
        assert "version" in data
        assert "mode" in data

    def test_health_check_mode_is_mock(self, client):
        """Тест: в тестовом режиме используется mock."""
        response = client.get("/health")
        data = response.json()
        # По умолчанию USE_MOCK_AI=true
        assert data["mode"] in ["mock", "real"]


# ============================================================================
# Тесты для GET /
# ============================================================================


class TestRootEndpoint:
    """Тесты корневого эндпоинта."""

    def test_root_success(self, client):
        """Тест: корневой эндпоинт возвращает 200."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "AI Text Processor"
        assert "docs" in data
        assert "health" in data


# ============================================================================
# Тесты для POST /api/v1/process
# ============================================================================


class TestProcessEndpoint:
    """Тесты эндпоинта обработки текста."""

    def test_process_tech_support(self, client):
        """Тест: обработка запроса технической поддержки."""
        response = client.post(
            "/api/v1/process", json={"text": "Не могу войти в систему, ошибка 500"}
        )

        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert "request_type" in data
        assert "summary" in data
        assert "confidence" in data
        assert "is_processed_by_mock" in data

        # Проверяем значения
        assert data["request_type"] == "TECH_SUPPORT"
        assert len(data["summary"]) >= 10
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["is_processed_by_mock"] is True

    def test_process_sales(self, client):
        """Тест: обработка запроса о продажах."""
        response = client.post("/api/v1/process", json={"text": "Сколько стоит премиум тариф?"})

        assert response.status_code == 200
        data = response.json()
        assert data["request_type"] == "SALES"

    def test_process_complaint(self, client):
        """Тест: обработка жалобы."""
        response = client.post(
            "/api/v1/process", json={"text": "Ваш сервис ужасен, хочу вернуть деньги"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["request_type"] == "COMPLAINT"

    def test_process_general(self, client):
        """Тест: обработка общего вопроса."""
        response = client.post("/api/v1/process", json={"text": "Привет, как дела?"})

        assert response.status_code == 200
        data = response.json()
        assert data["request_type"] == "GENERAL"

    def test_process_empty_text_returns_422(self, client):
        """Тест: пустой текст возвращает 422."""
        response = client.post("/api/v1/process", json={"text": ""})

        assert response.status_code == 422

    def test_process_whitespace_only_returns_422(self, client):
        """Тест: текст из пробелов возвращает 422."""
        response = client.post("/api/v1/process", json={"text": "   "})

        assert response.status_code == 422

    def test_process_missing_text_returns_422(self, client):
        """Тест: отсутствие поля text возвращает 422."""
        response = client.post("/api/v1/process", json={})

        assert response.status_code == 422

    def test_process_invalid_json_returns_422(self, client):
        """Тест: невалидный JSON возвращает 422."""
        response = client.post(
            "/api/v1/process", content="not a json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_process_long_text(self, client):
        """Тест: обработка длинного текста."""
        long_text = "Проблема с системой " * 100
        response = client.post("/api/v1/process", json={"text": long_text})

        assert response.status_code == 200
        data = response.json()
        assert data["request_type"] == "TECH_SUPPORT"

    def test_process_response_schema(self, client):
        """Тест: проверка схемы ответа."""
        response = client.post("/api/v1/process", json={"text": "Тестовый запрос"})

        assert response.status_code == 200
        data = response.json()

        # Проверяем типы полей
        assert isinstance(data["request_type"], str)
        assert isinstance(data["summary"], str)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["is_processed_by_mock"], bool)

        # Проверяем допустимые значения request_type
        valid_types = ["TECH_SUPPORT", "SALES", "COMPLAINT", "GENERAL"]
        assert data["request_type"] in valid_types


# ============================================================================
# Тесты для Swagger/OpenAPI документации
# ============================================================================


class TestDocumentation:
    """Тесты доступности документации."""

    def test_swagger_ui_accessible(self, client):
        """Тест: Swagger UI доступен."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_accessible(self, client):
        """Тест: OpenAPI схема доступна."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        # Проверяем наличие основных полей
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

        # Проверяем наличие наших эндпоинтов
        assert "/api/v1/process" in data["paths"]
        assert "/health" in data["paths"]

    def test_redoc_accessible(self, client):
        """Тест: ReDoc доступен."""
        response = client.get("/redoc")
        assert response.status_code == 200
