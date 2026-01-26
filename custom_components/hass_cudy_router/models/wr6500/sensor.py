from __future__ import annotations

from typing import Final, Any, Iterable, Set

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ...const import *
from .coordinator import WR6500Coordinator

# Build groups of keys that belong to modules (use sets for fast membership checks)
SYSTEM_KEYS: Set[str] = {
    SENSOR_FIRMWARE_VERSION,
    SENSOR_HARDWARE,
    SENSOR_SYSTEM_UPTIME,
}

MESH_KEYS: Set[str] = {
    SENSOR_MESH_NETWORK,
    SENSOR_MESH_UNITS
}

WAN_KEYS: Set[str] = {
    SENSOR_WAN_PUBLIC_IP,
    SENSOR_WAN_IP,
    SENSOR_WAN_DNS,
    SENSOR_WAN_TYPE,
    SENSOR_WAN_UPTIME,
}

LAN_KEYS: Set[str] = {
    SENSOR_LAN_IP,
}

DEVICE_COUNT_KEYS: Set[str] = {
    SENSOR_DEVICE_COUNT,
    SENSOR_WIFI_24_DEVICE_COUNT,
    SENSOR_WIFI_5_DEVICE_COUNT,
    SENSOR_WIRED_DEVICE_COUNT,
    SENSOR_MESH_DEVICE_COUNT,
}

# Define sensors we want for WR6500. Model package owns which sensors are present.
SENSOR_DESCRIPTIONS: Final[tuple[SensorEntityDescription, ...]] = (
    # SYSTEM
    SensorEntityDescription(
        key=SENSOR_FIRMWARE_VERSION,
        name="Firmware Version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_HARDWARE,
        name="Hardware",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_SYSTEM_UPTIME,
        name="Connected Time",
        icon="mdi:clock-check",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # MESH
    SensorEntityDescription(
        key=SENSOR_MESH_NETWORK,
        name="Mesh Network",
        icon="mdi:router-network-wireless",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_MESH_UNITS,
        name="Mesh Units",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # WAN
    SensorEntityDescription(
        key=SENSOR_WAN_PUBLIC_IP,
        name="WAN Public IP Address",
        icon="mdi:earth",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_WAN_IP,
        name="WAN IP Address",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_WAN_DNS,
        name="WAN DNS Address(es)",
        icon="mdi:dns",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_WAN_TYPE,
        name="Connection Type",
        icon="mdi:transit-connection-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_WAN_UPTIME,
        name="WAN Connected Time",
        icon="mdi:clock-check",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # LAN
    SensorEntityDescription(
        key=SENSOR_LAN_IP,
        name="LAN IP Address",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # DEVICES COUNTS
    SensorEntityDescription(
        key=SENSOR_DEVICE_COUNT,
        name="Total Devices Connected",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_WIFI_24_DEVICE_COUNT,
        name="2.4GHz WiFi Devices Connected",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_WIFI_5_DEVICE_COUNT,
        name="5GHz WiFi Devices Connected",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_WIRED_DEVICE_COUNT,
        name="Wired Devices Connected",
        icon="mdi:lan",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_MESH_DEVICE_COUNT,
        name="Mesh Devices Connected",
        icon="mdi:router-network",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

# Backwards-compatible alias/tests expect this name
SENSOR_TYPES: Final = SENSOR_DESCRIPTIONS


def _resolve_coordinator(stored: Any) -> WR6500Coordinator:
    """Resolve coordinator object from hass.data storage patterns."""
    if isinstance(stored, WR6500Coordinator):
        return stored
    if isinstance(stored, dict):
        if "coordinator" in stored and isinstance(stored["coordinator"], WR6500Coordinator):
            return stored["coordinator"]
        if "integration" in stored and hasattr(stored["integration"], "coordinator"):
            return stored["integration"].coordinator
    if hasattr(stored, "coordinator") and isinstance(stored.coordinator, WR6500Coordinator):
        return stored.coordinator
    raise ValueError("Could not resolve WR6500Coordinator from hass.data")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for a config entry."""
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = _resolve_coordinator(stored)

    entities = [WR6500Sensor(coordinator, desc, entry) for desc in SENSOR_DESCRIPTIONS]
    async_add_entities(entities)


class WR6500Sensor(CoordinatorEntity[WR6500Coordinator], SensorEntity):
    """Single WR6500 sensor backed by the model coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WR6500Coordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        host = getattr(coordinator, "host", None) or entry.data.get("host") or entry.unique_id or entry.entry_id
        self._attr_unique_id = f"cudy_{host}_{description.key}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "manufacturer": "Cudy",
            "name": f"Cudy Router {host}",
        }

    @property
    def native_value(self) -> Any:
        """Return the value for this sensor based on coordinator data and const -> module mapping."""
        data = self.coordinator.data or {}

        key = self.entity_description.key

        # System keys
        if key in SYSTEM_KEYS:
            module = data.get(MODULE_SYSTEM, {})
            return module.get(key)

        # Mesh keys
        if key in MESH_KEYS:
            module = data.get(MODULE_MESH, {})
            return module.get(key)

        # WAN keys
        if key in WAN_KEYS:
            module = data.get(MODULE_WAN, {})
            return module.get(key)

        # LAN keys
        if key in LAN_KEYS:
            module = data.get(MODULE_LAN, {})
            return module.get(key)

        # Device count / devices-related keys
        if key in DEVICE_COUNT_KEYS:
            module = data.get(MODULE_DEVICES, {})
            return module.get(key)

        # Fallback: try top-level by key
        return data.get(key)