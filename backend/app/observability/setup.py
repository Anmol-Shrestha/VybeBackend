"""Arize Phoenix initialization and instrumentation setup."""

import logging
import os
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_phoenix(app: FastAPI):
    """Initialize Arize Phoenix embedded server and instrument OpenTelemetry.

    This function:
    1. Launches Phoenix embedded server (UI at http://localhost:6006)
    2. Registers Phoenix as the global OTel tracer provider
    3. Auto-instruments FastAPI for HTTP spans
    4. Auto-instruments OpenAI client for embedding spans

    Call this at the very top of FastAPI lifespan startup, before any service construction.
    """
    try:
        import phoenix as px
        from phoenix.otel import register
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

        # 1. Launch the background UI dashboard server (disabled for container deployment)
        # px.launch_app()
        # logger.info("✅ Phoenix embedded server launched at http://localhost:6006")

        # 2. Globally bind the OpenTelemetry context to Phoenix
        phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
        register(project_name="vybe-food-rag", endpoint=phoenix_endpoint)
        logger.info(f"✅ Registered global OpenTelemetry TracerProvider targeting Phoenix at {phoenix_endpoint}")

        # 3. Auto-instrument FastAPI (adds HTTP root spans)
        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ FastAPI instrumented for HTTP request tracing")

        # 4. Auto-instrument OpenAI (adds EMBEDDING spans for embedding calls)
        OpenAIInstrumentor().instrument()
        logger.info("✅ OpenAI instrumented for embedding tracing")

    except ImportError as e:
        logger.warning(f"Phoenix or instrumentation packages not installed: {e}. Tracing disabled.")
    except Exception as e:
        logger.warning(f"Error setting up Phoenix observability: {e}. Continuing without tracing.")
