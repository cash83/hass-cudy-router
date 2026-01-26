"""Button platform for Cudy WR6500 Router."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.hass_cudy_router.const import DOMAIN
from .coordinator import WR6500Coordinator

_LOGGER = logging.getLogger(__name__)


BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart-alert",
    ),
)


def _resolve_coordinator(stored: Any) -> WR6500Coordinator:
    if isinstance(stored, WR6500Coordinator):
        return stored
    if isinstance(stored, dict):
        if "coordinator" in stored and isinstance(stored["coordinator"], WR6500Coordinator):
            return stored["coordinator"]
        if "integration" in stored and hasattr(stored["integration"], "coordinator"):
            return stored["integration"].coordinator
    if hasattr(stored, "coordinator") and isinstance(stored.coordinator, WR6500Coordinator):
        return stored.coordinator
    # fallback for tests
    if hasattr(stored, "data"):
        return stored  # type: ignore[return-value]
    raise ValueError("Could not resolve WR6500Coordinator from hass.data")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WR6500 reboot button."""
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = _resolve_coordinator(stored)

    async_add_entities(
        [CudyRouterRebootButton(coordinator, entry, desc) for desc in BUTTON_TYPES]
    )


class CudyRouterRebootButton(CoordinatorEntity[WR6500Coordinator], ButtonEntity):
    """Reboot button for the Cudy WR6500 router."""

    def __init__(
        self,
        coordinator: WR6500Coordinator,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        host = (
            getattr(coordinator, "host", None)
            or entry.data.get("host")
            or entry.unique_id
            or entry.entry_id
        )

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = f"Cudy Router {host} {description.name}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "manufacturer": "Cudy",
            "name": f"Cudy Router {host}",
        }

    async def async_press(self) -> None:
        """Handle reboot button press."""
        _LOGGER.warning("Reboot button pressed for %s", self.coordinator.host)

        await self.coordinator.api.async_reboot(self.hass)