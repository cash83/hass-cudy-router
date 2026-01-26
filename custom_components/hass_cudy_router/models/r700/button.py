from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.hass_cudy_router.const import DOMAIN

from .coordinator import R700Coordinator
from ..base_button import BaseCudyButton

_LOGGER = logging.getLogger(__name__)


BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart-alert",
    ),
)


def _resolve_coordinator(stored: Any) -> R700Coordinator:
    if isinstance(stored, R700Coordinator):
        return stored
    if isinstance(stored, dict):
        if "coordinator" in stored and isinstance(stored["coordinator"], R700Coordinator):
            return stored["coordinator"]
        if "integration" in stored and hasattr(stored["integration"], "coordinator"):
            return stored["integration"].coordinator
    if hasattr(stored, "coordinator") and isinstance(stored.coordinator, R700Coordinator):
        return stored.coordinator
    # fallback for tests
    if hasattr(stored, "data"):
        return stored  # type: ignore[return-value]
    raise ValueError("Could not resolve R700Coordinator from hass.data")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = _resolve_coordinator(stored)

    async_add_entities(
        [WR6500RebootButton(coordinator, entry, desc) for desc in BUTTON_TYPES]
    )


class WR6500RebootButton(BaseCudyButton):

    def __init__(
        self,
        coordinator: R700Coordinator,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        super().__init__(
            coordinator,
            entry,
            description,
            domain=DOMAIN,
            manufacturer="Cudy",
            device_name_prefix="Cudy Router",
        )

    async def async_action(self) -> None:
        _LOGGER.warning(
            "Reboot button pressed for %s", getattr(self.coordinator, "host", "unknown")
        )
        await self.coordinator.api.async_reboot(self.hass)