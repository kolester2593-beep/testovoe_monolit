# testovoe_monolit
AI-агент для обработки текстовых обращений (тестовое задание)

## 📊 Архитектура и Flow

Полная визуальная схема flow доступна в файле [docs/flow_diagram.md](docs/flow_diagram.md).

Ниже представлена упрощённая схема основного процесса:

```mermaid
flowchart LR
    A[POST /api/v1/process<br/>text: string] --> B[FastAPI + Pydantic<br/>Валидация входа]
    B --> C[Processor Service]
    C --> D{USE_MOCK_AI?}
    D -->|true| E[MockAIClient]
    D -->|false| F[RealAIClient<br/>OpenAI API]
    E --> G[Pydantic<br/>Валидация выхода]
    F --> G
    G --> H[JSON Response<br/>200 OK]
    
    style A fill:#e1f5ff
    style H fill:#c8e6c9


Описание компонентов:
FastAPI — веб-фреймворк для создания API
Pydantic — валидация входных и выходных данных
Processor Service — бизнес-логика обработки
MockAIClient — эвристическая обработка без внешних зависимостей
RealAIClient — интеграция с реальным AI API (OpenAI)