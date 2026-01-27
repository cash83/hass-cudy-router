from pathlib import Path

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.base_api import BaseApi


def read_fixture(*candidates: str, model: str) -> str:
    base = Path(__file__).resolve().parents[0] / "html" / model
    for name in candidates:
        p = base / name
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")

    for p in sorted(base.glob("*system*.html")):
        return p.read_text(encoding="utf-8", errors="ignore")

    raise FileNotFoundError(f"No {model} system HTML fixture found in {base}")


def api_basic_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_basic_info(html), values=values)

def api_system_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_system_info(html), values=values)


def api_mesh_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_mesh_info(html), values=values)


def api_lan_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_lan_info(html), values=values)


def api_wan_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_wan_info(html), values=values)


def api_24g_wifi_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_wireless_24g_info(html), values=values)


def api_5g_wifi_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_wireless_5g_info(html), values=values)


def api_dhcp_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_dhcp_info(html), values=values)


def api_gsm_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_gsm_info(html), values=values)


def api_sms_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_sms_info(html), values=values)

def api_devices_info(api: BaseApi, html: str, values: dict):
    keys_and_values(api.parse_devices(html), values=values)

def api_device_list(html: str, items: int):
    data = BaseApi.parse_device_table(html)
    for device in data:
        keys_in_collection(device, [
            DEVICE_HOSTNAME,
            DEVICE_IP,
            DEVICE_MAC,
            DEVICE_UPLOAD_SPEED,
            DEVICE_DOWNLOAD_SPEED,
            DEVICE_SIGNAL,
            DEVICE_ONLINE_TIME,
            DEVICE_CONNECTION_TYPE
        ])
    assert len(data) == items


def keys_and_values(data: dict, values: dict):
    keys_in_collection(data, list(values.keys()))
    for key, value in values.items():
        assert data[key] == value


def keys_in_collection(data: dict, keys: list):
    for key in keys:
        assert key in data
