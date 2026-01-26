from __future__ import annotations

from typing import Final

from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.hass_cudy_router.const import *

from .coordinator import R700Coordinator
from ..base_sensor import BaseCudySensor

R700_MODULE_MAP: Final = {
    "system_": MODULE_SYSTEM,
    "dhcp_": MODULE_DHCP,
    "wan_": MODULE_WAN,
    "lan_": MODULE_LAN,
    "device_": MODULE_DEVICES,
}


SENSOR_DESCRIPTIONS: Final = (
    SensorEntityDescription(
        key=SENSOR_FIRMWARE_VERSION,
        name="Firmware Version",
        icon=ICON_FIRMWARE_VERSION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_HARDWARE,
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
    SensorEntityDescription(
        key=SENSOR_SYSTEM_LOCALTIME,
        name="Local Time",
        icon=ICON_SYSTEM_LOCALTIME,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # ----- DHCP -----
    SensorEntityDescription(
        key=SENSOR_DHCP_IP_START,
        name="IP Start",
        icon=ICON_DHCP_IP_START,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_DHCP_IP_END,
        name="IP End",
        icon=ICON_DHCP_IP_END,
        state_class=SensorStateClass.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_DHCP_DNS_PRIMARY,
        name="Preferred DNS",
        icon=ICON_DHCP_DNS_PRIMARY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_DHCP_DNS_SECONDARY,
        name="Alternate DNS",
        icon=ICON_DHCP_DNS_SECONDARY,
        state_class=SensorStateClass.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_DHCP_GATEWAY,
        name="Default Gateway",
        icon=ICON_DHCP_GATEWAY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_DHCP_LEASE_TIME,
        name="Leasetime",
        icon=ICON_DHCP_LEASE_TIME,
        state_class=SensorStateClass.DIAGNOSTIC,
    ),
    # ----- WAN -----
    SensorEntityDescription(
        key=SENSOR_WAN_PUBLIC_IP,
        name="WAN Public IP Address",
        icon="mdi:earth",
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
        key=SENSOR_DEVICE_ONLINE,
        name="Online Devices",
        icon=ICON_DEVICE_ONLINE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_DEVICE_BLOCKED,
        name="Blocked Devices",
        icon=ICON_DEVICE_BLOCKED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def _resolve_coordinator(stored) -> R700Coordinator:
    if isinstance(stored, R700Coordinator):
        return stored
    if isinstance(stored, dict):
        if "coordinator" in stored:
            return stored["coordinator"]
        if "integration" in stored:
            return stored["integration"].coordinator
    if hasattr(stored, "coordinator"):
        return stored.coordinator
    if hasattr(stored, "data"):
        return stored
    raise ValueError("Could not resolve R700Coordinator")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = _resolve_coordinator(hass.data[DOMAIN][entry.entry_id])

    async_add_entities(
        BaseCudySensor(
            coordinator,
            entry,
            desc,
            module_map=R700_MODULE_MAP,
        )
        for desc in SENSOR_DESCRIPTIONS
    )