from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import *
from .coordinator import CudyCoordinator


def _device_unique_id(entry_id: str, mac: str) -> str:
    mac_norm = (mac or "").strip().lower().replace(":", "")
    return f"{entry_id}_dev_{mac_norm}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CudyCoordinator = data["coordinator"]
    spec = data.get("spec")
    if spec and "device_tracker" not in getattr(spec, "platforms", set()):
        return
    devices = _get_devices(coordinator.data)
    entities = [
        CudyDeviceTracker(coordinator, entry, dev)
        for dev in devices
    ]
    async_add_entities(entities)


def _get_devices(coordinator_data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not coordinator_data:
        return []
    mod = coordinator_data.get(MODULE_DEVICES, {}) or {}
    devs = mod.get(MODULE_DEVICE_LIST, []) or []
    return [
        d for d in devs
        if isinstance(d, dict) and d.get(DEVICE_MAC)
    ]


class CudyDeviceTracker(CoordinatorEntity, TrackerEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CudyCoordinator,
        entry: ConfigEntry,
        device: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._initial = device  # IMPORTANT fallback for attributes
        self._mac = str(device.get(DEVICE_MAC) or "").strip()
        hostname = (device.get(DEVICE_HOSTNAME) or "").strip()
        self._attr_name = hostname or self._mac
        self._attr_unique_id = _device_unique_id(entry.entry_id, self._mac)

    @property
    def source_type(self) -> str:
        return "router"

    @property
    def mac_address(self) -> str | None:
        return self._mac or None

    @property
    def ip_address(self) -> str | None:
        dev = self._find_self()
        ip = (dev.get(DEVICE_IP) if dev else None) or None
        return str(ip) if ip else None

    @property
    def is_connected(self) -> bool:
        dev = self._find_self()
        if not dev:
            return False
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        dev = self._find_self()
        if dev is None:
            dev = self._initial
        return dev if isinstance(dev, dict) else None

    def _find_self(self) -> dict[str, Any] | None:
        devices = _get_devices(getattr(self.coordinator, "data", None))
        for d in devices:
            if str(d.get(DEVICE_MAC) or "").strip().lower() == self._mac.lower():
                return d
        return None