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

from .coordinator import WR6500Coordinator
from ..base_sensor import async_setup_model_sensors

WR6500_MODULE_MAP: Final = {
    "info_": MODULE_INFO,
    "system_": MODULE_SYSTEM,
    "mesh_": MODULE_DEVICES,
    "lan_": MODULE_LAN,
    "wan_": MODULE_WAN,
    "24g_": MODULE_WIRELESS_24G,
    "5g_": MODULE_WIRELESS_5G,
    "dhcp_": MODULE_DHCP,
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
        icon=ICON_SYSTEM_FIRMWARE_VERSION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_SYSTEM_HARDWARE,
        name="Hardware",
        icon=ICON_SYSTEM_HARDWARE,
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
    # ----- WIFI 2.4G -----
    SensorEntityDescription(
        key=SENSOR_24G_WIFI_SSID,
        name="SSID",
        icon=ICON_24G_WIFI_SSID,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_24G_WIFI_BSSID,
        name="BSSID",
        icon=ICON_24G_WIFI_BSSID,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_24G_WIFI_ENCRYPTION,
        name="Encryption",
        icon=ICON_24G_WIFI_ENCRYPTION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_24G_WIFI_CHANNEL,
        name="Channel",
        icon=ICON_24G_WIFI_CHANNEL,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ----- WIFI 5G -----
    SensorEntityDescription(
        key=SENSOR_5G_WIFI_SSID,
        name="SSID",
        icon=ICON_5G_WIFI_SSID,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_5G_WIFI_BSSID,
        name="BSSID",
        icon=ICON_5G_WIFI_BSSID,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_5G_WIFI_ENCRYPTION,
        name="Encryption",
        icon=ICON_5G_WIFI_ENCRYPTION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_5G_WIFI_CHANNEL,
        name="Channel",
        icon=ICON_5G_WIFI_CHANNEL,
        state_class=SensorStateClass.MEASUREMENT,
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
        entity_category=EntityCategory.DIAGNOSTIC,
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
        entity_category=EntityCategory.DIAGNOSTIC,
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    await async_setup_model_sensors(
        hass,
        entry,
        async_add_entities,
        SENSOR_DESCRIPTIONS,
        module_map=WR6500_MODULE_MAP,
        coordinator_cls=WR6500Coordinator,
    )