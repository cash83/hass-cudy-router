from __future__ import annotations

import logging
import re
from typing import Any, Optional

from custom_components.hass_cudy_router.const import SENSOR_SYSTEM_MODEL
from custom_components.hass_cudy_router.models.base_api import BaseApi

_LOGGER = logging.getLogger(__name__)

KNOWN_MODELS = {
    r"WR6500": "WR6500",
    r"R700": "R700",
    r"P5": "P5",
    r"Generic": "Generic",
}


async def detect_model(client: Any) -> str:
    api = BaseApi(client)
    system_raw = await api.fetch_text("/admin/system/status?detail=1")
    system_data = api.parse_system_info(system_raw)
    return system_data[SENSOR_SYSTEM_MODEL] if system_data[SENSOR_SYSTEM_MODEL] in KNOWN_MODELS.values() else "Generic"