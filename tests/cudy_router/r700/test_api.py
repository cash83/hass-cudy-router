from __future__ import annotations

from pathlib import Path

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.r700.api import R700Api
from tests.cudy_router.basic_api_test import read_fixture, api_device_list, api_basic_info, api_system_info, \
    api_dhcp_info, api_lan_info, api_devices_info, api_wan_info

API = R700Api(client=None)


def test_r700_parse_system():
    html = read_fixture("system.html", model="r700")
    expected = {
        SENSOR_SYSTEM_FIRMWARE_VERSION: "1.15.5-20230420-155410",
        SENSOR_SYSTEM_HARDWARE: "R700 V1.0",
        SENSOR_SYSTEM_UPTIME: "23 Day 03:53:02",
        SENSOR_SYSTEM_LOCALTIME: "2026-01-26 16:23:57",
    }
    api_system_info(API, html, expected)


def test_r700_parse_lan():
    html = read_fixture("lan.html", model="r700")
    expected = {
        SENSOR_LAN_IP: "192.168.1.1",
        SENSOR_LAN_SUBNET: "255.255.255.0",
        SENSOR_LAN_MAC: "80:AF:CA:30:6C:77",
    }

    api_lan_info(API, html, expected)


def test_r700_parse_wan():
    html = read_fixture("wan.html", model="r700")
    expected = {
        SENSOR_WAN_IP: "83.238.165.41",
        SENSOR_WAN_PUBLIC_IP: "n/a",
        SENSOR_WAN_DNS: "87.204.204.204/62.233.233.233",
        SENSOR_WAN_TYPE: "PPPoE",
        SENSOR_WAN_UPTIME: "23 Day 04:09:38",
    }

    api_wan_info(API, html, expected)


def test_r700_parse_dhcp():
    html = read_fixture("dhcp.html", model="r700")
    expected = {
        SENSOR_DHCP_IP_START: "192.168.1.100",
        SENSOR_DHCP_IP_END: "192.168.1.199",
        SENSOR_DHCP_DNS_PRIMARY: "8.8.8.8",
        SENSOR_DHCP_DNS_SECONDARY: "62.233.233.233",
        SENSOR_DHCP_GATEWAY: "192.168.1.1",
        SENSOR_DHCP_LEASE_TIME: "12 Hours",
    }

    api_dhcp_info(API, html, expected)


def test_r700_parse_devices():
    html = read_fixture("devices.html", model="r700")
    expected = {
        SENSOR_DEVICE_COUNT: 11,
        SENSOR_DEVICE_ONLINE: 6,
        SENSOR_DEVICE_BLOCKED: 2,
    }

    api_devices_info(API, html, expected)


def test_r700_parse_device_list():
    html = read_fixture("device_list.html", model="r700")
    api_device_list(html, 1)
