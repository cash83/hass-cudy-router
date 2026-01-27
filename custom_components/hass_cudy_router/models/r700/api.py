from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.basic_api import BasicHtmlApi

_LOGGER = logging.getLogger(__name__)

_UP_RE = re.compile(r"↑\s*([\d.]+)\s*([A-Za-z/]+)")
_DOWN_RE = re.compile(r"↓\s*([\d.]+)\s*([A-Za-z/]+)")


@dataclass(frozen=True)
class Device:
    hostname: str
    ip: str
    mac: str
    upload_speed: str
    download_speed: str
    signal: str
    online_time: str
    connection: bool
    connection_type: str


class R700Api(BasicHtmlApi):

    def __init__(self, client: Any) -> None:
        self._client = client

    async def get_data(self) -> Dict[str, Dict[str, Any]]:
        system_raw = await self._fetch_system()
        lan_raw = await self._fetch_lan()
        devices_raw = await self._fetch_devices()
        wan_raw = await self._fetch_wan()
        dhcp_raw = await self._fetch_dhcp()
        devices_list_raw = await self._fetch_devices_list()

        system = self.parse_system_info(system_raw)
        lan = self.parse_lan_info(lan_raw)
        wan = self.parse_wan_info(wan_raw)
        dhcp = self.parse_dhcp_info(dhcp_raw)
        devices = self.parse_devices(devices_raw)
        devices[OPTIONS_DEVICE_LIST] = self.parse_device_list(devices_list_raw)
        devices = dict(devices)

        return {
            MODULE_SYSTEM: system,
            MODULE_DHCP: dhcp,
            MODULE_LAN: lan,
            MODULE_DEVICES: devices,
            MODULE_WAN: wan,
        }

    async def _fetch_system(self) -> Any:
        return await self._client.get(self._luci("/admin/system/status?detail=1"))

    async def _fetch_lan(self) -> Any:
        return await self._client.get(self._luci("/admin/network/lan/status?detail=1"))

    async def _fetch_wan(self) -> Any:
        return await self._client.get(self._luci("/admin/network/wan/status?detail=1"))

    async def _fetch_dhcp(self) -> Any:
        return await self._client.get(self._luci("/admin/services/dhcp/status"))

    async def _fetch_devices(self) -> Any:
        return await self._client.get(self._luci("/admin/network/devices/status?detail=1"))

    async def _fetch_devices_list(self) -> Any:
        return await self._client.get(self._luci("/admin/network/devices/devlist?detail=1"))

    def parse_devices(self, html: str) -> dict[str, Any]:
        data = self.parse_kv_table(
            html,
            {
                SENSOR_DEVICE_COUNT: "Devices",
                SENSOR_DEVICE_ONLINE: "Online",
                SENSOR_DEVICE_BLOCKED: "Blocked",
            },
        )

        if html:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()
            dc_match = re.search(r"Devices\s*([^\s|]+)", text)
            if dc_match:
                data[SENSOR_DEVICE_COUNT] = self._to_int(dc_match.group(1).strip())

        for k in (SENSOR_DEVICE_ONLINE, SENSOR_DEVICE_BLOCKED):
            if k in data:
                iv = self._to_int(data.get(k))
                if iv is not None:
                    data[k] = iv
        return data