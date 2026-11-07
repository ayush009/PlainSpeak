"""Application factory and production server entry point."""

import logging
import time
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from plainspeak.ai.client import LLM, ClaudeClient, GeminiClient, GroqClient, OllamaClient, OpenRouterClient, TUBSClient
from plainspeak.api import router
from plainspeak.config import Settings, get_settings
from plainspeak.storage import CaseStore

STATIC_DIR = Path(__file__).parent / "static"

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, llm: LLM | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="PlainSpeak",
        description=(
            "AI-powered care intelligence — bridging clinical expertise and everyday understanding. "
            "Turns discharge instructions into grounded, voice-accessible care guidance."
        ),
        version="1.0.0",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
    )

    app.state.store = CaseStore(settings.cases_dir, settings.uploads_dir)
    if llm is not None:
        app.state.llm = llm
    elif settings.tubs_api_key:
        log.info("Using TUBS backend: model=%s", settings.tubs_model)
        app.state.llm = TUBSClient(settings)
    elif settings.gemini_api_key:
        log.info("Using Gemini backend: model=%s", settings.gemini_model)
        app.state.llm = GeminiClient(settings)
    elif settings.groq_api_key:
        log.info("Using Groq backend: model=%s", settings.groq_model)
        app.state.llm = GroqClient(settings)
    elif settings.openrouter_api_key:
        log.info("Using OpenRouter backend: model=%s", settings.openrouter_model)
        app.state.llm = OpenRouterClient(settings)
    elif settings.use_ollama or not settings.anthropic_api_key:
        log.info("Using Ollama backend: model=%s url=%s", settings.ollama_model, settings.ollama_base_url)
        app.state.llm = OllamaClient(settings)
    else:
        log.info("Using Claude backend: model=%s", settings.anthropic_model)
        app.state.llm = ClaudeClient(settings)

    # Compress responses larger than 1 KB
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # CORS — restrict to configured origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_middleware(request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex[:12]
        start = time.perf_counter()

        try:
            response: Response = await call_next(request)
        except Exception:
            log.exception("Unhandled exception req_id=%s path=%s", request_id, request.url.path)
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        # Skip logging static asset requests to keep logs clean
        if not request.url.path.startswith("/static") and request.url.path not in ("/", "/favicon.ico"):
            log.info(
                "req_id=%s method=%s path=%s status=%d ms=%.1f",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )

        # Security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response

    app.include_router(router)
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
    return app


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    settings = get_settings()
    log.info(
        "Starting PlainSpeak v1.0 on %s:%d (env=%s)",
        settings.host,
        settings.port,
        settings.app_env,
    )
    uvicorn.run(
        "plainspeak.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
        workers=1,
        access_log=False,  # handled by our middleware
        log_level="warning",
    )


if __name__ == "__main__":
    run()
