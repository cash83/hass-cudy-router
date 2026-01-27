from __future__ import annotations

from typing import Final

from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.hass_cudy_router.const import *

from .coordinator import P5Coordinator
from ..base_sensor import BaseCudySensor

P5_MODULE_MAP: Final = {
    "info_": MODULE_INFO,
    "system_": MODULE_SYSTEM,
    "mesh_": MODULE_DEVICES,
    "lan_": MODULE_LAN,
    "24g_": MODULE_WIRELESS_24G,
    "5g_": MODULE_WIRELESS_5G,
    "dhcp_": MODULE_DHCP,
    "gsm_": MODULE_GSM,
    "sms_": MODULE_SMS,
    "device_": MODULE_DEVICES,
}


SENSOR_DESCRIPTIONS: Final = (
    # ----- INFO -----
    SensorEntityDescription(
        key=SENSOR_INFO_WORK_MODE,
        name="Work Mode",
        icon=ICON_INFO_WORK_MODE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_INFO_INTERFACE,
        name="Interface",
        icon=ICON_INFO_INTERFACE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # ----- SYSTEM -----
    SensorEntityDescription(
        key=SENSOR_SYSTEM_FIRMWARE_VERSION,
        name="Firmware Version",
        icon=ICON_FIRMWARE_VERSION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_SYSTEM_HARDWARE,
        name="Hardware",
        icon=ICON_HARDWARE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_SYSTEM_UPTIME,
        name="Connected Time",
        icon=ICON_SYSTEM_UPTIME,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # ----- MESH -----
    SensorEntityDescription(
        key=SENSOR_MESH_NETWORK,
        name="Mesh Network",
        icon=ICON_MESH_NETWORK,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_MESH_UNITS,
        name="Mesh Units",
        icon=ICON_MESH_UNITS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ----- WAN -----
    SensorEntityDescription(
        key=SENSOR_WAN_PUBLIC_IP,
        name="WAN Public IP Address",
        icon=ICON_WAN_PUBLIC_IP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_WAN_IP,
        name="WAN IP Address",
        icon=ICON_WAN_IP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_WAN_DNS,
        name="WAN DNS Address(es)",
        icon=ICON_WAN_DNS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_WAN_TYPE,
        name="Connection Type",
        icon=ICON_WAN_TYPE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_WAN_UPTIME,
        name="WAN Connected Time",
        icon=ICON_WAN_UPTIME,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # ----- LAN -----
    SensorEntityDescription(
        key=SENSOR_LAN_IP,
        name="LAN IP Address",
        icon=ICON_LAN_IP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_LAN_SUBNET,
        name="Subnet Mask",
        icon=ICON_LAN_SUBNET,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_LAN_MAC,
        name="MAC-Address",
        icon=ICON_LAN_MAC,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # ----- DEVICES COUNTS -----
    SensorEntityDescription(
        key=SENSOR_DEVICE_COUNT,
        name="Total Devices Connected",
        icon=ICON_DEVICE_COUNT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_WIFI_24_DEVICE_COUNT,
        name="2.4GHz WiFi Devices Connected",
        icon=ICON_WIFI_24_DEVICE_COUNT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_WIFI_5_DEVICE_COUNT,
        name="5GHz WiFi Devices Connected",
        icon=ICON_WIFI_5_DEVICE_COUNT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_WIRED_DEVICE_COUNT,
        name="Wired Devices Connected",
        icon=ICON_WIRED_DEVICE_COUNT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_MESH_DEVICE_COUNT,
        name="Mesh Devices Connected",
        icon=ICON_MESH_DEVICE_COUNT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def _resolve_coordinator(stored) -> P5Coordinator:
    # Accept direct coordinator
    if isinstance(stored, P5Coordinator):
        return stored
    # Common wrapper pattern
    if isinstance(stored, dict):
        if "coordinator" in stored:
            return stored["coordinator"]
        if "integration" in stored:
            return stored["integration"].coordinator
    # Attribute pattern
    if hasattr(stored, "coordinator"):
        return stored.coordinator
    # Test/loose fallback
    if hasattr(stored, "data"):
        return stored  # type: ignore[return-value]
    raise ValueError("Could not resolve P5Coordinator from hass.data")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = _resolve_coordinator(stored)

    entities = [
        BaseCudySensor(
            coordinator,
            entry,
            desc,
            module_map=P5_MODULE_MAP,
        )
        for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)