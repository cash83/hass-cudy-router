from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.base_api import BaseApi


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


class GenericApi(BaseApi):

    async def get_data(self) -> Dict[str, Dict[str, Any]]:
        system_raw = await self._fetch_system()
        lan_raw = await self._fetch_lan()
        devices_raw = await self._fetch_devices()
        dhcp_raw = await self._fetch_dhcp()
        devices_list_raw = await self._fetch_devices_list()

        system = self.parse_system_info(system_raw)
        lan = self.parse_lan_info(lan_raw)
        dhcp = self.parse_dhcp_info(dhcp_raw)
        devices = self.parse_devices(devices_raw)
        devices[OPTIONS_DEVICE_LIST] = self.parse_device_list(devices_list_raw)
        devices = dict(devices)

        return {
            MODULE_SYSTEM: system,
            MODULE_DHCP: dhcp,
            MODULE_LAN: lan,
            MODULE_DEVICES: devices
        }

    async def _fetch_system(self) -> Any:
        return await self.fetch_text(self._luci("/admin/system/status?detail=1"))

    async def _fetch_lan(self) -> Any:
        return await self.fetch_text(self._luci("/admin/network/lan/status?detail=1"))

    async def _fetch_dhcp(self) -> Any:
        return await self.fetch_text(self._luci("/admin/services/dhcp/status"))

    async def _fetch_devices(self) -> Any:
        return await self.fetch_text(self._luci("/admin/network/devices/status?detail=1"))

    async def _fetch_devices_list(self) -> Any:
        return await self.fetch_text(self._luci("/admin/network/devices/devlist?detail=1"))