from __future__ import annotations

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.models.p5.api import P5Api
from tests.cudy_router.basic_api_test import api_system_info, api_dhcp_info, api_lan_info, read_fixture, \
    api_device_list, api_mesh_info, api_gsm_info, api_sms_info, api_basic_info, api_devices_info

API = P5Api(client=None)

def test_p5_parse_info():
    html = read_fixture("info.html", model="p5")
    expected = {
        SENSOR_INFO_WORK_MODE: "Cellular Router",
        SENSOR_INFO_INTERFACE: "5G",
    }
    api_basic_info(API, html, expected)


def test_p5_parse_system():
    html = read_fixture("system.html", model="p5")
    expected = {
        SENSOR_SYSTEM_FIRMWARE_VERSION: "2.4.25-20260112-095317",
        SENSOR_SYSTEM_MODEL: "P5",
        SENSOR_SYSTEM_HARDWARE: "P5 V1.1",
        SENSOR_SYSTEM_UPTIME: "14:33:38",
        SENSOR_SYSTEM_LOCALTIME: "2026-01-26 19:33:53",
    }
    api_system_info(API, html, expected)


def test_p5_parse_mesh():
    html = read_fixture("mesh.html", model="p5")
    expected = {
        SENSOR_MESH_NETWORK: "Mesh_D72C",
        SENSOR_MESH_UNITS: 3
    }

    api_mesh_info(API, html, expected)


def test_p5_parse_lan():
    html = read_fixture("lan.html", model="p5")
    expected = {
        SENSOR_LAN_IP: "192.168.1.1",
        SENSOR_LAN_SUBNET: "255.255.255.0",
        SENSOR_LAN_MAC: "80:AF:AA:2D:D7:2C",
    }

    api_lan_info(API, html, expected)


def test_p5_parse_dhcp():
    html = read_fixture("dhcp.html", model="p5")
    expected = {
        SENSOR_DHCP_IP_START: "192.168.1.10",
        SENSOR_DHCP_IP_END: "192.168.1.250",
        SENSOR_DHCP_DNS_PRIMARY: "8.8.8.8",
        SENSOR_DHCP_DNS_SECONDARY: "1.1.1.1",
        SENSOR_DHCP_GATEWAY: "192.168.1.1",
        SENSOR_DHCP_LEASE_TIME: "120 Mins",
    }

    api_dhcp_info(API, html, expected)


def test_p5_parse_gsm():
    html = read_fixture("gsm.html", model="p5")
    expected = {
        SENSOR_GSM_NETWORK_TYPE: "T-Mobile 5G-NSA",
        SENSOR_GSM_DOWNLOAD: "0.78 GB",
        SENSOR_GSM_UPLOAD: "1.05 GB",
        SENSOR_GSM_PUBLIC_IP: "37.31.32.103",
        SENSOR_GSM_IP_ADDRESS: "100.66.71.18",
        SENSOR_GSM_CONNECTED_TIME: "14:49:45"
    }

    api_gsm_info(API, html, expected)


def test_p5_parse_sms():
    html = read_fixture("sms.html", model="p5")
    expected = {
        SENSOR_SMS_INBOX: 12,
        SENSOR_SMS_OUTBOX: 32,
    }

    api_sms_info(API, html, expected)


def test_p5_parse_devices():
    html = read_fixture("devices.html", model="p5")
    expected = {
        SENSOR_DEVICE_COUNT: 5,
        SENSOR_WIFI_24_DEVICE_COUNT: 1,
        SENSOR_WIFI_5_DEVICE_COUNT: 13,
        SENSOR_WIRED_DEVICE_COUNT: 0,
        SENSOR_MESH_DEVICE_COUNT: 3,
    }

    api_devices_info(API, html, expected)

def test_p5_device_list():
    html = read_fixture("device_list.html", model="p5")
    api_device_list(html, 5)
