from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup

from custom_components.hass_cudy_router.const import *

_UP_RE = re.compile(r"↑\s*([\d.]+)\s*([A-Za-z/]+)")
_DOWN_RE = re.compile(r"↓\s*([\d.]+)\s*([A-Za-z/]+)")

LOGGER = logging.getLogger(__name__)

class BaseApi:

    def __init__(self, client: Any) -> None:
        self.client = client

    @staticmethod
    def _luci(path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"/cgi-bin/luci{path}"

    async def fetch_text(self, path: str) -> str:
        if self.client is None:
            return ""
        fetch = getattr(self.client, "get_text", None)
        if callable(fetch):
            return await fetch(self._luci(path))
        fetch2 = getattr(self.client, "get", None)
        if callable(fetch2):
            resp = await fetch2(self._luci(path))
            try:
                return await resp.text()
            except Exception:
                return str(resp)
        return ""

    def parse_basic_info(self, input_html: str) -> dict[str, Any]:
        return self.parse_kv_table(
            input_html,
            {
                SENSOR_INFO_INTERFACE: "Interface",
                SENSOR_INFO_WORK_MODE: "Work Mode",
            },
        )

    def parse_system_info(self, html: str) -> dict[str, Any]:
        data: dict[str, Any] = {
            SENSOR_SYSTEM_FIRMWARE_VERSION: "Firmware Version",
            SENSOR_SYSTEM_MODEL: "Model",
            SENSOR_SYSTEM_HARDWARE: "Hardware",
            SENSOR_SYSTEM_UPTIME: "System Uptime",
            SENSOR_SYSTEM_LOCALTIME: "Local Time",
        }
        if not html:
            return data

        data = self.parse_kv_table(
            html,
            {
                SENSOR_SYSTEM_FIRMWARE_VERSION: "Firmware Version",
                SENSOR_SYSTEM_MODEL: "Model",
                SENSOR_SYSTEM_HARDWARE: "Hardware",
                SENSOR_SYSTEM_UPTIME: "System Uptime",
                SENSOR_SYSTEM_LOCALTIME: "Local Time",
            },
        )

        lines = self._get_text_lines(html)

        uptime = self._get_info_from_lines(lines, "Uptime")
        if uptime:
            data[SENSOR_SYSTEM_UPTIME] = uptime

        local_time = (
                self._get_info_from_lines(lines, "Local Time")
                or self._get_info_from_lines(lines, "Local time")
        )
        if local_time:
            data[SENSOR_SYSTEM_LOCALTIME] = local_time

        return data

    def parse_mesh_info(self, html: str) -> Dict[str, Any]:
        mesh = self.parse_kv_table(
            html,
            {
                SENSOR_MESH_NETWORK: "Device Name",
                SENSOR_MESH_UNITS: "Mesh Units",
            },
        )
        mesh[SENSOR_MESH_UNITS] = self._to_int(mesh[SENSOR_MESH_UNITS])
        return mesh

    def parse_lan_info(self, input_html: str) -> dict[str, Any]:
        return self.parse_kv_table(
            input_html,
            {
                SENSOR_LAN_IP: "IP Address",
                SENSOR_LAN_SUBNET: "Subnet Mask",
                SENSOR_LAN_MAC: "MAC-Address",
            },
        )

    def parse_wan_info(self, html: str) -> Dict[str, Any]:
        return self.parse_kv_table(
            html,
            {
                SENSOR_WAN_TYPE: "Protocol",
                SENSOR_WAN_IP: "IP Address",
                SENSOR_WAN_UPTIME: "Connected Time",
                SENSOR_WAN_PUBLIC_IP: "Public IP",
                SENSOR_WAN_DNS: "DNS",
            },
        )

    def parse_wireless_24g_info(self, html: str) -> Dict[str, Any]:
        return self.parse_kv_table(
            html,
            {
                SENSOR_24G_WIFI_SSID: "SSID",
                SENSOR_24G_WIFI_BSSID: "BSSID",
                SENSOR_24G_WIFI_ENCRYPTION: "Encryption",
                SENSOR_24G_WIFI_CHANNEL: "Channel",
            },
        )

    def parse_wireless_5g_info(self, html: str) -> Dict[str, Any]:
        return self.parse_kv_table(
            html,
            {
                SENSOR_5G_WIFI_SSID: "SSID",
                SENSOR_5G_WIFI_BSSID: "BSSID",
                SENSOR_5G_WIFI_ENCRYPTION: "Encryption",
                SENSOR_5G_WIFI_CHANNEL: "Channel",
            },
        )

    def parse_dhcp_info(self, input_html: str) -> dict[str, Any]:
        return self.parse_kv_table(
            input_html,
            {
                SENSOR_DHCP_IP_START: "IP Start",
                SENSOR_DHCP_IP_END: "IP End",
                SENSOR_DHCP_DNS_PRIMARY: "Preferred DNS",
                SENSOR_DHCP_DNS_SECONDARY: "Alternate DNS",
                SENSOR_DHCP_GATEWAY: "Default Gateway",
                SENSOR_DHCP_LEASE_TIME: "Leasetime",
            },
        )

    def parse_gsm_info(self, html: str) -> Dict[str, Any]:
        data = self.parse_kv_table(
            html,
            {
                SENSOR_GSM_NETWORK_TYPE: "Network Type",
                SENSOR_GSM_DOWNLOAD: "Download",
                SENSOR_GSM_UPLOAD: "Upload",
                SENSOR_GSM_PUBLIC_IP: "Public IP",
                SENSOR_GSM_IP_ADDRESS: "IP Address",
                SENSOR_GSM_CONNECTED_TIME: "Connected Time",
            },
        )
        upload_download = data[SENSOR_GSM_UPLOAD].split("/")
        data[SENSOR_GSM_UPLOAD] = upload_download[0].strip()
        data[SENSOR_GSM_DOWNLOAD] = upload_download[1].strip()
        return data

    def parse_sms_info(self, html: str) -> Dict[str, Any]:
        sms = self.parse_kv_table(
            html,
            {
                SENSOR_SMS_INBOX: "Inbox",
                SENSOR_SMS_OUTBOX: "Outbox",
            },
        )
        sms[SENSOR_SMS_INBOX] = self._to_int(sms[SENSOR_SMS_INBOX])
        sms[SENSOR_SMS_OUTBOX] = self._to_int(sms[SENSOR_SMS_OUTBOX])
        return sms

    def parse_devices(self, html: str) -> Dict[str, Any]:
        devices = self.parse_kv_table(
            html,
            {
                SENSOR_DEVICE_COUNT: "Devices",
                SENSOR_WIFI_24_DEVICE_COUNT: "2.4G WiFi",
                SENSOR_WIFI_5_DEVICE_COUNT: "5G WiFi",
                SENSOR_WIRED_DEVICE_COUNT: "Wired",
                SENSOR_MESH_DEVICE_COUNT: "Mesh",
            },
        )
        for k in (
                SENSOR_DEVICE_COUNT,
                SENSOR_WIFI_24_DEVICE_COUNT,
                SENSOR_WIFI_5_DEVICE_COUNT,
                SENSOR_WIRED_DEVICE_COUNT,
                SENSOR_MESH_DEVICE_COUNT,
        ):
            if k in devices:
                iv = self._to_int(devices.get(k))
                if iv is not None:
                    devices[k] = iv

        return devices

    def parse_device_list(self, html: str) -> list[dict]:
        return self.parse_device_table(html)

    async def reboot(self):
        try:
            await self._client.post(
                self._luci("/admin/system/reboot"),
                data={"reboot": "1"},  # harmless if router ignores it
            )
        except Exception as exc:
            LOGGER.warning("Reboot request failed: %s", exc)

    @staticmethod
    def _normalize_spaces(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _get_text_lines(html: str) -> List[str]:
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n")
        lines = [BaseApi._normalize_spaces(l) for l in text.splitlines() if BaseApi._normalize_spaces(l)]
        return list(dict.fromkeys(lines))

    @staticmethod
    def _get_info_from_lines(lines: Iterable[str], label: str) -> Optional[str]:
        needle = label.strip().lower()
        lines_list = list(lines)
        for idx, line in enumerate(lines_list):
            l = line.strip().lower()
            if l == needle or l.startswith(needle):
                if idx + 1 < len(lines_list):
                    return lines_list[idx + 1]
                return None
        return None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        s = str(value).strip()
        if not s or s.upper() == "N/A":
            return None
        m = re.search(r"\d+", s)
        return int(m.group(0)) if m else None

    @staticmethod
    def parse_kv_table(html: str, mapping: Dict[str, str]) -> Dict[str, Any]:
        lines = BaseApi._get_text_lines(html)
        out: Dict[str, Any] = {}
        for out_key, label in mapping.items():
            v = BaseApi._get_info_from_lines(lines, label)
            if v is not None:
                out[out_key] = v
            else:
                out[out_key] = "n/a"
        return out

    @staticmethod
    def parse_device_table(
            html: str,
            *,
            row_selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        if row_selector:
            rows = soup.select(row_selector)
        else:
            rows = soup.select("table tbody tr[id^='cbi-table-']") or soup.select("table tbody tr") or []

        parsed: List[Dict[str, Any]] = []
        for tr in rows:
            cols = tr.find_all(["td", "th"])
            cell_texts = [BaseApi._normalize_spaces(td.get_text(" ")) for td in cols]

            mac = None
            ip = None
            hostname = None
            signal = None
            uptime = None
            conn_type = None
            upload = None
            download = None

            for text in cell_texts:
                tokens = [t for t in re.split(r"[,\s/|]+", text) if t]
                for tok in tokens:
                    if re.match(r"^[0-9A-Fa-f]{2}([:\-][0-9A-Fa-f]{2}){5}$", tok):
                        mac = tok
                    elif re.match(r"^\d{1,3}(\.\d{1,3}){3}$", tok):
                        ip = tok
            if cell_texts:
                hostname = cell_texts[0].splitlines()[0] if cell_texts[0] else None
                if len(cell_texts) > 1 and not mac:
                    tokens = [t for t in re.split(r"[,\s/|]+", cell_texts[1]) if t]
                    for tok in tokens:
                        if re.match(r"^[0-9A-Fa-f]{2}([:\-][0-9A-Fa-f]{2}){5}$", tok):
                            mac = tok
                        elif re.match(r"^\d{1,3}(\.\d{1,3}){3}$", tok):
                            ip = tok

            for text in cell_texts:
                m = re.search(r"(-\d{1,3})\s*dBm", text)
                if m:
                    signal = m.group(1)
                if signal is None:
                    m2 = re.search(r"\s(-\d{1,3}|---)\s", f" {text} ")
                    if m2:
                        signal = m2.group(1)

            for text in cell_texts:
                up = _UP_RE.search(text)
                down = _DOWN_RE.search(text)
                if up:
                    upload = f"{up.group(1)}{up.group(2)}"
                if down:
                    download = f"{down.group(1)}{down.group(2)}"

            for text in cell_texts:
                m = re.search(r"(\d+d\s*)?\d{1,2}:\d{2}:\d{2}", text)
                if m:
                    uptime = m.group(0)
                    break

            # connection type heuristic: look for keywords
            joined = " ".join(cell_texts).lower()
            if "wifi" in joined:
                conn_type = "wifi"
            elif "mesh" in joined:
                conn_type = "mesh"
            elif "lan" in joined or "ethernet" in joined or "wired" in joined:
                conn_type = "wired"

            parsed.append(
                {
                    DEVICE_HOSTNAME: hostname or "n/a",
                    DEVICE_IP: ip or "n/a",
                    DEVICE_MAC: mac or "n/a",
                    DEVICE_UPLOAD_SPEED: upload or "n/a",
                    DEVICE_DOWNLOAD_SPEED: download or "n/a",
                    DEVICE_SIGNAL: signal or "n/a",
                    DEVICE_ONLINE_TIME: uptime or "n/a",
                    DEVICE_CONNECTION_TYPE: conn_type or "n/a",
                }
            )

        return parsed
