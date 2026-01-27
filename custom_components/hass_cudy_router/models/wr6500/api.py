from __future__ import annotations

import logging
from typing import Any, Dict

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.base_api import BaseApi

_LOGGER = logging.getLogger(__name__)


class WR6500Api(BaseApi):

    async def get_data(self) -> Dict[str, Dict[str, Any]]:
        system_raw = await self.fetch_text("/admin/system/status?detail=1")
        mesh_raw = await self.fetch_text("/admin/network/mesh/status?detail=1")
        lan_raw = await self.fetch_text("/admin/network/lan/status?detail=1")
        devices_raw = await self.fetch_text("/admin/network/devices/status?detail=1")
        wan_raw = await self.fetch_text("/admin/network/wan/status?detail=1")
        devices_list_raw = await self.fetch_text("/admin/network/devices/devlist?detail=1")

        system = self.parse_system_info(system_raw)
        mesh = self.parse_mesh_info(mesh_raw)
        lan = self.parse_lan_info(lan_raw)
        wan = self.parse_wan_info(wan_raw)
        devices = self.parse_devices(devices_raw)
        devices_parsed_list = self.parse_device_list(devices_list_raw)
        devices = dict(devices)  # copy
        devices[OPTIONS_DEVICE_LIST] = devices_parsed_list

        return {
            MODULE_SYSTEM: system,
            MODULE_MESH: mesh,
            MODULE_LAN: lan,
            MODULE_DEVICES: devices,
            MODULE_WAN: wan,
        }

    def parse_device_list(self, html: str) -> list[dict]:
        return self.parse_device_table(html)