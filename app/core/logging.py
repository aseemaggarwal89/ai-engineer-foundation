import logging
import sys
from typing import Any, Dict
import json
from datetime import date, datetime, timezone
from uuid import UUID
from app.core.request_context import request_id_ctx


def setup_logging(level: str) -> None:
    configure_logging(level)
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("passlib.handlers").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # logging.basicConfig(
    #     level=level,
    #     format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    # )


STANDARD_ATTRS = {
    "name", "msg", "args", "levelname", "levelno",
    "pathname", "filename", "module", "exc_info",
    "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process",
    "taskName"
}


class JsonFormatter(logging.Formatter):    
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # ✅ request correlation
        request_id = request_id_ctx.get()
        if request_id:
            log_record["request_id"] = request_id

        # ✅ capture extra fields properly
        for key, value in record.__dict__.items():
            if key not in STANDARD_ATTRS:
                if isinstance(value, (UUID, datetime, date)):
                    log_record[key] = str(value)
                else:
                    log_record[key] = value

        return json.dumps(log_record)


def configure_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)