from __future__ import annotations

import re
from typing import Any, Dict

from custom_components.hass_cudy_router.const import SENSOR_SYSTEM_MODEL, MODULE_SYSTEM, CUDY_DEVICES, CAPABILITY_URLS, \
    SENSOR_SYSTEM_HARDWARE
from custom_components.hass_cudy_router.parser import parse_module_by_sensors

SPECIAL_CASES = {
    "LT300 V3.0": "LT300V3",
    "WR1300E V2.0": "WR1300EV2",
    "WR1300 V4.0": "WR1300V4.0",
}


async def detect_model(client: Any) -> str:
    path = f"/cgi-bin/luci{CAPABILITY_URLS[MODULE_SYSTEM][0]}"
    try:
        html = await client.get(path)
        if html:
            data = parse_module_by_sensors(MODULE_SYSTEM, html)
            return fit_model(data)
        raise Exception
    except Exception:
        raise

def fit_model(data: Dict) -> str:
    potential_model = normalize_model_name(data[SENSOR_SYSTEM_MODEL])
    hardware = data[SENSOR_SYSTEM_HARDWARE]
    has_dash = "-" in potential_model
    if hardware in SPECIAL_CASES.keys():
        return SPECIAL_CASES[hardware]
    else:
        if potential_model in CUDY_DEVICES:
            return potential_model
        elif has_dash:
            without_dash = potential_model.replace("-", "")
            if without_dash in CUDY_DEVICES:
                return without_dash
            else:
                raise Exception
        else:
            raise Exception


def normalize_model_name(name: str) -> str:
    s = (name or "").strip()
    s = re.sub(r"\s*-\s*Outdoor\s*$", "-Outdoor", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+Outdoor\s*$", "-Outdoor", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^A-Za-z0-9\-.]", "", s)
    return s