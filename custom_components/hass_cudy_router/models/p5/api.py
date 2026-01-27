from __future__ import annotations

import logging
from typing import Any, Dict

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.basic_api import BasicHtmlApi

_LOGGER = logging.getLogger(__name__)


class P5Api(BasicHtmlApi):

    def __init__(self, client: Any) -> None:
        self.client = client

    async def get_data(self) -> Dict[str, Dict[str, Any]]:
        info_raw = await self._fetch_text("/admin/system/wizard")
        system_raw = await self._fetch_text("/admin/system/status?detail=1")
        mesh_raw = await self._fetch_text("/admin/network/mesh/status?detail=1")
        lan_raw = await self._fetch_text("/admin/network/lan/status?detail=1")
        wifi_24g_raw = await self._fetch_text("/admin/network/wireless/status?detail=1&iface=wlan00")
        wifi_5g_raw = await self._fetch_text("/admin/network/wireless/status?detail=1&iface=wlan10")
        dhcp_raw = await self._fetch_text("/admin/services/dhcp/status")
        gsm_raw = await self._fetch_text("/admin/network/gcom/status")
        sms_raw = await self._fetch_text("/admin/network/gcom/sms/status")
        devices_raw = await self._fetch_text("/admin/network/devices/status?detail=1")
        devices_list_raw = await self._fetch_text("/admin/network/devices/devlist?detail=1")

        info = self.parse_basic_info(info_raw)
        system = self.parse_system_info(system_raw)
        mesh = self.parse_mesh_info(mesh_raw)
        lan = self.parse_lan_info(lan_raw)
        wifi_24g = self.parse_wireless_24g_info(wifi_24g_raw)
        wifi_5g = self.parse_wireless_5g_info(wifi_5g_raw)
        dhcp = self.parse_dhcp_info(dhcp_raw)
        gsm = self.parse_gsm_info(gsm_raw)
        sms = self.parse_sms_info(sms_raw)
        devices = self.parse_devices(devices_raw)
        devices_parsed_list = self.parse_device_list(devices_list_raw)
        devices = dict(devices)
        devices[OPTIONS_DEVICE_LIST] = devices_parsed_list

        return {
            MODULE_INFO: info,
            MODULE_SYSTEM: system,
            MODULE_MESH: mesh,
            MODULE_LAN: lan,
            MODULE_WIRELESS_24G: wifi_24g,
            MODULE_WIRELESS_5G: wifi_5g,
            MODULE_DHCP: dhcp,
            MODULE_GSM: gsm,
            MODULE_SMS: sms,
            MODULE_DEVICES: devices,
        }