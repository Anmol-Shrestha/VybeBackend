"""Global tracer instance and decorators for OTel spans."""

import functools
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("vybe.food_search")


def trace_span(span_name: str, **static_attrs):
    """Decorator for async functions: wraps execution in an OTel span.

    Args:
        span_name: The span name (e.g., "hybrid_search.embed_query")
        **static_attrs: Attributes to set on the span that don't change (e.g., model="text-embedding-3-small")

    Usage:
        @trace_span("my_operation", model="gpt-4")
        async def my_func(query: str):
            return process(query)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                # Set static attributes
                for key, value in static_attrs.items():
                    span.set_attribute(key, value)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        return wrapper
    return decorator
