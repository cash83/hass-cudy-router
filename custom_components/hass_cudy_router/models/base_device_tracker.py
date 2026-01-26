from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.hass_cudy_router.const import DOMAIN, MODULE_DEVICES

# Try strict constant first, fallback to legacy string
try:
    from .const import DEVICE_LIST  # type: ignore
except Exception:
    DEVICE_LIST = "device_list"


class BaseCudyDeviceTracker(CoordinatorEntity, TrackerEntity):

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

        devs = devices_block.get(DEVICE_LIST, [])
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

            # Wired → always connected
            if connection_type == "wired":
                return True

            # Wi-Fi → connected if signal is meaningful
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