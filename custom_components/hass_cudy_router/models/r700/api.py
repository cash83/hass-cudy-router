from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict

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


class R700Api:
    """R700 model-specific endpoints + parsing."""

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

        return {
            MODULE_SYSTEM: system,
            MODULE_DHCP: dhcp,
            MODULE_LAN: lan,
            MODULE_DEVICES: devices,
            MODULE_WAN: wan,
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

    def parse_system_info(self, input_html: str) -> dict[str, Any]:
        data = {
            SENSOR_FIRMWARE_VERSION: "Unknown",
            SENSOR_HARDWARE: "Unknown",
            SENSOR_SYSTEM_UPTIME: "Unknown",
            SENSOR_SYSTEM_LOCALTIME: "Unknown"
        }
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

    def parse_lan_info(self, input_html: str) -> dict[str, Any]:
        return self._parse_lines(
            input_html=input_html,
            keys={
                SENSOR_LAN_IP: "IP Address",
                SENSOR_LAN_SUBNET: "Subnet Mask",
                SENSOR_LAN_MAC: "MAC-Address",
            }
        )

    def parse_wan_info(self, input_html: str) -> dict[str, Any]:
        return self._parse_lines(
            input_html=input_html,
            keys={
                SENSOR_WAN_TYPE: "Protocol",
                SENSOR_WAN_IP: "IP Address",
                SENSOR_WAN_GATEWAY: "Gateway",
                SENSOR_WAN_UPTIME: "Connected Time",
                SENSOR_WAN_DNS: "DNS",
            }
        )

    def parse_dhcp_info(self, input_html: str) -> dict[str, Any]:
        return self._parse_lines(
            input_html=input_html,
            keys={
                SENSOR_DHCP_IP_START: "IP Start",
                SENSOR_DHCP_IP_END: "IP End",
                SENSOR_DHCP_DNS_PRIMARY: "Preferred DNS",
                SENSOR_DHCP_DNS_SECONDARY: "Alternate DNS",
                SENSOR_DHCP_GATEWAY: "Default Gateway",
                SENSOR_DHCP_LEASE_TIME: "Leasetime",
            }
        )

    def parse_devices(self, input_html: str) -> dict[str, Any]:
        data = self._parse_lines(
            input_html=input_html,
            keys={
                SENSOR_DEVICE_COUNT: "Devices",
                SENSOR_DEVICE_ONLINE: "Online",
                SENSOR_DEVICE_BLOCKED: "Blocked",
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

            # 1: hostname
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
            match = R700Api._get_info(unique_lines, label)
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