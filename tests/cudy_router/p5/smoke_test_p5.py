#!/usr/bin/env python3
import os
import sys
import asyncio
from datetime import datetime

from custom_components.hass_cudy_router.const import *

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, ROOT)

from custom_components.hass_cudy_router.client import CudyClient
from custom_components.hass_cudy_router.models.p5.api import (
    P5Api,
    MODULE_SYSTEM,
    MODULE_LAN,
    MODULE_DEVICES,
)

EXPECTED_VALUES = {
    SENSOR_SYSTEM_FIRMWARE_VERSION: "2.3.15-20250805-113843",
    SENSOR_SYSTEM_HARDWARE: "WR6500 V1.0",
    SENSOR_SYSTEM_UPTIME: "09:44:16",
    SENSOR_MESH_NETWORK: "Mesh_5456",
    SENSOR_MESH_UNITS: "2",
    SENSOR_WAN_PUBLIC_IP: "83.238.165.41 *",
    SENSOR_WAN_IP: "192.168.10.150",
    SENSOR_WAN_DNS: "8.8.8.8/62.233.233.233",
    SENSOR_WAN_TYPE: "DHCP client",
    SENSOR_WAN_UPTIME: "09:51:02",
    SENSOR_LAN_IP: "192.168.178.1 ",
    SENSOR_DEVICE_COUNT: "30",
    SENSOR_WIFI_24_DEVICE_COUNT: "4",
    SENSOR_WIFI_5_DEVICE_COUNT: "2",
    SENSOR_WIRED_DEVICE_COUNT: "5",
    SENSOR_MESH_DEVICE_COUNT: "18",
}

# ------------------------------------------------------------------
# CONFIG (via env vars)
# ------------------------------------------------------------------
PROTOCOL = os.getenv("CUDY_PROTOCOL", "http")
HOST = os.getenv("CUDY_HOST", "192.168.1.1")
USERNAME = os.getenv("CUDY_USER", "admin")
PASSWORD = os.getenv("CUDY_PASS")

if not PASSWORD:
    print("❌ Set CUDY_PASS env variable")
    sys.exit(1)

USE_HTTPS = PROTOCOL == "https"


def print_module(name: str, values: dict) -> None:
    print(f"Values for {name}: \n")
    for key, value in values.items():
        print(f"{key}: {value} \n")
    print("_______________________________________ \n")


async def main() -> None:
    print("=== Cudy Router Smoke Test (WR6500 API) ===")
    print(f"Host: {PROTOCOL}://{HOST}")
    print(f"User: {USERNAME}")
    print(f"Pass: {PASSWORD}")
    print("-----------------------------")

    client = CudyClient(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
        use_https=USE_HTTPS,
    )

    try:
        print("🔐 Authenticating...")
        ok = await client.authenticate()
        print(f"Auth result: {ok}")
        print(f"sysauth set: {client.sysauth}")
        print(f"Auth cookie: {'SET' if ok else 'NOT SET'}")

        if not ok:
            print("❌ Authentication failed, aborting")
            return

        return
        print("\n📦 Running P5Api.get_data()")
        api = P5Api(client)
        data = await api.get_data()

        print("\n=== Parsed modules ===")
        for key in (MODULE_SYSTEM, MODULE_MESH, MODULE_WAN, MODULE_LAN, MODULE_DEVICES):
            value = data.get(key)
            if isinstance(value, dict):
                print_module(key, value)
            else:
                print(f"Value for {key}: {value}")
                assert EXPECTED_VALUES.get(key) == value

        print("\n🕒 Finished at", datetime.now().isoformat())

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())