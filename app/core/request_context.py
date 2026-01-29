from contextvars import ContextVar
from typing import Optional

# Holds request_id for the current async context
request_id_ctx: ContextVar[Optional[str]] = ContextVar(
    "request_id",
    default=None,
)
