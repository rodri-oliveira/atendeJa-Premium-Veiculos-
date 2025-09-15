from __future__ import annotations
from typing import Protocol, Optional, Dict, Any
from app.core.config import settings


class IMessagingProvider(Protocol):
    def send_text(self, to: str, text: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        ...

    def send_template(self, to: str, template_name: str, language: str = "pt_BR", components: Optional[list] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        ...

    def mark_read(self, message_id: str) -> Dict[str, Any]:
        ...


_provider_singleton: Optional[IMessagingProvider] = None


def get_provider() -> IMessagingProvider:
    global _provider_singleton
    if _provider_singleton is not None:
        return _provider_singleton

    provider_name = (settings.WA_PROVIDER or "meta").lower()
    if provider_name == "meta":
        from .meta import MetaCloudProvider

        _provider_singleton = MetaCloudProvider(
            api_base=settings.WA_API_BASE,
            token=settings.WA_TOKEN,
            phone_number_id=settings.WA_PHONE_NUMBER_ID,
        )
        return _provider_singleton
    elif provider_name == "noop":
        from .noop import NoopProvider

        _provider_singleton = NoopProvider()
        return _provider_singleton
    else:
        # Fallback: usar Meta como default para simplificar
        from .meta import MetaCloudProvider

        _provider_singleton = MetaCloudProvider(
            api_base=settings.WA_API_BASE,
            token=settings.WA_TOKEN,
            phone_number_id=settings.WA_PHONE_NUMBER_ID,
        )
        return _provider_singleton
