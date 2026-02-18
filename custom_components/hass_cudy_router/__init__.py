from __future__ import annotations

import inspect
import importlib.util
import logging
from typing import Any, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import registry
from .client import CudyClient
from .const import DOMAIN, PLATFORMS as DEFAULT_PLATFORMS
from .model_detect import detect_model

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    protocol = entry.data.get("protocol", "http")
    use_https = protocol.lower() in ("https", "ssl", "tls")

    client = CudyClient(
        host=entry.data.get("host"),
        username=entry.data.get("username"),
        password=entry.data.get("password"),
        use_https=use_https,
    )

    try:
        model = await detect_model(client)
    except Exception:
        _LOGGER.debug("Model detection failed, falling back to Generic", exc_info=True)
        model = "Generic"

    integration = await registry.create_model_integration(model, hass, entry, client)

    if hasattr(integration, "platforms") and getattr(integration, "platforms") is not None:
        platforms = list(getattr(integration, "platforms"))
    elif hasattr(integration, "spec") and getattr(integration, "spec") is not None:
        try:
            platforms = list(getattr(integration, "spec").platforms)
        except Exception:
            platforms = list(DEFAULT_PLATFORMS)
    else:
        platforms = list(DEFAULT_PLATFORMS)

    filtered: List[str] = []
    for platform in platforms:
        if importlib.util.find_spec(f"{__package__}.{platform}") is not None:
            filtered.append(platform)
        else:
            _LOGGER.debug("Skipping missing platform module: %s.%s", __package__, platform)
    platforms = filtered

    if hasattr(integration, "async_setup"):
        try:
            maybe_coro = integration.async_setup()
            if inspect.isawaitable(maybe_coro):
                await maybe_coro
        except Exception:
            _LOGGER.exception("Error while running integration.async_setup()")

    coordinator = getattr(integration, "coordinator", None)
    if coordinator is not None and hasattr(coordinator, "async_config_entry_first_refresh"):
        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception:
            _LOGGER.debug("Coordinator first refresh failed (continuing setup)", exc_info=True)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "integration": integration,
        "coordinator": getattr(integration, "coordinator", None),
        "platforms": platforms,
    }

    try:
        await hass.config_entries.async_forward_entry_setups(entry, platforms)
    except Exception:
        _LOGGER.exception("Failed to forward platforms for hass_cudy_router")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data: dict[str, Any] | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not data:
        return True

    platforms = data.get("platforms") or []

    try:
        await hass.config_entries.async_unload_platforms(entry, list(platforms))
    except Exception:
        _LOGGER.exception("Error unloading platforms for hass_cudy_router")

    client = data.get("client")
    if client:
        close_fn = getattr(client, "async_close", None) or getattr(client, "close", None)
        if callable(close_fn):
            try:
                result = close_fn()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                _LOGGER.debug("Error closing CudyClient", exc_info=True)

    return True