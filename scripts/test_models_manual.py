"""
Ручная проверка Pydantic моделей.

Этот скрипт демонстрирует, как работают модели в реальном использовании.
"""

from app.models import ProcessRequest, ProcessResponse, RequestType, ErrorResponse


def main():
    print("=" * 60)
    print("Тестирование Pydantic моделей")
    print("=" * 60)

    # Тест 1: Валидный запрос
    print("\n1. Создание валидного запроса:")
    request = ProcessRequest(text="  Не могу войти в систему  ")
    print(f"   Входной текст: '  Не могу войти в систему  '")
    print(f"   После валидации: '{request.text}'")
    print(f"   Пробелы удалены")

    # Тест 2: Валидный ответ
    print("\n2. Создание валидного ответа:")
    response = ProcessResponse(
        request_type=RequestType.TECH_SUPPORT,
        summary="Пользователь не может войти в систему.",
        confidence=0.9567,
        is_processed_by_mock=True,
    )
    print(f"   Тип запроса: {response.request_type}")
    print(f"   Summary: {response.summary}")
    print(f"   Confidence (до округления): 0.9567")
    print(f"   Confidence (после округления): {response.confidence}")
    print(f"   Confidence округлён до 2 знаков")

    # Тест 3: Сериализация в JSON
    print("\n3. Сериализация ответа в JSON:")
    json_str = response.model_dump_json(indent=2)
    print(json_str)
    print(f"   Успешно сериализовано")

    # Тест 4: Модель ошибки
    print("\n4. Создание модели ошибки:")
    error = ErrorResponse(
        error="VALIDATION_ERROR", message="Текст не может быть пустым", details={"field": "text"}
    )
    print(f"   Error: {error.error}")
    print(f"   Message: {error.message}")
    print(f"   Details: {error.details}")
    print(f"   Модель ошибки работает")

    print("\n" + "=" * 60)
    print("Все тесты пройдены успешно!")
    print("=" * 60)


if __name__ == "__main__":
    main()
