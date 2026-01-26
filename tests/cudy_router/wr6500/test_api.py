from __future__ import annotations

from pathlib import Path

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.wr6500.api import WR6500Api

API = WR6500Api(client=None)


def _read_fixture(*candidates: str) -> str:
    base = Path(__file__).resolve().parents[1] / "html" / "wr6500"
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

    assert any(
        (
            data.get(SENSOR_FIRMWARE_VERSION),
            data.get(SENSOR_HARDWARE),
            data.get(SENSOR_SYSTEM_UPTIME),
        )
    )


def test_parse_mesh_from_fixture_html():
    html = _read_fixture("mesh.html")

    data = API.parse_mesh_info(html)

    assert SENSOR_MESH_UNITS in data
    assert SENSOR_MESH_NETWORK in data

    assert any(
        (
            data.get(SENSOR_MESH_UNITS),
            data.get(SENSOR_MESH_NETWORK)
        )
    )


def test_parse_lan_from_fixture_html():
    html = _read_fixture("lan.html")

    data = API.parse_lan_info(html)

    assert SENSOR_LAN_IP in data

    lan_ip = data.get(SENSOR_LAN_IP)
    if lan_ip:
        assert "." in lan_ip


def test_parse_wan_from_fixture_html():
    html = _read_fixture("wan.html")

    data = API.parse_wan_info(html)

    assert SENSOR_WAN_PUBLIC_IP in data
    assert SENSOR_WAN_IP in data
    assert SENSOR_WAN_DNS in data
    assert SENSOR_WAN_TYPE in data
    assert SENSOR_WAN_UPTIME in data

    wan_ip = data.get(SENSOR_WAN_PUBLIC_IP)
    if wan_ip:
        assert "." in wan_ip


def test_parse_devices_from_fixture_html():
    html = _read_fixture("devices.html")
    device_list = _read_fixture("device_list.html")

    data = API.parse_devices(html)
    data[OPTIONS_DEVICELIST] = API.parse_device_list(device_list)

    assert SENSOR_DEVICE_COUNT in data
    assert SENSOR_WIFI_24_DEVICE_COUNT in data
    assert SENSOR_WIFI_5_DEVICE_COUNT in data
    assert SENSOR_WIRED_DEVICE_COUNT in data
    assert SENSOR_MESH_DEVICE_COUNT in data
    assert isinstance(data[OPTIONS_DEVICELIST], list)

    for dev in data[OPTIONS_DEVICELIST]:
        assert DEVICE_HOSTNAME in dev
        assert DEVICE_IP in dev
        assert DEVICE_MAC in dev