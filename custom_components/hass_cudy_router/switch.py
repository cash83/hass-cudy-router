from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MODULE_SYSTEM,
    SENSOR_SYSTEM_MODEL,
    SENSOR_SYSTEM_FIRMWARE_VERSION,
    SENSOR_SYSTEM_HARDWARE,
)

_LOGGER = logging.getLogger(__name__)

WIFI_24 = SwitchEntityDescription(
    key="wifi_24",
    name="Wi-Fi 2.4 GHz",
    icon="mdi:wifi",
)

WIFI_5 = SwitchEntityDescription(
    key="wifi_5",
    name="Wi-Fi 5 GHz",
    icon="mdi:wifi",
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            CudyWifiSwitch(hass, entry, band="2g", description=WIFI_24),
            CudyWifiSwitch(hass, entry, band="5g", description=WIFI_5),
        ]
    )


class CudyWifiSwitch(SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        band: str,
        description: SwitchEntityDescription,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._band = band  # "2g" / "5g"
        self.entity_description = description

        entry_data = getattr(entry, "data", {}) or {}
        self._host = entry_data.get("host", "") if isinstance(entry_data, dict) else ""

        self._attr_unique_id = f"{entry.entry_id}_wifi_{band}"
        self._attr_is_on = False  # verrà valorizzato da async_update

    def _get_objects(self) -> tuple[Any, Any, Any]:
        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        return data.get("client"), data.get("integration"), data.get("coordinator")

    @property
    def device_info(self) -> DeviceInfo:
        stable_id = getattr(self._entry, "unique_id", None) or self._host or self._entry.entry_id

        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        coordinator = data.get("coordinator")
        coord_data = getattr(coordinator, "data", None) or {}
        system = coord_data.get(MODULE_SYSTEM, {}) if isinstance(coord_data, dict) else {}

        model = system.get(SENSOR_SYSTEM_MODEL) if isinstance(system, dict) else None
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

    async def async_added_to_hass(self) -> None:
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Legge lo stato reale dal router (se supportato dal client)."""
        client, integration, coordinator = self._get_objects()

        # prefer client, ma accettiamo anche integration/coordinator se espongono async_get_wifi_state()
        getter = None
        for obj in (client, integration, coordinator):
            fn = getattr(obj, "async_get_wifi_state", None)
            if callable(fn):
                getter = fn
                break

        if not getter:
            # niente lettura stato -> non inventiamo cose
            return

        try:
            st = await getter()  # atteso: {"2g": bool, "5g": bool}
            if isinstance(st, dict):
                if self._band == "2g" and "2g" in st:
                    self._attr_is_on = bool(st["2g"])
                elif self._band == "5g" and "5g" in st:
                    self._attr_is_on = bool(st["5g"])
        except Exception as e:
            _LOGGER.debug("Wi-Fi state read failed (%s): %s", self._band, e)

    async def async_turn_on(self) -> None:
        await self._set_wifi(True)

    async def async_turn_off(self) -> None:
        await self._set_wifi(False)

    async def _set_wifi(self, enabled: bool) -> None:
        client, integration, coordinator = self._get_objects()

        # Prova async_set_wifi(band, enabled) dove disponibile
        setter = None
        for obj in (integration, coordinator, client):
            fn = getattr(obj, "async_set_wifi", None)
            if callable(fn):
                setter = fn
                break

        if not setter:
            _LOGGER.error("Wi-Fi switch pressed but no async_set_wifi() found in integration/coordinator/client")
            return

        try:
            await setter(self._band, enabled)
        except TypeError:
            # compat: alcune implementazioni accettano solo (enabled)
            await setter(enabled)

        # Dopo il comando: rileggi lo stato reale e aggiorna HA
        await self.async_update()
        self.async_write_ha_state()
