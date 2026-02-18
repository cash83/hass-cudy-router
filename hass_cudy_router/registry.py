from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .client import CudyClient
from .coordinator import CudyCoordinator
from .api import CudyApi
from .const import CUDY_DEVICES

_LOGGER = logging.getLogger(__name__)


class CudyIntegration:
    """Runtime integration instance.

    This integration is model-aware but behavior is fully dynamic
    (capabilities + parser driven).
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: CudyClient,
        model: str,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.client = client
        self.model = model

        self.api = CudyApi(client)

        self.coordinator = CudyCoordinator(
            hass=hass,
            entry=entry,
            api=self.api,
            host=entry.data.get("host"),
        )

    async def async_setup(self) -> None:
        await self.coordinator.async_config_entry_first_refresh()


async def create_model_integration(
    model: str,
    hass: HomeAssistant,
    entry: ConfigEntry,
    client: CudyClient,
) -> CudyIntegration:
    if model not in CUDY_DEVICES:
        _LOGGER.error("Unsupported or unknown Cudy model detected: %s", model)
        raise ValueError(f"Unsupported Cudy model: {model}")

    integration = CudyIntegration(
        hass=hass,
        entry=entry,
        client=client,
        model=model,
    )
    await integration.async_setup()
    return integration