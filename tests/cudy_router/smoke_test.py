#!/usr/bin/env python3
import os
import sys
import json
import asyncio
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT)

from custom_components.hass_cudy_router.router import CudyRouter
from custom_components.hass_cudy_router.const import (
    MODULE_SYSTEM, MODULE_LAN, MODULE_DEVICES
)

# ---- CONFIG VIA ENV VARS (recommended) ----
PROTOCOL = os.getenv("CUDY_PROTOCOL", "https")
HOST = os.getenv("CUDY_HOST", "router.gdzi.es")
USERNAME = os.getenv("CUDY_USER", "admin")
PASSWORD = os.getenv("CUDY_PASS", "3zUo2Fk@")

if not PASSWORD:
    print("❌ Set CUDY_PASS env variable")
    sys.exit(1)


# ---- minimal fake hass ----
class FakeHass:
    async def async_add_executor_job(self, func, *args):
        return func(*args)


async def main():
    print("=== Cudy Router Smoke Test ===")
    print(f"Host: {PROTOCOL}://{HOST}")
    print(f"User: {USERNAME}")
    print("-----------------------------")

    hass = FakeHass()
    router = CudyRouter(
        hass=hass,
        protocol=PROTOCOL,
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
    )

    # ---- AUTH ----
    print("🔐 Authenticating...")
    ok = router.authenticate()
    print(f"Auth result: {ok}")
    print(f"Auth value: {router.auth_cookie}")
    print(f"Auth cookie: {'SET' if router.auth_cookie else 'NOT SET'}")

    if not ok:
        print("❌ Authentication failed, aborting")
        return

    # ---- FULL get_data() ----
    print("\n📦 Running get_data()")
    data = await router.get_data(hass, options={})

    print("\n=== Parsed modules ===")
    for key in [MODULE_SYSTEM, MODULE_LAN, MODULE_DEVICES]:
        value = data.get(key)
        if isinstance(value, dict):
            print(f"Values for {key}: \n")
            for dict_key, dict_value in value.items():
                print(f"{dict_key}: {dict_value} \n")
            print("_______________________________________ \n")
        elif isinstance(value, list):
            print(f"Values for {key}: \n")
            for list_item in value:
                print(f"{list_item} \n")
            print("_______________________________________ \n")
        else:
            print(f"Value for {key}: {value}")

    print("\n🕒 Finished at", datetime.now().isoformat())


if __name__ == "__main__":
    asyncio.run(main())