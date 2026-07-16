# testovoe_monolit
AI-агент для обработки текстовых обращений (тестовое задание)

## 📊 Архитектура и Flow

Полная визуальная схема flow доступна в файле [docs/flow_diagram.md](docs/flow_diagram.md).


Описание компонентов:
FastAPI — веб-фреймворк для создания API
Pydantic — валидация входных и выходных данных
Processor Service — бизнес-логика обработки
MockAIClient — эвристическая обработка без внешних зависимостей
RealAIClient — интеграция с реальным AI API (OpenAI)