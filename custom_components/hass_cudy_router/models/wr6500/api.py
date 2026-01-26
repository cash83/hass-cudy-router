from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from custom_components.hass_cudy_router.const import *

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


class WR6500Api:
    """WR6500 model-specific endpoints + parsing."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def get_data(self) -> Dict[str, Dict[str, Any]]:
        """Return parsed data for system/lan/devices/wan."""
        system_raw = await self._fetch_system()
        mesh_raw = await self._fetch_mesh()
        lan_raw = await self._fetch_lan()
        devices_raw = await self._fetch_devices()
        wan_raw = await self._fetch_wan()
        devices_list_raw = await self._fetch_devices_list()

        system = self.parse_system_info(system_raw)
        mesh = self.parse_mesh_info(mesh_raw)
        lan = self.parse_lan_info(lan_raw)
        wan = self.parse_wan_info(wan_raw)
        devices = self.parse_devices(devices_raw)
        devices[OPTIONS_DEVICELIST] = self.parse_device_list(devices_list_raw)

        return {
            MODULE_SYSTEM: system,
            MODULE_MESH: mesh,
            MODULE_LAN: lan,
            MODULE_DEVICES: devices,
            MODULE_WAN: wan,                          # NEW: include WAN module
        }

    # ------------------------------------------------------------------
    # Fetchers
    # ------------------------------------------------------------------
    @staticmethod
    def _luci(path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"/cgi-bin/luci{path}"

    async def _fetch_system(self) -> Any:
        return await self._client.get(self._luci("/admin/system/status?detail=1"))

    async def _fetch_mesh(self) -> Any:
        return await self._client.get(self._luci("/admin/network/mesh/status?detail=1"))

    async def _fetch_lan(self) -> Any:
        return await self._client.get(self._luci("/admin/network/lan/status?detail=1"))

    async def _fetch_devices(self) -> Any:
        return await self._client.get(self._luci("/admin/network/devices/status?detail=1"))

    async def _fetch_wan(self) -> Any:
        return await self._client.get(self._luci("/admin/network/wan/status?detail=1"))

    async def _fetch_devices_list(self) -> Any:
        return await self._client.get(self._luci("/admin/network/devices/devlist?detail=1"))

    def parse_system_info(self, input_html: str) -> dict[str, Any]:
        data = {SENSOR_FIRMWARE_VERSION: "Unknown", SENSOR_HARDWARE: "Unknown", SENSOR_SYSTEM_UPTIME: "Unknown"}
        if not input_html: return data

        soup = BeautifulSoup(input_html, "html.parser")
        text = soup.get_text()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        unique_lines = list(dict.fromkeys(lines))
        hw_match = self._get_info(unique_lines, "Hardware")
        if hw_match:
            data[SENSOR_HARDWARE] = hw_match

        fw_match = re.search(r"Firmware Version\s*([^\s|]+)", text)
        if fw_match:
            data[SENSOR_FIRMWARE_VERSION] = fw_match.group(1).strip()

        ut_match = self._get_info(unique_lines, "Uptime")
        if ut_match:
            data[SENSOR_SYSTEM_UPTIME] = ut_match

        return data

    def parse_mesh_info(self, input_html: str) -> dict[str, Any]:
        return self._parse_lines(
            input_html=input_html,
            keys={
                SENSOR_MESH_NETWORK: "Device Name",
                SENSOR_MESH_UNITS: "Mesh Units",
            }
        )

    def parse_lan_info(self, input_html: str) -> dict[str, Any]:
        return self._parse_lines(
            input_html=input_html,
            keys={
                SENSOR_LAN_IP: "IP Address"
            }
        )

    def parse_wan_info(self, input_html: str) -> dict[str, Any]:
        return self._parse_lines(
            input_html=input_html,
            keys={
                SENSOR_WAN_TYPE: "Protocol",
                SENSOR_WAN_IP: "IP Address",
                SENSOR_WAN_UPTIME: "Connected Time",
                SENSOR_WAN_PUBLIC_IP: "Public IP",
                SENSOR_WAN_DNS: "DNS",
            }
        )

    def parse_devices(self, input_html: str) -> dict[str, Any]:
        data = self._parse_lines(
            input_html=input_html,
            keys={
                SENSOR_DEVICE_COUNT: "Devices",
                SENSOR_WIFI_24_DEVICE_COUNT: "2.4G WiFi",
                SENSOR_WIFI_5_DEVICE_COUNT: "5G WiFi",
                SENSOR_WIRED_DEVICE_COUNT: "Wired",
                SENSOR_MESH_DEVICE_COUNT: "Mesh",
            }
        )
        soup = BeautifulSoup(input_html, "html.parser")
        text = soup.get_text()
        dc_match = re.search(r"Devices\s*([^\s|]+)", text)
        if dc_match:
            data[SENSOR_DEVICE_COUNT] = dc_match.group(1).strip()
        return data

    @staticmethod
    def parse_device_list(input_html: str) -> list[dict]:
        data = []
        soup = BeautifulSoup(input_html, "html.parser")
        table = soup.find("table", class_="table table-striped")
        if not table:
            return data

        # All rows with ids like "cbi-table-1", "cbi-table-2", ...
        for row in table.select("tbody tr[id^='cbi-table-']"):
            cols = row.find_all("td")

            # 0: index (No.)
            idx_cell = cols[0]
            idx = idx_cell.get_text(strip=True)

            # 1: hostname + connection type (Mesh / 2.4G WiFi / etc.)
            hostname_cell = cols[1]
            # take only the "desktop" version (hidden-xs) to avoid duplicates
            host_p = hostname_cell.find("p", class_="form-control-static hidden-xs")
            hostname = None
            conn_type = None
            if host_p:
                parts = [t.strip() for t in host_p.stripped_strings]
                if parts:
                    hostname = parts[0]
                if len(parts) > 1:
                    conn_type = parts[1]

            # 4: IP / MAC address
            ipmac_cell = cols[4]
            ipmac_p = ipmac_cell.find("p", class_="form-control-static hidden-xs")
            ip = mac = None
            if ipmac_p:
                ipmac_parts = [t.strip() for t in ipmac_p.stripped_strings]
                if ipmac_parts:
                    ip = ipmac_parts[0]
                if len(ipmac_parts) > 1:
                    mac = ipmac_parts[1]

            # 5 Upload/Download
            speed_p = cols[5].find("p", class_="form-control-static hidden-xs")
            upload = download = None
            upload_unit = download_unit = None
            if speed_p:
                speed_text = speed_p.get_text(" ")
                # Example: "0.00 Kbps 0.00 Kbps" but with arrows in between depending on parsing
                up_m = _UP_RE.search(speed_text)
                down_m = _DOWN_RE.search(speed_text)
                if up_m:
                    upload = float(up_m.group(1))
                    upload_unit = up_m.group(2)
                if down_m:
                    download = float(down_m.group(1))
                    download_unit = down_m.group(2)

            # 6: Signal
            signal_cell = cols[6]
            signal_p = signal_cell.find("p", class_="form-control-static hidden-xs")
            signal = signal_p.get_text(strip=True) if signal_p else None

            # 7: Duration / online
            online_cell = cols[7]
            online_p = online_cell.find("p", class_="form-control-static hidden-xs")
            online = online_p.get_text(strip=True) if online_p else None

            # 8: Internet toggle (fa-toggle-on / fa-toggle-off)
            internet_cell = cols[8]
            toggle_icon = internet_cell.find("i", class_=["fa-toggle-on", "fa-toggle-off"])
            internet_enabled = None
            if toggle_icon:
                internet_enabled = "fa-toggle-on" in toggle_icon.get("class", [])

            data.append(
                {
                    DEVICE_HOSTNAME: hostname,
                    DEVICE_IP: ip,
                    DEVICE_MAC: mac,
                    DEVICE_UPLOAD_SPEED: upload + upload_unit if upload is not None else "0.00Kbps",
                    DEVICE_DOWNLOAD_SPEED: download + download_unit if download is not None else "0.00Kbps",
                    DEVICE_SIGNAL: signal,
                    DEVICE_ONLINE_TIME: online,
                    DEVICE_CONNECTION: internet_enabled,
                    DEVICE_CONNECTION_TYPE: conn_type,
                }
            )

        return data

    @staticmethod
    def _parse_lines(
            input_html: str,
        keys: dict[str, str]
    ) -> dict[str, Any]:
        if not input_html:
            return {}

        result = {}
        for output_key, label in keys.items():
            result[output_key] = "N/A"

        soup = BeautifulSoup(input_html, "html.parser")
        text = soup.get_text()

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        unique_lines = list(dict.fromkeys(lines))

        for output_key, label in keys.items():
            match = WR6500Api._get_info(unique_lines, label)
            if match is not None:
                result[output_key] = match

        return result

    @staticmethod
    def _get_info(lines: list[str], key: str) -> str | None:
        try:
            idx = lines.index(key)
            return lines[idx + 1]
        except (ValueError, IndexError):
            return None