"""
Тесты для Pydantic моделей.

Демонстрируем подход QA Engineer к тестированию моделей данных.
"""

import pytest
from pydantic import ValidationError
from app.models import ProcessRequest, ProcessResponse, RequestType, ErrorResponse


# ============================================================================
# Тесты для ProcessRequest
# ============================================================================


class TestProcessRequest:
    """Тесты входной модели ProcessRequest."""

    def test_valid_request(self):
        """Тест: валидный запрос успешно создаётся."""
        request = ProcessRequest(text="Тестовый текст")
        assert request.text == "Тестовый текст"

    def test_request_strips_whitespace(self):
        """Тест: пробелы по краям удаляются."""
        request = ProcessRequest(text="  Тестовый текст  ")
        assert request.text == "Тестовый текст"

    def test_empty_text_raises_error(self):
        """Тест: пустой текст вызывает ошибку валидации."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessRequest(text="")

        # Проверяем, что ошибка связана с полем text
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("text",) for error in errors)

    def test_whitespace_only_text_raises_error(self):
        """Тест: текст из пробелов вызывает ошибку валидации."""
        with pytest.raises(ValidationError):
            ProcessRequest(text="   ")

    def test_text_too_long_raises_error(self):
        """Тест: слишком длинный текст вызывает ошибку валидации."""
        long_text = "a" * 10001  # Больше 10000 символов
        with pytest.raises(ValidationError):
            ProcessRequest(text=long_text)

    def test_missing_text_raises_error(self):
        """Тест: отсутствие поля text вызывает ошибку валидации."""
        with pytest.raises(ValidationError):
            ProcessRequest()  # type: ignore


# ============================================================================
# Тесты для ProcessResponse
# ============================================================================


class TestProcessResponse:
    """Тесты выходной модели ProcessResponse."""

    def test_valid_response(self):
        """Тест: валидный ответ успешно создаётся."""
        response = ProcessResponse(
            request_type=RequestType.TECH_SUPPORT,
            summary="Пользователь сообщает о проблеме с входом в систему.",
            confidence=0.95,
            is_processed_by_mock=True,
        )

        assert response.request_type == "TECH_SUPPORT"  # use_enum_values=True
        assert response.summary == "Пользователь сообщает о проблеме с входом в систему."
        assert response.confidence == 0.95
        assert response.is_processed_by_mock is True

    def test_confidence_rounding(self):
        """Тест: confidence округляется до 2 знаков."""
        response = ProcessResponse(
            request_type=RequestType.GENERAL,
            summary="Общий вопрос.",
            confidence=0.9567,
            is_processed_by_mock=False,
        )

        assert response.confidence == 0.96  # Округлено

    def test_confidence_below_zero_raises_error(self):
        """Тест: confidence меньше 0 вызывает ошибку."""
        with pytest.raises(ValidationError):
            ProcessResponse(
                request_type=RequestType.GENERAL,
                summary="Тест.",
                confidence=-0.1,
                is_processed_by_mock=True,
            )

    def test_confidence_above_one_raises_error(self):
        """Тест: confidence больше 1 вызывает ошибку."""
        with pytest.raises(ValidationError):
            ProcessResponse(
                request_type=RequestType.GENERAL,
                summary="Тест.",
                confidence=1.5,
                is_processed_by_mock=True,
            )

    def test_summary_too_short_raises_error(self):
        """Тест: слишком короткий summary вызывает ошибку."""
        with pytest.raises(ValidationError):
            ProcessResponse(
                request_type=RequestType.GENERAL,
                summary="Коротко",  # Меньше 10 символов
                confidence=0.9,
                is_processed_by_mock=True,
            )

    def test_all_request_types(self):
        """Тест: все типы запросов корректно обрабатываются."""
        for request_type in RequestType:
            response = ProcessResponse(
                request_type=request_type,
                summary="Тестовое описание для проверки.",
                confidence=0.85,
                is_processed_by_mock=True,
            )
            assert response.request_type == request_type.value

    def test_response_serialization(self):
        """Тест: модель корректно сериализуется в JSON."""
        response = ProcessResponse(
            request_type=RequestType.SALES,
            summary="Пользователь спрашивает о ценах.",
            confidence=0.88,
            is_processed_by_mock=True,
        )

        # Сериализация в dict
        response_dict = response.model_dump()

        assert response_dict["request_type"] == "SALES"
        assert response_dict["summary"] == "Пользователь спрашивает о ценах."
        assert response_dict["confidence"] == 0.88
        assert response_dict["is_processed_by_mock"] is True

        # Сериализация в JSON
        response_json = response.model_dump_json()
        assert '"request_type":"SALES"' in response_json


# ============================================================================
# Тесты для ErrorResponse
# ============================================================================


class TestErrorResponse:
    """Тесты модели ошибок ErrorResponse."""

    def test_valid_error_response(self):
        """Тест: валидный ответ об ошибке успешно создаётся."""
        error = ErrorResponse(error="VALIDATION_ERROR", message="Текст не может быть пустым")

        assert error.error == "VALIDATION_ERROR"
        assert error.message == "Текст не может быть пустым"
        assert error.details is None

    def test_error_response_with_details(self):
        """Тест: ответ об ошибке с деталями."""
        error = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Невалидное поле",
            details={"field": "text", "value": ""},
        )

        assert error.details == {"field": "text", "value": ""}

    def test_error_response_serialization(self):
        """Тест: модель ошибки корректно сериализуется."""
        error = ErrorResponse(error="AI_PROVIDER_ERROR", message="Ошибка подключения к AI API")

        error_dict = error.model_dump()
        assert error_dict["error"] == "AI_PROVIDER_ERROR"
        assert error_dict["details"] is None


# ============================================================================
# Тесты для RequestType Enum
# ============================================================================


class TestRequestType:
    """Тесты enum RequestType."""

    def test_enum_values(self):
        """Тест: все значения enum корректны."""
        assert RequestType.TECH_SUPPORT.value == "TECH_SUPPORT"
        assert RequestType.SALES.value == "SALES"
        assert RequestType.COMPLAINT.value == "COMPLAINT"
        assert RequestType.GENERAL.value == "GENERAL"

    def test_enum_is_string(self):
        """Тест: enum наследуется от str."""
        assert isinstance(RequestType.TECH_SUPPORT, str)
        assert RequestType.TECH_SUPPORT == "TECH_SUPPORT"
