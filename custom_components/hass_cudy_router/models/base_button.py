from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class BaseCudyButton(CoordinatorEntity, ButtonEntity):

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
        *,
        domain: str,
        manufacturer: str = "Cudy",
        device_name_prefix: str = "Cudy Router",
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        host = (
            getattr(coordinator, "host", None)
            or entry.data.get("host")
            or entry.unique_id
            or entry.entry_id
        )

        # Keep the same unique_id convention used elsewhere in the project/tests.
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = f"{device_name_prefix} {host} {description.name}"

        self._attr_device_info = {
            "identifiers": {(domain, host)},
            "manufacturer": manufacturer,
            "name": f"{device_name_prefix} {host}",
        }

    async def async_press(self) -> None:
        """Handle button press."""
        await self.async_action()

    async def async_action(self) -> None:
        """Perform the model-specific action."""
        raise NotImplementedError