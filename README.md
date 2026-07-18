AI-агент для обработки текстовых обращений

Выбранный кейс: Кейс 1 — AI-агент для обработки текстовых обращений.

## 📊 Архитектура и Flow

Полная визуальная схема flow доступна в файле [docs/flow_diagram.md](docs/flow_diagram.md).

Что сделано
Архитектура: Реализован паттерн Стратегия для AI-провайдеров. Легко переключаться между Mock и Real режимами.

Валидация данных: Использован Pydantic v2 для строгой типизации и валидации входных/выходных данных (очистка пробелов, проверка длины, диапазоны).

Тестирование: Написано 50+ тестов (модели, бизнес-логика, API) с использованием pytest. Покрытие кода тестами > 90%.

Документация: Автоматическая генерация OpenAPI/Swagger документации.

Качество кода: Настроен линтер ruff и форматирование.


Как запустить
1. Клонирование и установка зависимостей
# Клонировать репозиторий
git clone https://github.com/kolester2593-beep/testovoe_monolit
cd testovoe_monolit

# Создать и активировать виртуальное окружение
python -m venv .venv

# Windows:
.\\.venv\\Scripts\\Activate.ps1

# macOS/Linux:
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

2. Настройка окружения
Скопируйте файл .env.example в .env и настройте переменные:
cp .env.example .env

3. Запуск сервера
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
Сервер будет доступен по адресу: http://127.0.0.1:8000/docs


Примеры запросов и ответов

1. Техническая поддержка
    Запрос:
    curl -X POST "http://127.0.0.1:8000/api/v1/process" \
     -H "Content-Type: application/json" \
     -d '{"text": "Не могу войти в личный кабинет, постоянно выдает ошибку 500"}'

    Ответ:
    {
  "request_type": "TECH_SUPPORT",
  "summary": "Пользователь сообщает о технической проблеме: Не могу войти в личный кабинет, постоянно выдает ошибку 500",
  "confidence": 0.6,
  "is_processed_by_mock": true
}

2. Продажи 
    Запрос:
    curl -X POST "http://127.0.0.1:8000/api/v1/process" \
     -H "Content-Type: application/json" \
     -d '{"text": "Подскажите, сколько стоит корпоративный тариф и есть ли скидки?"}'

    Ответ:
     {
  "request_type": "SALES",
  "summary": "Пользователь интересуется вопросами продаж: Подскажите, сколько стоит корпоративный тариф и есть ли скидки?",
  "confidence": 0.6,
  "is_processed_by_mock": true
}

3. Ошибка валидации (пустой текст)
    Запрос:
    curl -X POST "http://127.0.0.1:8000/api/v1/process" \
     -H "Content-Type: application/json" \
     -d '{"text": ""}'

    Ответ:
    {
  "error": "VALIDATION_ERROR",
  "message": "Ошибка валидации входных данных",
  "details": {
    "errors": [
      {
        "type": "value_error",
        "loc": ["body", "text"],
        "msg": "Текст не может быть пустым или состоять только из пробелов",
        "input": ""
      }
    ]
  }
}
        Запуск тестов

        pytest tests/ -v --cov=app --cov-report=term-missing