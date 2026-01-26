"""Device tracker platform for Cudy Router."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.hass_cudy_router.const import (
    DOMAIN,
    OPTIONS_DEVICELIST,
    MODULE_DEVICES,
)

from .coordinator import WR6500Coordinator

_LOGGER = logging.getLogger(__name__)

# DATA keys stored in coordinator.data[MODULE_DEVICES]
try:
    from custom_components.hass_cudy_router.const import DEVICE_LIST as _DEVICE_LIST_KEY  # type: ignore
except Exception:
    _DEVICE_LIST_KEY = "device_list"

try:
    from custom_components.hass_cudy_router.const import DEVICE_COUNT as _DEVICE_COUNT_KEY  # type: ignore
except Exception:
    _DEVICE_COUNT_KEY = "device_count"


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

    # ✅ test/loose fallback: accept any coordinator-like object with .data
    if hasattr(stored, "data"):
        return stored  # type: ignore[return-value]

    raise ValueError("Could not resolve WR6500Coordinator from hass.data")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker entities from a config entry."""
    stored = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = _resolve_coordinator(stored)

    device_list_opt = config_entry.options.get(OPTIONS_DEVICELIST, "")
    tracked_macs = [mac.strip().lower() for mac in device_list_opt.split(",") if mac.strip()]

    if not tracked_macs:
        _LOGGER.debug("No device MACs configured for tracking")
        return

    async_add_entities(CudyRouterDeviceTracker(coordinator, mac) for mac in tracked_macs)


class CudyRouterDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Device tracker for a device connected to the Cudy Router."""

    _attr_source_type = SourceType.ROUTER
    _attr_should_poll = False

    def __init__(self, coordinator: Any, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac.lower()

        self._attr_unique_id = f"cudy_device_{self._mac.replace(':', '').replace('-', '')}"
        self._attr_name = f"Cudy Device {self._mac}"

        host = getattr(coordinator, "host", None) or "unknown"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "manufacturer": "Cudy",
            "name": f"Cudy Router {host}",
        }

    @property
    def available(self) -> bool:
        return bool(getattr(self.coordinator, "last_update_success", False))

    def _device_list(self) -> list[dict[str, Any]]:
        devices_block = (self.coordinator.data or {}).get(MODULE_DEVICES, {})
        if not isinstance(devices_block, dict):
            return []
        devs = devices_block.get(_DEVICE_LIST_KEY, [])
        return devs if isinstance(devs, list) else []

    @property
    def is_connected(self) -> bool:
        for dev in self._device_list():
            if not isinstance(dev, dict):
                continue
            if dev.get("mac", "").lower() != self._mac:
                continue

            connection_type = (dev.get("connection_type") or "").lower()
            signal = dev.get("signal")

            if connection_type == "wired":
                return True

            if signal is not None and str(signal).strip() not in ("", "---"):
                return True

            return False

        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        for dev in self._device_list():
            if isinstance(dev, dict) and dev.get("mac", "").lower() == self._mac:
                return dict(dev)
        return {}