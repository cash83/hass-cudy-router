from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import *

_LOGGER = logging.getLogger(__name__)

REBOOT_BUTTON = ButtonEntityDescription(
    key="reboot",
    translation_key="reboot",
    name="Reboot",
    icon="mdi:restart",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([CudyRebootButton(hass, entry)])


class CudyRebootButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry

        entry_data = getattr(entry, "data", {})
        self._host = entry_data.get("host", "") if isinstance(entry_data, dict) else ""

        self.entity_description = REBOOT_BUTTON
        self._attr_unique_id = f"{entry.entry_id}_button_reboot"

    @property
    def device_info(self) -> DeviceInfo:
        stable_id = (
            getattr(self._entry, "unique_id", None)
            or self._host
            or getattr(self._entry, "entry_id", "")
        )

        # Try to show firmware on the device card if coordinator already fetched it
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        coordinator = data.get("coordinator")
        coord_data = getattr(coordinator, "data", None) or {}
        system = coord_data.get(MODULE_SYSTEM, {}) if isinstance(coord_data, dict) else {}

        model = None
        if isinstance(system, dict):
            model = system.get(SENSOR_SYSTEM_MODEL)
        sw_version = None
        if isinstance(system, dict):
            sw_version = system.get(SENSOR_SYSTEM_FIRMWARE_VERSION) or system.get(SENSOR_SYSTEM_HARDWARE)

        return DeviceInfo(
            identifiers={(DOMAIN, stable_id)},
            name=f"Cudy Router ({self._host})" if self._host else "Cudy Router",
            manufacturer="Cudy",
            model=model,
            sw_version=sw_version,
        )

    async def async_press(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        integration = data.get("integration")
        coordinator = data.get("coordinator")
        client = data.get("client")

        # 1) integration.async_reboot()
        fn = getattr(integration, "async_reboot", None)
        if callable(fn):
            await fn()
            return

        # 2) coordinator.async_reboot()
        fn = getattr(coordinator, "async_reboot", None)
        if callable(fn):
            await fn()
            return

        # 3) client.async_reboot() or client.reboot()
        fn = getattr(client, "async_reboot", None)
        if callable(fn):
            await fn()
            return

        fn = getattr(client, "reboot", None)
        if callable(fn):
            result = fn()
            if hasattr(result, "__await__"):
                await result
            return

        _LOGGER.error(
            "Reboot requested but no reboot method found. "
            "Implement integration.async_reboot() or coordinator.async_reboot()."
        )