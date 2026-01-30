from opentelemetry import trace
from functools import wraps

tracer = trace.get_tracer("ai_engineer_app")


def traced(name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
