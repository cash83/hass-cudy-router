from __future__ import annotations

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.wr6500.api import WR6500Api
from tests.cudy_router.basic_api_test import read_fixture, api_wan_info, api_basic_info, api_system_info, api_mesh_info, \
    api_lan_info, api_dhcp_info, api_devices_info, api_device_list

API = WR6500Api(client=None)

def test_wr6500_parse_info():
    html = read_fixture("info.html", model="wr6500")
    expected = {
        SENSOR_INFO_WORK_MODE: "Wireless Router",
        SENSOR_INFO_INTERFACE: "WAN",
    }
    api_basic_info(API, html, expected)


def test_wr6500_parse_system():
    html = read_fixture("system.html", model="wr6500")
    expected = {
        SENSOR_SYSTEM_FIRMWARE_VERSION: "2.3.15-20250805-113843",
        SENSOR_SYSTEM_MODEL: "WR6500",
        SENSOR_SYSTEM_HARDWARE: "WR6500 V1.0",
        SENSOR_SYSTEM_UPTIME: "08:09:48",
        SENSOR_SYSTEM_LOCALTIME: "2026-01-21 12:10:10",
    }
    api_system_info(API, html, expected)


def test_wr6500_parse_mesh():
    html = read_fixture("mesh.html", model="wr6500")
    expected = {
        SENSOR_MESH_NETWORK: "Mesh_5456",
        SENSOR_MESH_UNITS: 2
    }

    api_mesh_info(API, html, expected)


def test_wr6500_parse_lan():
    html = read_fixture("lan.html", model="wr6500")
    expected = {
        SENSOR_LAN_IP: "192.168.2.1",
        SENSOR_LAN_SUBNET: "255.255.255.0",
        SENSOR_LAN_MAC: "80:AF:CA:0E:54:56",
    }

    api_lan_info(API, html, expected)


def test_wr6500_parse_wan():
    html = read_fixture("wan.html", model="wr6500")
    expected = {
        SENSOR_WAN_IP: "192.168.10.150",
        SENSOR_WAN_PUBLIC_IP: "83.238.165.41 *",
        SENSOR_WAN_DNS: "8.8.8.8/62.233.233.233",
        SENSOR_WAN_TYPE: "DHCP client",
        SENSOR_WAN_UPTIME: "08:26:31",
    }

    api_wan_info(API, html, expected)


def test_wr6500_parse_dhcp():
    html = read_fixture("dhcp.html", model="wr6500")
    expected = {
        SENSOR_DHCP_IP_START: "192.168.2.10",
        SENSOR_DHCP_IP_END: "192.168.2.250",
        SENSOR_DHCP_DNS_PRIMARY: "192.168.2.191",
        SENSOR_DHCP_DNS_SECONDARY: "8.8.8.8",
        SENSOR_DHCP_GATEWAY: "192.168.2.1",
        SENSOR_DHCP_LEASE_TIME: "120 Mins",
    }

    api_dhcp_info(API, html, expected)

def test_wr6500_parse_devices():
    html = read_fixture("devices.html", model="wr6500")
    expected = {
        SENSOR_DEVICE_COUNT: 30,
        SENSOR_WIFI_24_DEVICE_COUNT: 4,
        SENSOR_WIFI_5_DEVICE_COUNT: 2,
        SENSOR_WIRED_DEVICE_COUNT: 5,
        SENSOR_MESH_DEVICE_COUNT: 19,
    }

    api_devices_info(API, html, expected)

def test_wr6500_device_list():
    html = read_fixture("device_list.html", model="wr6500")
    api_device_list(html, 31)