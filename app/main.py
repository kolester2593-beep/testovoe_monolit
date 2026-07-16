"""
Главный модуль FastAPI приложения.

Точка входа для AI Text Processor API.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import settings
from app.models import ProcessRequest, ProcessResponse, ErrorResponse
from app.services.processor import TextProcessor, get_processor, reset_processor


# ============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================================

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN: Инициализация и завершение приложения
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.

    Выполняется при старте и завершении приложения.
    """
    # === STARTUP ===
    logger.info("=" * 60)
    logger.info("🚀 Запуск AI Text Processor API")
    logger.info("=" * 60)
    logger.info(f"Режим работы AI: {'MOCK' if settings.USE_MOCK_AI else 'REAL (OpenAI)'}")
    logger.info(f"Хост: {settings.APP_HOST}:{settings.APP_PORT}")
    logger.info(f"Debug: {settings.APP_DEBUG}")
    logger.info("=" * 60)

    # Инициализируем процессор
    get_processor(
        use_mock=settings.USE_MOCK_AI,
        api_key=settings.OPENAI_API_KEY if not settings.USE_MOCK_AI else None,
        model=settings.OPENAI_MODEL,
    )

    yield  # Приложение работает

    # === SHUTDOWN ===
    logger.info("🛑 Остановка приложения...")
    reset_processor()
    logger.info("Приложение остановлено")


# ============================================================================
# СОЗДАНИЕ FASTAPI ПРИЛОЖЕНИЯ
# ============================================================================

app = FastAPI(
    title="AI Text Processor",
    description="""
    ## AI-агент для обработки текстовых обращений
    
    Этот сервис принимает текстовые обращения, определяет их тип,
    создаёт краткое резюме и возвращает структурированный JSON-ответ.
    
    ### Возможности:
    - **Классификация** обращений по типам (TECH_SUPPORT, SALES, COMPLAINT, GENERAL)
    - **Суммаризация** текста обращения
    - **Оценка уверенности** AI в определении типа
    - **Два режима работы**: Mock (эвристика) и Real (OpenAI API)
    
    ### Режимы работы:
    - `USE_MOCK_AI=true` — эвристическая обработка на ключевых словах (по умолчанию)
    - `USE_MOCK_AI=false` — обработка через OpenAI API (требует OPENAI_API_KEY)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ============================================================================
# CORS MIDDLEWARE (опционально, для интеграции с фронтендом)
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ОБРАБОТЧИКИ ОШИБОК
# ============================================================================


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Обработчик ошибок валидации Pydantic."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Ошибка валидации входных данных",
            details={"errors": exc.errors()},
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик непредвиденных ошибок."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="Внутренняя ошибка сервера",
            details={"detail": str(exc)} if settings.APP_DEBUG else None,
        ).model_dump(),
    )


# ============================================================================
# ЭНДПОИНТЫ
# ============================================================================


@app.get(
    "/health",
    tags=["Service"],
    summary="Проверка работоспособности",
    response_description="Статус сервиса",
)
async def health_check():
    """
    Эндпоинт для проверки работоспособности сервиса.

    Используется для health checks в Kubernetes/Docker.
    """
    return {
        "status": "healthy",
        "service": "AI Text Processor",
        "version": "1.0.0",
        "mode": "mock" if settings.USE_MOCK_AI else "real",
    }


@app.get(
    "/", tags=["Service"], summary="Корневой эндпоинт", response_description="Информация о сервисе"
)
async def root():
    """Корневой эндпоинт с базовой информацией."""
    return {
        "service": "AI Text Processor",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.post(
    "/api/v1/process",
    response_model=ProcessResponse,
    status_code=200,
    tags=["Processing"],
    summary="Обработка текстового обращения",
    response_description="Структурированный результат обработки",
    responses={
        200: {
            "description": "Успешная обработка",
            "content": {
                "application/json": {
                    "example": {
                        "request_type": "TECH_SUPPORT",
                        "summary": "Пользователь сообщает о проблеме с входом в систему.",
                        "confidence": 0.95,
                        "is_processed_by_mock": True,
                    }
                }
            },
        },
        422: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {
                        "error": "VALIDATION_ERROR",
                        "message": "Ошибка валидации входных данных",
                        "details": {},
                    }
                }
            },
        },
        502: {
            "description": "Ошибка AI-провайдера",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AI_PROVIDER_ERROR",
                        "message": "Ошибка при обращении к AI-провайдеру",
                        "details": {},
                    }
                }
            },
        },
    },
)
async def process_text(request: ProcessRequest):
    """
    Обработать текстовое обращение.

    Принимает текст, определяет его тип, создаёт краткое резюме
    и возвращает структурированный JSON-ответ.

    - **text**: Текст обращения (обязательное поле, 1-10000 символов)

    Возвращает:
    - **request_type**: Определённый тип запроса
    - **summary**: Краткое содержание (1-3 предложения)
    - **confidence**: Уверенность AI (0.0-1.0)
    - **is_processed_by_mock**: Флаг использования мока
    """
    logger.info(f"Получен запрос на обработку. Длина текста: {len(request.text)} символов")

    try:
        # Получаем процессор
        processor: TextProcessor = get_processor()

        # Обрабатываем запрос
        response = await processor.process(request)

        logger.info(
            f"Запрос успешно обработан. "
            f"Тип: {response.request_type}, "
            f"Уверенность: {response.confidence}"
        )

        return response

    except ValidationError as e:
        # Ошибка валидации ответа от AI
        logger.error(f"AI provider returned invalid response: {e}")
        raise HTTPException(
            status_code=502,
            detail=ErrorResponse(
                error="AI_PROVIDER_ERROR",
                message="AI-провайдер вернул невалидный ответ",
                details={"detail": str(e)},
            ).model_dump(),
        )

    except Exception as e:
        # Любая другая ошибка
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=ErrorResponse(
                error="AI_PROVIDER_ERROR",
                message="Ошибка при обработке запроса",
                details={"detail": str(e)} if settings.APP_DEBUG else None,
            ).model_dump(),
        )


# ============================================================================
# ТОЧКА ВХОДА ДЛЯ ЗАПУСКА ЧЕРЕЗ `python -m app.main`
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.APP_DEBUG
    )
