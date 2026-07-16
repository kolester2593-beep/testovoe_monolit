"""
AI-провайдеры для обработки текстовых обращений.

Этот модуль реализует паттерн Стратегия для работы с разными AI-клиентами:
- MockAIClient: эвристическая обработка без внешних зависимостей
- RealAIClient: интеграция с реальным AI API (OpenAI)
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any

import httpx
from pydantic import ValidationError

from app.models import RequestType, ProcessResponse


# ============================================================================
# АБСТРАКТНЫЙ ИНТЕРФЕЙС: AI Client
# ============================================================================


class AIClient(ABC):
    """
    Абстрактный интерфейс для AI-клиентов.

    Все реализации должны наследоваться от этого класса
    и реализовывать метод process_text.
    """

    @abstractmethod
    async def process_text(self, text: str) -> Dict[str, Any]:
        """
        Обработать текст и вернуть структурированный результат.

        Args:
            text: Текст для обработки

        Returns:
            Словарь с полями:
            - request_type: str (значение из RequestType)
            - summary: str (краткое содержание)
            - confidence: float (уверенность 0.0-1.0)
        """
        pass


# ============================================================================
# РЕАЛИЗАЦИЯ 1: MockAIClient (эвристика на ключевых словах)
# ============================================================================


class MockAIClient(AIClient):
    """
    Мок AI-клиент, использующий эвристику на ключевых словах.

    Не требует внешних API, работает локально.
    Подходит для демонстрации flow и тестирования.
    """

    # Словари ключевых слов для каждого типа запроса
    # Включаем разные морфологические формы для robustness
    KEYWORD_MAP = {
        RequestType.TECH_SUPPORT: [
            "не работает",
            "ошибка",
            "баг",
            "проблема",
            "сломалось",
            "не могу",
            "не получается",
            "вылетает",
            "зависает",
            "тормозит",
            "ошибк",
            "сломал",
            "почини",
            "глючит",
            "тормоз",
            "error",
            "bug",
            "crash",
            "fail",
            "broken",
        ],
        RequestType.SALES: [
            "цена",
            "стоимость",
            "купить",
            "заказать",
            "тариф",
            "скидка",
            "акция",
            "предложение",
            "оплата",
            "счет",
            "стоит",
            "стоил",
            "стоить",
            "прайс",
            "оплат",
            "price",
            "buy",
            "order",
            "cost",
            "discount",
        ],
        RequestType.COMPLAINT: [
            "жалоба",
            "недоволен",
            "плохо",
            "ужасно",
            "возврат",
            "деньги назад",
            "претензия",
            "разочарован",
            "халтура",
            "ужас",
            "ужасен",
            "ужасн",
            "вернуть деньги",
            "вернуть",
            "плох",
            "кошмар",
            "отвратит",
            "бесит",
            "ненавиж",
            "жалоб",
            "complaint",
            "bad",
            "terrible",
            "refund",
            "disappointed",
        ],
        RequestType.GENERAL: [],  # Всё остальное
    }

    # Шаблоны для генерации summary
    SUMMARY_TEMPLATES = {
        RequestType.TECH_SUPPORT: "Пользователь сообщает о технической проблеме: {text_short}",
        RequestType.SALES: "Пользователь интересуется вопросами продаж: {text_short}",
        RequestType.COMPLAINT: "Пользователь выражает недовольство: {text_short}",
        RequestType.GENERAL: "Пользователь задал общий вопрос: {text_short}",
    }

    async def process_text(self, text: str) -> Dict[str, Any]:
        """
        Обработать текст с помощью эвристики на ключевых словах.

        Алгоритм:
        1. Приводим текст к нижнему регистру
        2. Ищем ключевые слова для каждого типа запроса
        3. Выбираем тип с наибольшим количеством совпадений
        4. Генерируем summary на основе шаблона
        5. Возвращаем структурированный результат
        """
        text_lower = text.lower()

        # Подсчитываем совпадения для каждого типа
        matches_count = {}
        for request_type, keywords in self.KEYWORD_MAP.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            matches_count[request_type] = count

        # Выбираем тип с максимальным количеством совпадений
        # Если совпадений нет - GENERAL
        max_matches = max(matches_count.values())
        if max_matches == 0:
            detected_type = RequestType.GENERAL
        else:
            detected_type = max(matches_count, key=matches_count.get)

        # Генерируем summary
        text_short = text[:100] + "..." if len(text) > 100 else text
        summary = self.SUMMARY_TEMPLATES[detected_type].format(text_short=text_short)

        # Рассчитываем confidence на основе количества совпадений
        # Чем больше совпадений - тем выше уверенность
        confidence = min(0.95, 0.5 + (max_matches * 0.1))

        return {"request_type": detected_type.value, "summary": summary, "confidence": confidence}


# ============================================================================
# РЕАЛИЗАЦИЯ 2: RealAIClient (OpenAI API)
# ============================================================================


class RealAIClient(AIClient):
    """
    Реальный AI-клиент, использующий OpenAI API.

    Требует API ключ и интернет-соединение.
    Отправляет промпт с требованием вернуть JSON в определённой схеме.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Инициализация клиента.

        Args:
            api_key: API ключ OpenAI
            model: Название модели (по умолчанию gpt-4o-mini)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def process_text(self, text: str) -> Dict[str, Any]:
        """
        Обработать текст с помощью OpenAI API.
        """
        # Формируем промпт
        prompt = f"""
Проанализируй следующее текстовое обращение и верни результат в формате JSON.

Текст обращения:
{text}

Верни JSON со следующей структурой:
{{
    "request_type": "TECH_SUPPORT" | "SALES" | "COMPLAINT" | "GENERAL",
    "summary": "Краткое содержание обращения (1-3 предложения, максимум 200 символов)",
    "confidence": 0.0-1.0 (уверенность в определении типа)
}}

ВАЖНО:
- Верни ТОЛЬКО валидный JSON, без дополнительного текста
- request_type должен быть одним из: TECH_SUPPORT, SALES, COMPLAINT, GENERAL
- summary должен быть на русском языке
- confidence должен быть числом от 0.0 до 1.0
"""

        # Формируем запрос к OpenAI API
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты - AI-ассистент для классификации обращений. Отвечай ТОЛЬКО валидным JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 500,
        }

        # Отправляем запрос
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)

            # Проверяем статус ответа
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

            # Парсим ответ
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]

            # Извлекаем JSON из ответа
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                raise Exception(f"Failed to extract JSON from response: {content}")

            json_str = json_match.group(0)

            # Парсим JSON
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse JSON: {e}")

            # Валидируем структуру через Pydantic
            try:
                ProcessResponse(
                    request_type=result["request_type"],
                    summary=result["summary"],
                    confidence=result["confidence"],
                    is_processed_by_mock=False,
                )
            except (KeyError, ValidationError) as e:
                raise Exception(f"Invalid response structure: {e}")

            return {
                "request_type": result["request_type"],
                "summary": result["summary"],
                "confidence": result["confidence"],
            }


# ============================================================================
# FACTORY: Создание AI-клиента на основе конфигурации
# ============================================================================


def create_ai_client(use_mock: bool, api_key: str = None, model: str = "gpt-4o-mini") -> AIClient:
    """
    Фабрика для создания AI-клиента.

    Args:
        use_mock: Если True, создаёт MockAIClient, иначе RealAIClient
        api_key: API ключ для RealAIClient (обязателен, если use_mock=False)
        model: Название модели для RealAIClient

    Returns:
        Экземпляр AIClient

    Raises:
        ValueError: Если use_mock=False, но api_key не предоставлен
    """
    if use_mock:
        return MockAIClient()
    else:
        if not api_key:
            raise ValueError("API key is required for RealAIClient")
        return RealAIClient(api_key=api_key, model=model)
