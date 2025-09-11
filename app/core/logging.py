import logging
import sys
import structlog
from typing import Any, Mapping


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    SENSITIVE_KEYS = {
        "authorization",
        "x-hub-signature-256",
        "token",
        "access_token",
        "secret",
        "signature",
        "wa_token",
        "wa_webhook_secret",
    }

    def _mask(value: str) -> str:
        if not isinstance(value, str):
            return "***"
        if len(value) <= 8:
            return "***"
        return value[:2] + "***" + value[-2:]

    def _redact_mapping(d: Mapping[str, Any]) -> dict:
        out = {}
        for k, v in d.items():
            lk = str(k).lower()
            if lk in SENSITIVE_KEYS:
                out[k] = _mask(str(v))
            elif isinstance(v, Mapping):
                out[k] = _redact_mapping(v)
            else:
                out[k] = v
        return out

    def redact_processor(logger, method_name, event_dict):  # type: ignore[no-untyped-def]
        # Redact common containers like headers/payload and flat keys
        redacted = {}
        for k, v in event_dict.items():
            lk = str(k).lower()
            if lk in SENSITIVE_KEYS:
                redacted[k] = _mask(str(v))
            elif isinstance(v, Mapping):
                redacted[k] = _redact_mapping(v)
            else:
                redacted[k] = v
        return redacted

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            timestamper,
            redact_processor,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
