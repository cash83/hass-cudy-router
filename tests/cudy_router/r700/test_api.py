from __future__ import annotations

from pathlib import Path

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.r700.api import R700Api

API = R700Api(client=None)


def _read_fixture(*candidates: str) -> str:
    base = Path(__file__).resolve().parents[1] / "html" / "r700"
    for name in candidates:
        p = base / name
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")

    for p in sorted(base.glob("*system*.html")):
        return p.read_text(encoding="utf-8", errors="ignore")

    raise FileNotFoundError(f"No WR6500 system HTML fixture found in {base}")


def test_parse_system_from_fixture_html():
    html = _read_fixture("system.html")

    data = API.parse_system_info(html)

    assert SENSOR_FIRMWARE_VERSION in data
    assert SENSOR_HARDWARE in data
    assert SENSOR_SYSTEM_UPTIME in data
    assert SENSOR_SYSTEM_LOCALTIME in data

    assert any(
        (
            data.get(SENSOR_FIRMWARE_VERSION),
            data.get(SENSOR_HARDWARE),
            data.get(SENSOR_SYSTEM_UPTIME),
            data.get(SENSOR_SYSTEM_LOCALTIME),
        )
    )


def test_parse_dhcp_from_fixture_html():
    html = _read_fixture("dhcp.html")

    data = API.parse_dhcp_info(html)

    assert SENSOR_DHCP_IP_START in data
    assert SENSOR_DHCP_IP_END in data
    assert SENSOR_DHCP_GATEWAY in data
    assert SENSOR_DHCP_DNS_PRIMARY in data
    assert SENSOR_DHCP_DNS_SECONDARY in data
    assert SENSOR_DHCP_LEASE_TIME in data

    ip_start = data.get(SENSOR_DHCP_IP_START)
    assert "." in ip_start
    gateway = data.get(SENSOR_DHCP_GATEWAY)
    assert gateway == "192.168.10.1"
    lease_time = data.get(SENSOR_DHCP_LEASE_TIME)
    assert lease_time == "12 Hours"


def test_parse_lan_from_fixture_html():
    html = _read_fixture("lan.html")

    data = API.parse_lan_info(html)

    assert SENSOR_LAN_IP in data
    assert SENSOR_LAN_SUBNET in data
    assert SENSOR_LAN_MAC in data

    lan_ip = data.get(SENSOR_LAN_IP)
    if lan_ip:
        assert "." in lan_ip


def test_parse_wan_from_fixture_html():
    html = _read_fixture("wan.html")

    data = API.parse_wan_info(html)

    assert SENSOR_WAN_IP in data
    assert SENSOR_WAN_DNS in data
    assert SENSOR_WAN_TYPE in data
    assert SENSOR_WAN_UPTIME in data

    wan_ip = data.get(SENSOR_WAN_IP)
    if wan_ip:
        assert "." in wan_ip


def test_parse_devices_from_fixture_html():
    html = _read_fixture("devices.html")
    device_list = _read_fixture("device_list.html")

    data = API.parse_devices(html)
    data[OPTIONS_DEVICE_LIST] = API.parse_device_list(device_list)

    assert SENSOR_DEVICE_COUNT in data
    assert SENSOR_DEVICE_ONLINE in data
    assert SENSOR_DEVICE_BLOCKED in data


def test_parse_device_list_from_fixture_html():
    html = _read_fixture("device_list.html")
    data = API.parse_device_list(html)

    for dev in data:
        assert DEVICE_HOSTNAME in dev
        assert DEVICE_IP in dev
        assert DEVICE_MAC in dev